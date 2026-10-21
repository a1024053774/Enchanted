#!/bin/bash
# 主控在沙箱外提交修复；只包含 #71 授权范围，不 push，不手写尾注。
set -euo pipefail
export LC_ALL=C
unset GIT_DIR GIT_WORK_TREE
cd "$(dirname "$0")/../../.."
test "$(git branch --show-current)" = exec/t114
test "$(git rev-parse HEAD)" = 488ffe3e98ad2ac11d53ad6709ee2cd780477ba2
test -z "$(git diff --cached --name-only)"
git add --sparse -- \
  workbench/app/package.mjs workbench/app/RUN-OUTSIDE-LOCAL-PACKAGE.sh \
  workbench/tests/run_t102_packaged.mjs workbench/README.md \
  evidence/2026-10-20-batch18/T-114/RUN-OUTSIDE-BUILD-02.sh \
  evidence/2026-10-20-batch18/T-114/RUN-OUTSIDE-COMMIT-02.sh \
  evidence/2026-10-20-batch18/T-114/RUN-OUTSIDE-COUNTEREXAMPLE-02.sh \
  evidence/2026-10-20-batch18/T-114/check-packaged-start.mjs \
  evidence/2026-10-20-batch18/T-114/WORKER-FIX-02.md \
  evidence/2026-10-20-batch18/T-114/name-reference-search-02.txt \
  evidence/2026-10-20-batch18/T-114/project-map-worker-fix-02.txt
git diff --cached --check
git commit -m "T-114: align Enchanted executable and helpers and verify packaged startup"
git log -1 --format=full
git status --short
