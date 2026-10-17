#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
test "$(git rev-parse HEAD)" = dc67ce58b3300503bf31873d7c3c69c8d56b941f
test -z "$(git diff -- workbench/src workbench/app workbench/hooks)"
git diff --check
git add -- workbench/tests/p1_processes.py workbench/tests/run_t078_p1.py workbench/tests/test_t078_cleanup_lifetime.py workbench/tests/test_t078_cleanup_probe_locale.py evidence/2026-10-11-batch13/T-078
git add -- .project-map/inbox/20261014T191104Z-worker:t078-09bc-plan-issue-001.md
git add -- .project-map/inbox/20261014T191237Z-worker:t078-09bc-plan-report-001.md
git diff --cached --stat
git commit -m 'fix(T-078): verify cleanup lifetime and preserve 09A closeout with 09BC plan'
git status --short
