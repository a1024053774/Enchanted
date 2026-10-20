#!/bin/zsh
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t109
export LC_ALL=C
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
# The controller executes this commit for the recorded T-109/a1 worker.
export A2A_PROJECT=a2a
export A2A_TASK=T-109
export A2A_ATTEMPT=a1
export A2A_SESSION=05933b4f-66d7-4f57-a916-a02584790934
export A2A_ROLE=worker
export A2A_LAUNCH=launch-c756fd73ed4547a2971081b4dda29a41
export A2A_LAUNCHES=/Users/luckye/Documents/Code/a2a/records/launches.jsonl
export CODEX_THREAD_ID=01a157cd-118a-7d90-b0f2-335c3606f045
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a/scripts/git-hooks
[[ "$(git branch --show-current)" == exec/t109 ]]
git diff --check
[[ "$(git rev-parse HEAD)" == a88604853e266649b72aad9401b6390961d866c6 ]]
git diff --cached --quiet
git add --sparse \
  workbench/tests/t107_sidebar_driver.mjs workbench/tests/test_t109_keyboard_entry.mjs \
  evidence/2026-10-20-batch18/T-109
git diff --cached --stat
git commit -m 'Activate isolated Electron app before hierarchy keyboard acceptance'
git log -1 --format=fuller
