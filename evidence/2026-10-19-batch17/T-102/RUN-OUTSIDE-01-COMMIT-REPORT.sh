#!/bin/bash
# 执行主控在沙箱外运行：只提交 T-102 的阻塞报告和基线证据，不提交产品候选。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t102
if [[ "$(git rev-parse HEAD)" != 803e6cf69abbd7727c3694a446a52eb5940ddf2e ]]; then
  echo '起点已改变；请先核对 T-101 的历史映射，再更新本脚本起点。' >&2
  exit 1
fi
git diff --cached --quiet || { echo '暂存区已有内容；保留现场，停止。' >&2; exit 1; }

# 使用当前 worker 的真实启动绑定；尾注由既有钩子生成。
export A2A_PROJECT=a2a A2A_TASK=T-102 A2A_ATTEMPT=a1 A2A_ROLE=worker
export A2A_SESSION=b39683a9-f281-4941-aa23-d4479d9a917d
export A2A_LAUNCH=launch-60574dbe21504c0594fc02ef9a2475e3
export A2A_LAUNCHES=/Users/luckye/Documents/Code/a2a/records/launches.jsonl
export CODEX_THREAD_ID=01a15278-4b82-7963-8301-50cf9e0de9cd
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a/scripts/git-hooks
test -x "$GIT_CONFIG_VALUE_0/prepare-commit-msg"

git add --sparse -- \
  evidence/2026-10-19-batch17/T-102/PROBE-BASELINE.py \
  evidence/2026-10-19-batch17/T-102/RUN-OUTSIDE-01-COMMIT-REPORT.sh \
  evidence/2026-10-19-batch17/T-102/RESULTS.md \
  evidence/2026-10-19-batch17/T-102/baseline-01.json \
  evidence/2026-10-19-batch17/T-102/project-map-end.txt
git diff --cached --check
git commit -m 'docs(T-102): report packaging prerequisites and blocked baseline'
git log -1 --format=fuller
git status --short --branch
