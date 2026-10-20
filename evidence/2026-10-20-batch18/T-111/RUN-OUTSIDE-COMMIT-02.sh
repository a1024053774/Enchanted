#!/bin/zsh
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t111
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
export LC_ALL=C
export A2A_PROJECT=a2a A2A_TASK=T-111 A2A_ATTEMPT=a1 A2A_ROLE=worker
export A2A_SESSION=10858660-9c4e-4904-9811-feb626a89c75
export A2A_LAUNCH=launch-c9958cdeceed4ee2a1b96ada1da39586
export A2A_LAUNCHES=/Users/luckye/Documents/Code/a2a/records/launches.jsonl
export CODEX_THREAD_ID=01a1580e-96ab-73d2-b5a5-c7f825736cab
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a/scripts/git-hooks
[[ "$(git branch --show-current)" == exec/t111 ]]
[[ "$(git rev-parse HEAD)" == 862ca16709ec5936de8c769ce62dc4b0401dad22 ]]
git diff --check
git diff --cached --quiet
git add --sparse workbench/tests/test_t107_daemon_readonly.mjs workbench/tests/run_t111_flow.py \
  evidence/2026-10-20-batch18/T-111
git diff --cached --stat
git commit -m 'Prepare executable node-pty helpers only in private test runtimes'
git log -1 --format=fuller
