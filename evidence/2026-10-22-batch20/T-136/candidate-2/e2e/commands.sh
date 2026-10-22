#!/bin/zsh
# T-136 candidate 2 (338c51b4f), run from a clean detached worktree of that commit:
# git -C /private/tmp/a2a-t136-c1 checkout --detach 338c51b4f (node_modules linked to the main checkout's).
# red-candidate-1 runs this test against candidate 1's code (01e0effd7). t135-green covers the archive change.
set -u
W=/private/tmp/a2a-t136-c1
E=/Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-2/e2e
T=$W/workbench/tests/test_t136_retrospective_e2e.py
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; echo "$name exit=$?" >> $E/exits.txt; }
run green $T &
run red-candidate-1 $T --revision 01e0effd7 &
run mutant-archive-not-in-range $T --mutant archive-not-in-range &
wait
run mutant-start-failure-silent $T --mutant start-failure-silent &
run t135-green $W/workbench/tests/test_t135_trajectory_archive_e2e.py &
wait
