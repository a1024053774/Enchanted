#!/bin/zsh
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t112
unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE
export LC_ALL=C PYTHONDONTWRITEBYTECODE=1
export A2A_TASK=T-112
export A2A_ATTEMPT=a1
export A2A_SESSION=a1823572-94e7-4583-b6e7-0be9349bc52f
export A2A_ROLE=worker
export A2A_PROJECT=a2a
export A2A_LAUNCH=launch-4bae242ff4df4772b0a47a50c4eabdc9
export A2A_LAUNCHES=/Users/luckye/Documents/Code/a2a/records/launches.jsonl
export CODEX_THREAD_ID=01a15956-4232-7ee0-8601-276763e7e41a
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a/scripts/git-hooks
git diff --check
git add --sparse -- workbench/tests/run_t112_native.py evidence/2026-10-20-batch18/T-112
git commit -m '按用户裁定验证 T-112 未知 effort 原样透传'
git show -s --format=full HEAD
git status --short
