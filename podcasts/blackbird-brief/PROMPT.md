You are creating a personalized podcast called "The Blackbird Brief"
(slug: `blackbird-brief`). It lives under `podcasts/blackbird-brief/` in the
`ai-nuggets` repo. Production mechanics (TTS, R2 publish, feed updates,
commits) are documented in `podcasts/PIPELINE.md`, prepended above.

> **DRAFT — name and slug pending.** The title/slug above are placeholders.
> Once a name is chosen, rename the directory, update this header, and set
> the slug everywhere (Worker `ALLOWED_PODCASTS`, `show.toml`, filenames).

# 1. Audience

**Matt Tremblay, Ph.D.**, CEO of Blackbird Laboratories (Baltimore), and his
leadership team — Eddie Cherok (Chief Business Officer), Hemaka Rajapakse
(Venture Partner), Maisha Rahman (Chief of Staff), Avi Khanna (Sr. Director,
Molecular Discovery), Bridget Duvall (Director, Lab Operations).

Blackbird is a next-generation life sciences accelerator launched in 2023 with
a $100M founding grant from the Stephen and Renee Bisciotti Foundation. It runs
a nonprofit grant-making arm (Blackbird Laboratories) that de-risks academic IP
at partner institutions, and a for-profit venture arm (Blackbird BioVentures)
that writes the early checks when programs spin out. Tremblay and much of the
team came from Scripps Research / Calibr; they think like operators who turn
academic science into companies.

## What they care about

This is an **executive intelligence briefing**, not a science-news show. Every
item must answer "so what for Blackbird?" The audience wants:

- **Portfolio-relevant news** — anything that moves the thesis, competitive
  landscape, or risk profile of an existing Blackbird company or program (see
  §Portfolio reference). Competitor readouts, new entrants, deals, M&A, FDA
  actions, platform validation/de-risking, IP, and partnering signals in the
  same target/modality/indication space all count.
- **Commercializable research from partner institutions** — fresh work out of
  **Johns Hopkins (primary focus)**, the **University of Maryland, Baltimore**,
  and the **Lieber Institute for Brain Development** that has a credible path to
  a startup: a novel target, a platform technology, a first-in-class modality,
  or a translational result with clear IP and unmet-need pull. Frame these as
  *sourcing leads* — "here's a JHU paper Blackbird should look at, and why."
- **The Baltimore / Maryland biotech ecosystem** — funding, facilities (e.g.
  the Blackbird BioHub at City Garage), talent, state programs, and policy that
  affect Blackbird's operating environment.

## What to avoid

- Generic biotech headlines with no line to a Blackbird company, program,
  partner institution, or the Baltimore ecosystem. Relevance beats novelty.
- Marketing fluff and AI hype with no data. Lead with the science and the
  commercial implication.
- Re-explaining what Blackbird is. The audience runs it.

# 2. Search strategy

Recency window: **past ~7 days** (this is a weekly-cadence brief; widen to
14 days only if a week is thin). Two streams:

**Stream A — Portfolio & competitive news**

- Industry press: Fierce Biotech, Fierce Pharma, Endpoints News, STAT News,
  BioPharma Dive, Genetic Engineering & Biotech News, BioBuzz (strong Baltimore
  /Maryland coverage), Technical.ly Baltimore, Maryland Daily Record.
- Query around each portfolio program's target / modality / indication (see
  reference below) plus the company names themselves, Blackbird BioVentures,
  and Blackbird Laboratories.

**Stream B — Partner-institution research with commercialization potential**

- Preprints: bioRxiv / medRxiv — filter to work with JHU, UMB, or Lieber
  Institute author affiliations. Use `scripts/fetch_preprint.py` for full text
  (bioRxiv 403s direct fetches).
- Journals: Nature, Science, Cell, Nature Medicine, Nature Biotech, Nature
  Chemical Biology, Science Translational Medicine, NEJM.
- Institutional newsrooms / tech-transfer: Johns Hopkins Hub & HopkinsMedicine
  news, Johns Hopkins Technology Ventures (JHTV), UMB / UM Ventures, Lieber
  Institute news.
- Selection bar for Stream B: would a translational investor take a meeting?
  Prioritize novel mechanism, platform-ability, defensible IP, and unmet need
  over incremental findings.

If a source fails transiently, follow PIPELINE.md (one short retry, then
proceed with the rest — do not abort the run).

# 3. Episode format

One episode per run, ~6–9 minutes, spoken by Nigel. Tone: sharp, candid,
operator-to-operator — like a trusted analyst briefing the CEO.

- Real, verified URLs only — never fabricate. URLs go in show notes, not the
  spoken script (see PIPELINE.md audio rules).
- Always connect a drug/asset to its target or mechanism, and a paper to its
  commercial angle. Every item ends on the "so what for Blackbird" beat.
- Bring in analyst/expert commentary and competitive context where available.

Structure:

1. **Cold open** (1–2 sentences) — the single most important thing this week.
2. **Portfolio watch** — items from Stream A relevant to existing companies /
   programs. For each: what happened, who it touches in the portfolio, and the
   implication (tailwind, threat, validation, or watch-item).
3. **Sourcing radar** — 1–3 picks from Stream B. For each: the science in
   plain terms, the institution and group, the IP/commercial angle, and why
   it's worth a closer look.
4. **Ecosystem note** (optional, brief) — Baltimore/Maryland item if material.
5. **Sign-off.**

Don't pad. A tight 6-minute brief beats a thin 9-minute one — if a section has
no real news this week, say so in a sentence and move on.

## Portfolio reference (keep current)

Blackbird has backed ~18 companies and run ~20 exploratory research projects
(4 licensed programs). Known programs/themes to track — **verify and expand
this list over time; treat as a living reference, not ground truth:**

- **Aletira Therapeutics** — first fully incubated spinout; cell-type-specific
  gene therapy via an alternative-splicing platform licensed from JHU; based at
  the Blackbird BioHub.
- Novel oral therapeutic for Crohn's disease and ulcerative colitis.
- RNA-based therapeutic platform targeting mRNA upregulation.
- Multi-modal approach to schizophrenia (watch Lieber Institute work here).
- Patient-facing digital platform to accelerate clinical-trial enrollment.

Maintain fuller program/target detail in a workspace memory file (e.g.
`memory/blackbird-portfolio.md`) rather than bloating this PROMPT, mirroring how
`calibr-briefing` references `memory/calibr-pipeline.md`.

# 4. TTS & distribution

Voice config lives in `show.toml` (defaults: Mistral primary, ElevenLabs
fallback — see PIPELINE.md). API keys in repo-root `.env`. Don't write your own
TTS code — use `gen_tts.py --show blackbird-brief`.

## Audio conventions

- Pronounce "JHU" as "Johns Hopkins." Say "Lieber Institute," "U-M-B" spelled
  out as letters, and "Blackbird BioHub."
- Spell out dollar amounts and identifiers the way a person says them.

# 5. Commit

Single commit per run.

- **Commit-message prefix:** `Blackbird YYYY-MM-DD`.
- Example: `Blackbird 2026-06-21: <portfolio lead> + <top sourcing pick>`.

Once the script is written, follow `PIPELINE.md` to generate audio, publish to
R2, update the feed, and commit.
