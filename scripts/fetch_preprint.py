#!/usr/bin/env python3
"""Fetch bioRxiv / medRxiv preprint text via channels that bypass Cloudflare.

The recurring failure mode in the daily run is that `www.biorxiv.org` is
behind Cloudflare and 403s every non-browser request — direct curl, the
`.full.pdf` endpoint, the `source.xml` JATS endpoint, all of them. Hitting
those URLs from a script will not work and re-trying with different UAs
does not help.

What does work:

  1. r.jina.ai reader proxy on the `.full` HTML page. Jina renders the
     page server-side with a real browser, so Cloudflare passes it, and
     returns clean markdown. Caveat: bioRxiv's HTML render of a brand-new
     preprint often contains only the abstract until ~12–36h after the
     preprint is posted — for fresher papers expect abstract-only and
     plan to defer or run on the abstract.
  2. Europe PMC's full-text XML. Coverage of bioRxiv preprints lags by
     several months — useful for older work, not the daily case.
  3. bioRxiv details API. Always reachable (api.biorxiv.org is not behind
     Cloudflare) and always returns title + authors + abstract + funder
     info. Use as the guaranteed "minimum useful info" fallback.

Usage:
    scripts/fetch_preprint.py <url-or-doi>

Accepts a bioRxiv/medRxiv article URL (with or without `v<n>` / `.full`)
or a bare DOI. Prints the extracted text to stdout, status to stderr.

Exit codes:
    0  text extracted (full body or at least abstract+metadata)
    1  all channels failed (e.g. DOI doesn't resolve at all)
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional
from xml.etree import ElementTree as ET

TIMEOUT = 90  # jina can take 30-60s for a render

URL_RE = re.compile(
    r"https?://(?:www\.)?(?P<server>biorxiv|medrxiv)\.org/content/"
    r"(?P<prefix>10\.[0-9]+)/(?P<id>\d{4}\.\d{2}\.\d{2}\.\d+)(?:v(?P<version>\d+))?"
)
DOI_RE = re.compile(
    r"^(?:https?://(?:dx\.)?doi\.org/)?"
    r"(?P<prefix>10\.[0-9]+)/(?P<id>\d{4}\.\d{2}\.\d{2}\.\d+)$"
)


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def parse_input(arg: str) -> tuple[str, str, str, Optional[str]]:
    """Return (server, prefix, paper_id, version_or_None)."""
    m = URL_RE.search(arg)
    if m:
        return (
            m.group("server"),
            m.group("prefix"),
            m.group("id"),
            m.group("version"),
        )
    m = DOI_RE.match(arg.strip())
    if m:
        # Bare DOI → assume biorxiv. medRxiv DOIs share the 10.1101 prefix,
        # so we can't distinguish from the DOI alone; biorxiv is far more
        # common in this pipeline, and the details API will tell us if the
        # DOI isn't there.
        return ("biorxiv", m.group("prefix"), m.group("id"), None)
    raise ValueError(
        f"could not parse {arg!r} as a bioRxiv/medRxiv URL or DOI"
    )


def http_get(url: str, *, accept: str = "*/*") -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            # api.biorxiv.org and EPMC don't care about UA, but jina passes
            # this through to the upstream fetch, so a real browser UA
            # gives us the best chance there too.
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": accept,
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def clean_jina_markdown(md: str) -> str:
    """Strip bioRxiv's nav chrome from a jina-rendered page.

    Jina returns the entire page-as-markdown, which on bioRxiv includes a
    50KB sidebar of "Channels" links and a footer of citation-tool links.
    Drop everything before the first major content heading and everything
    after the references/footer markers, then strip image markdown.
    """
    lines = md.splitlines()

    # Find where the paper content starts. The bioRxiv template uses
    # "## Abstract" as the first H2 of the real article body — older
    # templates render the heading in uppercase, hence the IGNORECASE.
    start = 0
    abstract_re = re.compile(r"^##\s+Abstract\b", re.IGNORECASE)
    for i, line in enumerate(lines):
        if abstract_re.match(line):
            start = i
            break

    # Find where the paper content ends — references list, footer, or
    # the citation-tool block bioRxiv puts at the bottom of every page.
    end_markers = re.compile(
        r"^##\s+(?:References|Citation\s+Manager\s+Formats|"
        r"Footnotes|Acknowledgements?)\b",
        re.IGNORECASE,
    )
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if end_markers.match(lines[i]):
            end = i
            break

    kept = lines[start:end]
    # Drop image-only lines and bioRxiv's "View ORCID Profile" boilerplate.
    cleaned = [
        ln for ln in kept
        if not re.match(r"^\s*!\[", ln)
        and "View ORCID Profile" not in ln
    ]
    return "\n".join(cleaned).strip()


def try_jina_full_html(
    server: str, prefix: str, paper_id: str, version: Optional[str]
) -> tuple[Optional[str], str]:
    """Fetch the `.full` HTML page through r.jina.ai. Returns (text, msg)."""
    v = version or "1"
    page_url = (
        f"https://www.{server}.org/content/{prefix}/{paper_id}v{v}.full"
    )
    jina_url = "https://r.jina.ai/" + page_url
    try:
        md = http_get(jina_url, accept="text/markdown").decode(
            "utf-8", errors="replace"
        )
    except urllib.error.HTTPError as e:
        return None, f"jina HTTP {e.code} on {page_url}"
    except (urllib.error.URLError, TimeoutError) as e:
        return None, f"jina fetch failed: {e}"

    if "Attention Required! | Cloudflare" in md[:2000]:
        return None, "jina got a Cloudflare block from bioRxiv"

    text = clean_jina_markdown(md)
    if len(text) < 1500:
        return None, (
            f"jina returned only {len(text)} chars of body "
            "(likely an abstract-only render; preprint may be too new)"
        )
    return text, f"ok via jina .full HTML ({len(text)} chars)"


def jats_text(xml_bytes: bytes) -> str:
    """Walk <body> of a JATS document and collect <title>/<p> text only."""
    root = ET.fromstring(xml_bytes)
    body = root.find(".//{*}body")
    if body is None:
        body = root.find(".//{*}abstract")
    if body is None:
        return ""

    chunks: list[str] = []
    for elem in body.iter():
        tag = elem.tag.rsplit("}", 1)[-1]
        if tag in ("title", "p"):
            text = "".join(elem.itertext()).strip()
            if text:
                chunks.append(text)
    return "\n\n".join(chunks)


def try_europepmc(prefix: str, paper_id: str) -> tuple[Optional[str], str]:
    """Try Europe PMC full-text XML. Returns (text, status_msg).

    Coverage of bioRxiv preprints is sparse and lagged — EPMC's preprint
    full-text corpus runs months behind. Useful for older work.
    """
    doi = f"{prefix}/{paper_id}"
    search_url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        f"?query=DOI:{urllib.parse.quote(doi)}&resultType=lite&format=json"
    )
    try:
        data = json.loads(http_get(search_url, accept="application/json"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        return None, f"EPMC search failed: {e}"

    results = (data.get("resultList") or {}).get("result") or []
    ppr = next(
        (r for r in results if r.get("source") == "PPR" and r.get("id")),
        None,
    )
    if ppr is None:
        return None, "EPMC has no PPR record for this DOI"
    if ppr.get("inEPMC") != "Y":
        return None, f"EPMC has metadata for {ppr['id']} but no full text"

    full_url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/"
        f"PPR/{ppr['id']}/fullTextXML"
    )
    try:
        xml_bytes = http_get(full_url, accept="application/xml")
    except urllib.error.HTTPError as e:
        return None, f"EPMC fullTextXML HTTP {e.code} for {ppr['id']}"
    except (urllib.error.URLError, TimeoutError) as e:
        return None, f"EPMC fullTextXML fetch failed: {e}"

    text = jats_text(xml_bytes)
    if len(text) < 1500:
        return None, f"EPMC body too short ({len(text)} chars)"
    return text, f"ok via EPMC ({ppr['id']}, {len(text)} chars)"


def try_biorxiv_api_abstract(
    server: str, prefix: str, paper_id: str
) -> tuple[Optional[str], str]:
    """Last-resort: title + authors + abstract from api.biorxiv.org.

    api.biorxiv.org is not behind Cloudflare, so this works even when
    every other channel 403s. Body is missing but the abstract is real,
    and the caller can decide whether to drop the item or proceed.
    """
    api_url = f"https://api.biorxiv.org/details/{server}/{prefix}/{paper_id}"
    try:
        data = json.loads(http_get(api_url, accept="application/json"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        return None, f"bioRxiv API failed: {e}"

    collection = data.get("collection") or []
    if not collection:
        return None, "bioRxiv API has no record for this DOI"

    rec = max(collection, key=lambda r: int(r.get("version") or 0))
    parts = [
        f"TITLE: {rec.get('title', '').strip()}",
        f"AUTHORS: {rec.get('authors', '').strip()}",
        f"DATE: {rec.get('date', '').strip()}  VERSION: {rec.get('version', '')}",
        f"CATEGORY: {rec.get('category', '').strip()}",
        "",
        "ABSTRACT (full body unavailable — body not yet rendered or Cloudflare-blocked):",
        "",
        rec.get("abstract", "").strip(),
    ]
    text = "\n".join(p for p in parts if p is not None)
    return text, f"ok via bioRxiv API abstract only ({len(text)} chars)"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        log("usage: fetch_preprint.py <url-or-doi>")
        return 1

    try:
        server, prefix, paper_id, version = parse_input(argv[1])
    except ValueError as e:
        log(f"error: {e}")
        return 1

    log(
        f"resolving {server}:{prefix}/{paper_id}"
        + (f" v{version}" if version else "")
    )

    channels = (
        ("jina-full", lambda: try_jina_full_html(server, prefix, paper_id, version)),
        ("europepmc", lambda: try_europepmc(prefix, paper_id)),
        ("biorxiv-api", lambda: try_biorxiv_api_abstract(server, prefix, paper_id)),
    )

    failures: list[str] = []
    for name, fn in channels:
        text, msg = fn()
        if text is not None:
            log(f"[{name}] {msg}")
            sys.stdout.write(text)
            if not text.endswith("\n"):
                sys.stdout.write("\n")
            # Return 0 with a note when we only got the abstract — caller
            # should decide whether the item still meets the bar.
            if name == "biorxiv-api":
                log(
                    "note: only abstract+metadata were retrieved. "
                    "Decide whether to keep the item (per PIPELINE.md, "
                    "prefer dropping unless it's a clearly dominant pick)."
                )
            return 0
        failures.append(f"[{name}] {msg}")

    log("all channels failed:")
    for f in failures:
        log(f"  {f}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
