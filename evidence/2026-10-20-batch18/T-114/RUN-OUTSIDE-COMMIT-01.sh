#!/bin/bash
# 由执行主控在沙箱外提交本次明确列出的文件；不 push，不手写尾注。
set -euo pipefail
export LC_ALL=C
unset GIT_DIR GIT_WORK_TREE
cd "$(dirname "$0")/../../.."
test "$(git branch --show-current)" = exec/t114
test "$(git rev-parse HEAD)" = b71fc9b36beb64d9adf811ead64669b2d964fb33
test -z "$(git diff --cached --name-only)"
git add --sparse -- \
  README.md workbench/README.md \
  workbench/app/package.mjs workbench/app/desktop.mjs \
  workbench/app/main.ts workbench/app/index.html workbench/app/renderer.tsx \
  evidence/2026-10-20-batch18/T-114/RUN-OUTSIDE-BUILD-01.sh \
  evidence/2026-10-20-batch18/T-114/RUN-OUTSIDE-COMMIT-01.sh \
  evidence/2026-10-20-batch18/T-114/WORKER-RESULTS.md \
  evidence/2026-10-20-batch18/T-114/worker-baseline.json \
  evidence/2026-10-20-batch18/T-114/project-map-worker-end.txt \
  evidence/2026-10-20-batch18/T-114/git-add-sandbox-denied.txt
git diff --cached --check
git commit -m "T-114: name the desktop app Enchanted and update Chinese homepage"
git log -1 --format=full
git status --short
