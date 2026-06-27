# AI Nuggets

Personalized AI-curated podcast feeds. Each show under `podcasts/<slug>/`
is a separate feed for a separate audience.

## Shows

| Slug | Audience | Subscribe |
|---|---|---|
| [`affinity-matured`](podcasts/affinity-matured/) | Mahdi Shafiei (Scripps) — antibody & protein language models and AI-driven antibody engineering, incl. influenza | [feed.xml](https://raw.githubusercontent.com/mahdishafiei/ai-nuggets/main/podcasts/affinity-matured/feed.xml) |

After cloning, run `git config core.hooksPath .githooks` once to activate the
pre-commit feed-XML validator.

- **Adding a new show to this deployment?** See [ADDING_A_SHOW.md](ADDING_A_SHOW.md).
- **Running your own ai-nuggets** (your own Cloudflare account, cron, API
  keys)? See [SETUP.md](SETUP.md).

## Repo layout

```
ai-nuggets/
├── gen_tts.py                          # shared TTS pipeline (Mistral / ElevenLabs)
├── lib/show.py                         # per-show config loader (reads show.toml)
├── scripts/
│   ├── new_show.py                     # scaffold a new podcast
│   ├── run_all_shows.sh                # daily cron entry point
│   ├── publish_episode.sh              # upload an mp3 to R2
│   └── update_feed_for_worker.py       # rewrite feed.xml enclosures for the Worker
├── worker/                             # Cloudflare Worker (analytics + redirect)
└── podcasts/<slug>/
    ├── show.toml                       # voice config, paths, RSS metadata
    ├── PROMPT.md                       # audience profile + daily recipe for the AI
    ├── feed.xml                        # this show's RSS feed
    ├── episodes/                       # mp3s
    ├── scripts/                        # daily transcripts (.md or .txt)
    └── logs/                           # run logs
```

## Adding a new show

```bash
python3 scripts/new_show.py my-new-show \
  --title "My New Show" \
  --description "What this show is about" \
  --owner "Owner Name <email>"
```

The daily runner (`scripts/run_all_shows.sh`) auto-discovers any
`podcasts/*/PROMPT.md` — no cron edit needed. After scaffolding you
still need to customize the PROMPT/show.toml, allow the slug on the
Worker, and smoke-test before letting cron take over. See
[ADDING_A_SHOW.md](ADDING_A_SHOW.md) for the full checklist.
