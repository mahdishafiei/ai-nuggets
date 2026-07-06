#!/bin/bash
# Upload an episode mp3 to the public server on Garibaldi so it's reachable
# at http://garibaldi.scripps.edu:8420/episodes/<basename>.mp3
#
# Usage:
#   scripts/publish_episode.sh <slug> <episode-basename>
#
# Example:
#   scripts/publish_episode.sh affinity-matured 2026-07-05-foo-bar
#
# Reads the mp3 from podcasts/<slug>/episodes/<basename>.mp3 and rsyncs it to
# ~/ai-nuggets-public/episodes/<basename>.mp3 on Garibaldi.
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
GARIBALDI_HOST=garibaldi.scripps.edu
GARIBALDI_PUBLIC_DIR=ai-nuggets-public   # relative to remote $HOME

if [ ! -f "$mp3" ]; then
  echo "ERROR: $mp3 not found" >&2
  exit 1
fi

rsync -a "$mp3" "$GARIBALDI_HOST:$GARIBALDI_PUBLIC_DIR/episodes/$basename.mp3"
