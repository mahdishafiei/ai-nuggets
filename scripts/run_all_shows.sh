#!/bin/bash
# Run the daily Claude pipeline for every show under podcasts/<slug>/.
# A "show" is any directory containing a PROMPT.md.
#
# Sequential on purpose: avoids TTS API contention and races on `git push`.
# Add a new show by creating podcasts/<slug>/PROMPT.md — no crontab edit needed.

set -u

REPO=/home/asu/Science/ai-nuggets
CLAUDE=/home/asu/.local/bin/claude

cd "$REPO" || exit 1

PIPELINE="$REPO/podcasts/PIPELINE.md"
if [ ! -f "$PIPELINE" ]; then
  echo "ERROR: $PIPELINE not found" >&2
  exit 1
fi

# Pre-fetch arXiv listing once for the whole run so multiple shows don't
# burst the same IP and trip a tarpit. The category union covers every
# show's needs (cs.AI, cs.CL, cs.MA, q-bio supercategory). Each show's
# PROMPT.md tells Claude to read from this cache instead of curling arXiv.
# Stable path so prompts don't need to embed today's date; we refresh it
# when its mtime is older than today's local midnight.
ARXIV_CACHE=/tmp/ai-nuggets-arxiv-cache.xml
if [ -z "$(find "$ARXIV_CACHE" -newermt "$(date +%F)" 2>/dev/null)" ]; then
  rm -f "$ARXIV_CACHE"
  curl -s --max-time 90 \
    -A 'ai-nuggets/1.0 (https://github.com/andrewsu/ai-nuggets)' \
    'https://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.MA+OR+cat:q-bio&sortBy=submittedDate&sortOrder=descending&max_results=500' \
    -o "$ARXIV_CACHE.tmp" \
    && mv "$ARXIV_CACHE.tmp" "$ARXIV_CACHE" \
    || rm -f "$ARXIV_CACHE.tmp"
fi

for prompt in podcasts/*/PROMPT.md; do
  [ -f "$prompt" ] || continue
  slug=$(basename "$(dirname "$prompt")")
  log="$REPO/podcasts/$slug/logs/cron.log"
  mkdir -p "$(dirname "$log")"

  # The content-AUP classifier occasionally flags the biomedical-agentic-ai
  # prompt on the first attempt; a retry minutes later typically clears it.
  for attempt in 1 2; do
    tag=""
    [ "$attempt" -gt 1 ] && tag=" (retry $((attempt-1)))"
    out=$(mktemp)
    {
      echo "=== $(date -Iseconds) start $slug$tag ==="
      cat "$PIPELINE" "$prompt" | "$CLAUDE" -p --permission-mode auto
      echo "=== $(date -Iseconds) done  $slug (exit $?)$tag ==="
    } 2>&1 | tee -a "$log" > "$out"
    if [ "$attempt" -eq 1 ] && \
       grep -q "Claude Code is unable to respond to this request, which appears to violate our Usage Policy" "$out"; then
      echo "=== $(date -Iseconds) AUP-refusal detected for $slug; retrying in 180s ===" | tee -a "$log"
      rm -f "$out"
      sleep 180
      continue
    fi
    rm -f "$out"
    break
  done
done

# Claude's per-episode commit happens mid-run, before the closing "done"
# line is written above. Pick up any straggling log changes as a follow-up
# commit so they don't accumulate untracked between cron runs.
if ! git diff --quiet -- 'podcasts/*/logs/cron.log'; then
  git add 'podcasts/*/logs/cron.log' \
    && git commit -m 'Update cron logs' \
    && git push
fi
