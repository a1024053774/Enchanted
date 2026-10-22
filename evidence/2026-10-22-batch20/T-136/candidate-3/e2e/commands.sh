#!/bin/zsh
# T-136 candidate 3 (077b83728), run from a clean detached worktree of that commit:
# git worktree add --detach /private/tmp/a2a-t136-c3 077b83728, with workbench/node_modules linked to the main checkout's.
# red-candidate-2 runs this test against candidate 2's code (338c51b4f).
set -u
W=/private/tmp/a2a-t136-c3
E=/Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-3/e2e
T=$W/workbench/tests/test_t136_retrospective_e2e.py
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; echo "$name exit=$?" >> $E/exits.txt; }
run green $T &
run red-candidate-2 $T --revision 338c51b4f &
run mutant-since-after-failed-run $T --mutant since-after-failed-run &
wait
