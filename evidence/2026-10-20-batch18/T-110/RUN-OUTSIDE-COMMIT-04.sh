#!/bin/zsh
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t110
export LC_ALL=C
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
# Controller commits for this recorded worker, using the existing provenance hook.
export A2A_PROJECT=a2a A2A_TASK=T-110 A2A_ATTEMPT=a1 A2A_ROLE=worker
export A2A_SESSION=08655309-afa5-40e1-90b5-70da288741da
export A2A_LAUNCH=launch-d008aad4e92d4bbc86a75109c7625d0f
export A2A_LAUNCHES=/Users/luckye/Documents/Code/a2a/records/launches.jsonl
export CODEX_THREAD_ID=01a15956-19a9-7332-8442-7860f235840b
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a/scripts/git-hooks
[[ $(git branch --show-current) == exec/t110 ]]
[[ $(git rev-parse HEAD) == e1c7b5c275eaca7e342da44cb2582cf81f56ca17 ]]
git diff --cached --quiet
git diff --check
git add --sparse -- \
  workbench/app/renderer.tsx workbench/README.md \
  workbench/tests/run_t110_notifications.py workbench/tests/t108_questions_driver.mjs \
  workbench/tests/t110_notifications_scenario.py workbench/tests/test_t110_reconnect_view.mjs \
  evidence/2026-10-20-batch18/T-110
# Existing hook writes the actual A2A trailers; no hand-written trailers.
git commit -m "fix(workbench): retain bound view when sidebar reload is offline"
git show -1 --format=full --stat
