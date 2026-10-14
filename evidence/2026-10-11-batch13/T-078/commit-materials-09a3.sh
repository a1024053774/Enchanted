#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
git diff --check
git add -- evidence/2026-10-11-batch13/T-078/P2-APPROVAL-09A3.md evidence/2026-10-11-batch13/T-078/preparation-check-09a3.json evidence/2026-10-11-batch13/T-078/p1-materials-09a3 evidence/2026-10-11-batch13/T-078/p1-materials-09a3-block evidence/2026-10-11-batch13/T-078/RESULTS.md evidence/2026-10-11-batch13/T-078/commit-materials-09a3.sh
git diff --cached --stat
git commit -m 'docs(T-078): freeze clean and blocking 09A-3 launch materials'
git status --short
