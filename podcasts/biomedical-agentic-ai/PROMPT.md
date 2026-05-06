You are creating a personalized podcast called "Biomedical Agentic AI" (slug:
`biomedical-agentic-ai`). It lives under `podcasts/biomedical-agentic-ai/` in
the `ai-nuggets` repo.

# 1. Audience

Andrew Su — computational biologist at Scripps Research (Su Lab). Works on
biomedical knowledge graphs, Wikidata, open data/open science. Bioinformatics,
data integration, APIs.

## What he likes

- Agentic AI applied to biomedical research
- AI for knowledge graphs, ontologies, data integration
- Novel tools/frameworks for scientific automation
- Open science + AI intersections
- Anything relevant to a lab that builds and maintains biomedical databases

## What to avoid

- (none yet — will update based on feedback)

## Past feedback

- 2026-03-17: Andrew requested systematic bioRxiv/arXiv searching alongside
  general web search. Don't ignore big non-academic news though.

# 2. TTS & distribution

Voice config lives in `show.toml`:

- **Primary:** Mistral `voxtral-mini-tts-2603` / `en_paul_neutral` (Paul Neutral)
- **Fallback:** ElevenLabs Bella (`hpp4J3VqNfWAUOO0d1Us`) / `eleven_flash_v2_5`

API keys in `.env` at repo root (`MISTRAL_API_KEY`, `ELEVENLABS_API_KEY`).

Don't write your own TTS code. `gen_tts.py` is the canonical pipeline:
chunking, ffmpeg stitching, duration sanity check, primary→fallback
orchestration, all already handled.

Public RSS URL: subscribers fetch
`https://raw.githubusercontent.com/andrewsu/ai-nuggets/main/podcasts/biomedical-agentic-ai/feed.xml`.
Episode mp3 enclosures are served via the `podcast` Cloudflare Worker so
downloads are logged centrally. See `worker/README.md` for setup.

# 3. Daily execution

## Step 1: gather candidates

Cast a wide net across THREE source types — do not skip any. The best nugget
might come from any of them; don't bias toward preprints if the biggest
story is a product launch or Nature paper, but don't miss important
preprints because a flashy announcement is easier to find.

1. **bioRxiv** — recent preprints (last 2 days) in bioinformatics, genomics,
   systems biology, pharmacology. Try queries like "agent", "LLM",
   "foundation model", "autonomous", "multi-agent". Use the bioRxiv API
   (`curl 'https://api.biorxiv.org/details/biorxiv/YYYY-MM-DD/YYYY-MM-DD'`,
   yesterday and today) or web search with `site:biorxiv.org`.
2. **arXiv** — recent papers in cs.AI, cs.CL, q-bio, cs.MA with
   biomedical/scientific relevance. Use `site:arxiv.org` or the arXiv API.
3. **General web** — last 1–2 days. Big AI + science news that may NOT be
   in preprints: major company announcements (DeepMind, NVIDIA, OpenAI),
   Nature/Science publications, policy developments, funding news,
   open-source tool releases.

## Step 2: pick + summarize

Pick ONE best item and create a ~5-minute episode. Write a punchy 3–5
sentence summary — why it matters, what's novel. Be opinionated. Include a
real, verified URL that you actually found during search — do NOT fabricate
or guess URLs. If you can't find the primary source, drop the item.

## Step 3: produce the episode

1. Write the script to:
   ```
   podcasts/biomedical-agentic-ai/scripts/YYYY-MM-DD-slug.md
   ```
   The file must contain a `## Script` heading; everything after that
   heading (minus `Paper link:` lines) is what gets spoken.

2. Generate the audio:
   ```
   python3 gen_tts.py --show biomedical-agentic-ai \
     podcasts/biomedical-agentic-ai/scripts/YYYY-MM-DD-slug.md \
     podcasts/biomedical-agentic-ai/episodes/YYYY-MM-DD-slug.mp3
   ```
   If the script exits non-zero, investigate and fix the root cause — do
   NOT commit partial output.

3. Publish the audio to R2 so the Worker can serve it directly:
   ```
   scripts/publish_episode.sh biomedical-agentic-ai YYYY-MM-DD-slug
   ```
   (omit the `.mp3` suffix). The script wraps `wrangler r2 object put` and
   uploads to the `ai-nuggets-episodes` bucket configured in
   `worker/wrangler.toml`. If it fails, fix the error before committing.

4. Update `podcasts/biomedical-agentic-ai/feed.xml` by inserting a new
   `<item>` immediately after the opening channel metadata and before the
   existing items. Use the actual byte size of the generated mp3 for
   `enclosure length` and the rounded duration from `ffprobe` for
   `itunes:duration`. Keep enclosure URLs pointing at the Worker
   (`https://podcast.<sub>.workers.dev/p/biomedical-agentic-ai/u/<user>/<slug>.mp3`).
   Keep the RSS feed valid XML — escape `&` → `&amp;`, `<` → `&lt;`, `>` →
   `&gt;` in every title, description, and summary. The `.githooks/pre-commit`
   hook will reject the commit if the feed doesn't parse, but catch it
   yourself first. Write guids as
   `<guid isPermaLink="false">YYYY-MM-DD-slug</guid>` — bare slugs without
   `isPermaLink="false"` violate RSS 2.0 and break strict podcast clients.

5. Commit and push:
   ```
   git add -A && git commit -m 'Episode: <title>' && git push
   ```

Note: while we're in the R2 cutover, mp3s are still committed to git as a
safety net (the Worker falls back to GitHub raw if R2 lacks the object).
Once R2 is verified end-to-end, mp3s will be excluded from git and only
uploaded to R2 — this prompt will be updated when that switch happens.
