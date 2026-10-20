#!/bin/zsh
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t110
export LC_ALL=C
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
export A2A_PROJECT=a2a A2A_TASK=T-110 A2A_ATTEMPT=a1 A2A_ROLE=worker
export A2A_SESSION=08655309-afa5-40e1-90b5-70da288741da
export A2A_LAUNCH=launch-d008aad4e92d4bbc86a75109c7625d0f
export A2A_LAUNCHES=/Users/luckye/Documents/Code/a2a/records/launches.jsonl
export CODEX_THREAD_ID=01a15956-19a9-7332-8442-7860f235840b
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a/scripts/git-hooks
[[ $(git branch --show-current) == exec/t110 ]]
[[ $(git rev-parse HEAD) == 92bc8820800bf7990cacfb3bcb4cddcfe4b48217 ]]
git diff --cached --quiet
git diff --check
git add --sparse -- \
  workbench/tests/t108_cleanup.py workbench/tests/test_t110_cleanup.py \
  workbench/tests/run_t110_notifications.py workbench/README.md \
  evidence/2026-10-20-batch18/T-110
# Existing hook adds provenance trailers.
git commit -m "fix(tests): await identity-matched exiting CLI processes"
git show -1 --format=full --stat
