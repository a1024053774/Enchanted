#!/bin/zsh
# T-136 candidate 1 (01e0effd7), run from a clean detached worktree of that commit:
# git worktree add --detach /private/tmp/a2a-t136-c1 01e0effd7, with workbench/node_modules linked to the main checkout's.
# red-parent runs the test against 1dc2b76c3 (same workbench tree as 8a8e1720c, before retrospectives).
# t135-green, t132-green and t122-green are regressions for the archive sweep change, the keyed pages, and the worker path.
set -u
W=/private/tmp/a2a-t136-c1
E=/Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-1/e2e
T=$W/workbench/tests/test_t136_retrospective_e2e.py
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; echo "$name exit=$?" >> $E/exits.txt; }
run green $T &
run red-parent $T --revision 1dc2b76c3 &
run mutant-package-ignores-range $T --mutant package-ignores-range &
wait
run mutant-out-not-confined $T --mutant out-not-confined &
run mutant-schedule-fires-when-disabled $T --mutant schedule-fires-when-disabled &
run mutant-import-failure-silent $T --mutant import-failure-silent &
wait
run mutant-archive-source-not-isolated $T --mutant archive-source-not-isolated &
run t135-green $W/workbench/tests/test_t135_trajectory_archive_e2e.py &
run t132-green $W/workbench/tests/test_t132_issues_panel_e2e.py &
wait
run t122-green $W/workbench/tests/test_t122_claude_worker_e2e.py
