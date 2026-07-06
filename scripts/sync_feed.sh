#!/bin/bash
# Sync a show's feed.xml to the public server on Garibaldi so subscribers
# fetching http://garibaldi.scripps.edu:8420/feed.xml see the latest episodes.
#
# Usage:
#   scripts/sync_feed.sh <slug>
#
# Run this after feed.xml is updated with the day's new <item>, before
# committing.

set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 <slug>" >&2
  exit 2
fi

slug="$1"

REPO="$(cd "$(dirname "$0")/.." && pwd)"
feed="$REPO/podcasts/$slug/feed.xml"
GARIBALDI_HOST=garibaldi.scripps.edu
GARIBALDI_PUBLIC_DIR=ai-nuggets-public   # relative to remote $HOME

if [ ! -f "$feed" ]; then
  echo "ERROR: $feed not found" >&2
  exit 1
fi

rsync -a "$feed" "$GARIBALDI_HOST:$GARIBALDI_PUBLIC_DIR/feed.xml"
