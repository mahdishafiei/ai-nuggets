#!/bin/bash
# Cron wrapper for scripts/daily_audit.py. Sources .env so AWS_*, SES_*,
# and MISTRAL_ADMIN_API_KEY are visible to the python process — cron's
# default environment otherwise omits them.
#
# Suggested crontab line (5 AM PT, late enough that the 02:00 PT show
# launches plus worst-case retry ladders are complete):
#   0 5 * * * /home/asu/Science/ai-nuggets/scripts/run_daily_audit.sh >> /home/asu/Science/ai-nuggets/logs/audit.log 2>&1

set -u
REPO=/home/asu/Science/ai-nuggets
PYTHON=/home/asu/miniforge3/bin/python3

if [ -f "$REPO/.env" ]; then
  set -a
  . "$REPO/.env"
  set +a
fi

exec "$PYTHON" "$REPO/scripts/daily_audit.py" "$@"
