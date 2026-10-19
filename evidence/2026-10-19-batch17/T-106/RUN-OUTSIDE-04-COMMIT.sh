#!/bin/bash
# 主控在沙箱外提交本 worker 的 P1 修复；保留原钩子，不手写尾注。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t106
[ "$(git branch --show-current)" = exec/t106 ]
[ "$(git rev-parse HEAD)" = 24cacef60f9e88103213c0bb93eecb0cb5c41cf3 ]
python3 - <<'CHECK'
import subprocess
names=subprocess.check_output(["git","diff","--cached","--name-only"],text=True).splitlines()
allowed={"workbench/README.md", "workbench/app/main.ts", "workbench/app/renderer.tsx", "workbench/tests/test_t106_postcommit.mjs", "workbench/tests/run_t106_postcommit_electron.py"}
assert names and all(p in allowed or p.startswith("evidence/2026-10-19-batch17/T-106/postcommit-") or p in {"evidence/2026-10-19-batch17/T-106/RESULTS-postcommit.md", "evidence/2026-10-19-batch17/T-106/RUN-OUTSIDE-03-POSTCOMMIT.sh", "evidence/2026-10-19-batch17/T-106/RUN-OUTSIDE-04-COMMIT.sh"} for p in names), names
subprocess.run(["git","diff","--exit-code","--","workbench"],check=True)
CHECK
git diff --cached --check
export A2A_PROJECT=a2a
export A2A_TASK=T-106
export A2A_ATTEMPT=a1
export A2A_SESSION=46c7c0a5-076f-48e7-adc0-4aea62a637a9
export A2A_ROLE=worker
export A2A_LAUNCH=launch-d83c474a34f148c19f8e35e9bd60ff71
export A2A_LAUNCHES=/Users/luckye/Documents/Code/a2a/records/launches.jsonl
export CODEX_THREAD_ID=01a15447-8801-7603-bab4-28ef3ed32a7b
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a/scripts/git-hooks
git commit -m 'T-106: verify uncertain card and task registration outcomes'
git log -1 --format=full
git status --short
