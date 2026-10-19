#!/bin/bash
# 主控 #19 授权合入 main；冲突保留给 worker 解决，不 rebase、不 abort。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t104
[[ "$(git branch --show-current)" == exec/t104 ]]
[[ "$(git rev-parse HEAD)" == c6dd956f0* ]]
git diff --quiet
git diff --cached --quiet
export A2A_PROJECT=a2a A2A_TASK=T-104 A2A_ATTEMPT=a1 A2A_ROLE=worker
export A2A_SESSION=8fbb58f9-18ea-43e8-a0e3-facbc7edcaad
export A2A_LAUNCH=launch-04f00c94021d4e9c9618c151af840bde
export A2A_LAUNCHES=/Users/luckye/Documents/Code/a2a/records/launches.jsonl
export CODEX_THREAD_ID=01a1527f-e702-7c20-9ee3-6758a25c911c
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a/scripts/git-hooks
git merge --no-edit main
