#!/bin/zsh
# T-132 candidate 2 (7dd585c92), run from a clean detached worktree of that commit:
# git worktree add --detach /private/tmp/a2a-t132-c2 7dd585c92, with workbench/node_modules linked to the main checkout's.
# red-candidate-1-* run the same test against candidate 1's code (--revision ea68df9d9).
set -u
W=/private/tmp/a2a-t132-c2
E=/Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-132/candidate-2/e2e
T=$W/workbench/tests/test_t132_issues_panel_e2e.py
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; echo "$name exit=$?" >> $E/exits.txt; }
run green $T &
run empty-failure $T --empty-failure &
run red-candidate-1 $T --revision ea68df9d9 &
wait
run red-candidate-1-empty-failure $T --empty-failure --revision ea68df9d9 &
run mutant-cards-dropped-on-error $T --mutant cards-dropped-on-error &
run mutant-empty-shown-with-error $T --empty-failure --mutant empty-shown-with-error &
wait
run mutant-error-shown-as-empty $T --mutant error-shown-as-empty &
run mutant-disposition-as-executor $T --mutant disposition-as-executor &
run t122-green $W/workbench/tests/test_t122_claude_worker_e2e.py &
wait
