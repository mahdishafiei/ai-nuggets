#!/bin/bash
# Upload an episode mp3 to R2 so the Worker can serve it directly.
#
# Usage:
#   scripts/publish_episode.sh <slug> <episode-basename>
#
# Example:
#   scripts/publish_episode.sh biomedical-agentic-ai 2026-05-03-foo-bar
#
# Reads the mp3 from podcasts/<slug>/episodes/<basename>.mp3 and writes it to
# R2 at podcasts/<slug>/episodes/<basename>.mp3 in the bucket configured in
# worker/wrangler.toml ([[r2_buckets]] bucket_name).
#
# Idempotent: re-uploading the same key overwrites.

set -eu

if [ "$#" -ne 2 ]; then
  echo "usage: $0 <slug> <episode-basename>" >&2
  exit 2
fi

slug="$1"
basename="$2"

REPO="$(cd "$(dirname "$0")/.." && pwd)"
mp3="$REPO/podcasts/$slug/episodes/$basename.mp3"
bucket="ai-nuggets-episodes"
key="podcasts/$slug/episodes/$basename.mp3"

if [ ! -f "$mp3" ]; then
  echo "ERROR: $mp3 not found" >&2
  exit 1
fi

# Load CLOUDFLARE_API_TOKEN (and any other secrets) from repo-root .env so
# wrangler works under cron, where ~/.bashrc isn't sourced.
if [ -f "$REPO/.env" ]; then
  set -a
  . "$REPO/.env"
  set +a
fi

cd "$REPO/worker"
npx wrangler r2 object put "$bucket/$key" \
  --file="$mp3" \
  --content-type="audio/mpeg"
