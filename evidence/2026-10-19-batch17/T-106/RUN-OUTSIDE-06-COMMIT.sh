#!/bin/bash
# 主控在沙箱外提交本 worker 的 P2 修复；尾注由原钩子添加。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t106
[ "$(git branch --show-current)" = exec/t106 ]
[ "$(git rev-parse HEAD)" = 5036a8dc32de265dc27499028f0b938db3d1a15a ]
python3 - <<'CHECK'
import subprocess
names=subprocess.check_output(["git","diff","--cached","--name-only"],text=True).splitlines()
allowed={"workbench/README.md", "workbench/app/main.ts", "workbench/app/renderer.tsx", "workbench/tests/test_t106_creation.mjs", "evidence/2026-10-19-batch17/T-106/RESULTS-preflight.md", "evidence/2026-10-19-batch17/T-106/RUN-OUTSIDE-05-PREFLIGHT.sh", "evidence/2026-10-19-batch17/T-106/RUN-OUTSIDE-06-COMMIT.sh"}
assert names and all(p in allowed or p.startswith("evidence/2026-10-19-batch17/T-106/preflight-") for p in names), names
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
git commit -m 'T-106: return structured preflight form refusals'
git log -1 --format=full
git status --short
