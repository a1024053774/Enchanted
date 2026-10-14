#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
test "$(git rev-parse HEAD)" = 643d59bfadbf07466ee28d57f471b8ef3d10646f
test -z "$(git diff -- workbench)"
git diff --check
git add -- evidence/2026-10-11-batch13/T-078/P2-APPROVAL-09A3R2.md evidence/2026-10-11-batch13/T-078/source-freeze-09a3r2.json evidence/2026-10-11-batch13/T-078/p1-materials-09a3r2 evidence/2026-10-11-batch13/T-078/p1-materials-09a3r2-block evidence/2026-10-11-batch13/T-078/preparation-generation-09a3r2 evidence/2026-10-11-batch13/T-078/preparation-check-09a3r2.json evidence/2026-10-11-batch13/T-078/materials-delivery-check-09a3r2.json evidence/2026-10-11-batch13/T-078/materials-project-status-09a3r2.txt evidence/2026-10-11-batch13/T-078/commit-materials-09a3r2.sh evidence/2026-10-11-batch13/T-078/RESULTS.md
git add -- .project-map/inbox/20261014T181011Z-worker:t078-09a3r2-report-001.md
git diff --cached --stat
git commit -m 'docs(T-078): freeze approved simulated-user 09A-3R2 launch materials'
git status --short
