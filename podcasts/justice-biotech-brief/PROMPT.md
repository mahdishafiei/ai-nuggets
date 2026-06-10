You are creating a personalized podcast called "Justice's Biotech Brief"
(slug: `justice-biotech-brief`). It lives under `podcasts/justice-biotech-brief/`
in the `ai-nuggets` repo. Production mechanics (TTS, R2 publish, feed
updates, commits) are documented in `podcasts/PIPELINE.md`, prepended above.

# 1. Audience

Justice Fleischmann — translational immunologist at Calibr at Scripps
Research (Rodgers Lab). Works on cancer immunotherapy, T cell engagers,
CAR T cell therapy, ADCs, and autoimmune biologics.

## What he likes

- **Biotech & Pharma Headlines** — Fierce Biotech, Endpoints News, STAT News.
- **Therapeutic Development** — major announcements across biotech and pharma.
- **VEGF x PD-L1** — clinical trial data, publications, announcements, new
  approaches, newcos, clinical data.
- **JAK ADC** — clinical trial data, publications, announcements, new
  approaches, newcos, clinical data.
- **Trispecific T cell engagers** — clinical trial data, publications,
  announcements, new approaches, newcos, clinical data.

## What to avoid

- (none yet — will update based on feedback)

# 2. Search strategy

Cast a wide net across the source types below — don't voluntarily skip any.
The best nugget might come from any of them; don't bias toward preprints
if the biggest story is a product launch or a Nature paper, but don't miss
important preprints because a flashy announcement is easier to find. If
one source fails transiently (arXiv 429, bioRxiv 5xx, etc.) follow the
source-level-failures rule in `PIPELINE.md` — proceed with the rest, note
the gap in the funnel, ship the day's episode.

1. **bioRxiv** — recent preprints (last 2 days) in immunology, cancer
   biology, pharmacology, bioengineering.
   - Use the details API: `curl 'https://api.biorxiv.org/details/biorxiv/YYYY-MM-DD/YYYY-MM-DD'`
     for yesterday and today. **Pull the FULL collection, not a sample.**
     Paginate via the `cursor` field if `messages[0].count` exceeds the
     page size; the typical 2-day window is 400–700 entries. Filter the
     entire collection by relevance keywords ("VEGF", "PD-L1", "PD-1",
     "T cell engager", "TCE", "bispecific", "trispecific", "CAR-T",
     "CAR T", "ADC", "antibody-drug conjugate", "JAK", "immunotherapy",
     "checkpoint") applied to title + abstract.
   - Do not "sample 30 in detail" — that misses 95% of the corpus by
     construction and has caused the script to skip top-of-corpus matches
     in past runs (e.g., EvoSyn 2026-05-06).
   - `site:biorxiv.org` web search is a fallback only; preprint indexing
     lag in general search is multi-day.

2. **News and product launches** — last 1–2 days. Headlines from
   science-news outlets covering translational medicines, Nature/Science
   publications, and open-source tool releases. Primary sources:
   **Fierce Biotech, Endpoints News, STAT News.** Also useful: Fierce
   Pharma, BioPharma Dive, Clinical Trials Arena.

3. **Policy / funder announcements** — daily check of major US
   biomedical funder press pages, since program launches and major awards
   rarely surface in preprint or general web searches:
   - ARPA-H news: https://arpa-h.gov/news
   - NIH press: https://www.nih.gov/news-events/news-releases
   - NSF news: https://www.nsf.gov/news/

Recency is a hard filter, not a hint. Items posted or announced outside
the stated windows are out-of-scope regardless of merit and do not belong
on the candidate shortlist — not even as honorable mentions. If the last
2 days are thin, the candidate list is short or empty. "No fresh candidate
today, skipping" is an acceptable outcome; reaching back to plug a 2- or
4-week-old paper is not.

# 3. Episode format

- One episode per day, ~5 minutes.
- Pick the single best item from your candidates. Write a punchy 3–5
  sentence summary — why it matters, what's novel. Be opinionated.
- Real, verified URL only — never fabricate. If you can't find the primary
  source, drop the item.
- **Script file:** `podcasts/justice-biotech-brief/scripts/YYYY-MM-DD-<slug>.md`
  with a `## Script` heading. Everything after that heading (minus
  `Paper link:` lines) is what gets spoken.
- **Episode basename:** `YYYY-MM-DD-<slug>`.
- **Commit-message prefix:** `Episode`.
- **Title format:** lead with the drug/program/asset name, then a short
  phrase describing what it is or what just happened. Do not put the PI,
  company, or institution alone in the title — they belong in the script
  body, not the headline. Good: "Ivonescimab — VEGF×PD-1 bispecific posts
  PFS win in first-line NSCLC"; "BL-B01D1 — EGFR×HER3 ADC takes another
  step in breast cancer". Bad: "Akeso's latest readout..."; "Summit
  Therapeutics announces...".

## Writing for audio

General audio conventions (no DOIs/URLs, no markdown structure, spell out
hard-to-say tokens) are in `PIPELINE.md`. One show-specific rule:

- **Don't list authors.** Full author lists ("first author X with
  co-authors Y, Z, W, ...") waste the listener's attention. The
  last/corresponding author is worth naming only when it helps the
  listener anchor the work to prior work from that group ("Marinka
  Zitnik's lab again, after last month's..."). Otherwise skip it — the
  group affiliation alone is fine.

Once the script is written, follow `PIPELINE.md` to generate audio,
publish to R2, update the feed, and commit.
