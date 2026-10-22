#!/bin/zsh
# T-133/T-134 candidate 2 (8a8e1720c), run from a clean detached worktree of that commit:
# git worktree add --detach /private/tmp/a2a-t133-c2 8a8e1720c, with workbench/node_modules linked to the main checkout's.
# red-candidate-1-range runs this test against candidate 1's code (e4d45c511).
set -u
W=/private/tmp/a2a-t133-c2
E=/Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-133-T-134/candidate-2/e2e
T=$W/workbench/tests/test_t133_t134_records_metrics_e2e.py
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; echo "$name exit=$?" >> $E/exits.txt; }
run green $T &
run red-candidate-1-range $T --revision e4d45c511 &
run mutant-range-by-created-only $T --mutant range-by-created-only &
wait
