#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
test "$(git rev-parse HEAD)" = 166509267fe11f02b1591f2089a77d7480a0c1e6
test -z "$(git diff -- workbench)"
git diff --check
git add -- evidence/2026-10-11-batch13/T-078/P2-APPROVAL-09A3R.md evidence/2026-10-11-batch13/T-078/p1-materials-09a3r evidence/2026-10-11-batch13/T-078/p1-materials-09a3r-block evidence/2026-10-11-batch13/T-078/preparation-generation-09a3r evidence/2026-10-11-batch13/T-078/preparation-check-09a3r.json evidence/2026-10-11-batch13/T-078/source-freeze-09a3r.json evidence/2026-10-11-batch13/T-078/RESULTS.md evidence/2026-10-11-batch13/T-078/commit-materials-09a3r.sh evidence/2026-10-11-batch13/T-078/materials-delivery-check-09a3r.json evidence/2026-10-11-batch13/T-078/materials-project-status-09a3r.txt
git add -- evidence/2026-10-11-batch13/T-078/SLOT-CLEANUP-DOC-ISSUE-09A3R.md .project-map/inbox/20261014T173439Z-worker:t078-09a3r-issue-001.md
git add -- .project-map/inbox/20261014T173744Z-worker:t078-09a3r-report-001.md
git diff --cached --stat
git commit -m 'docs(T-078): prepare fresh rebased clean and blocking 09A-3R materials'
git status --short
