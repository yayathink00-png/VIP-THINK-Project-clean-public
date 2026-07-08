#!/bin/zsh
set -euo pipefail

cd /Users/yangyi/.vipthink-auto-publish

/usr/bin/python3 tools/run_scheduled_instagram_queue.py \
  --queue generated/schedules/global_2026-07-07_2026-07-10/queue.scheduled.json \
  --preview-md generated/schedules/global_2026-07-07_2026-07-10/preview.md \
  --yes
