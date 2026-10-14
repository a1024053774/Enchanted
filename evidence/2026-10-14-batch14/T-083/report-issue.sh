#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a
/Users/luckye/Documents/Code/a2a/scripts/inbox send --from worker:s14-t083 --to triage --kind issue --title '范围外：intent 和任务卡模板仍要求 Fast' --body-file /Users/luckye/Documents/Code/a2a-wt-t083/evidence/2026-10-14-batch14/T-083/out-of-scope-issue.md --ref 'file:intent.md#L98' --ref 'file:.project-map/templates/task-card.md#L18'
