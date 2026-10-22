#!/bin/zsh
# T-133/T-134 candidate 1 (e4d45c511), run from a clean detached worktree of that commit:
# git worktree add --detach /private/tmp/a2a-t133-c1b e4d45c511, with workbench/node_modules linked to the main checkout's.
# probe-green-01..03 are earlier tries of the test while it was being written (task type, window_open scope); kept as found.
set -u
W=/private/tmp/a2a-t133-c1b
E=/Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-133-T-134/candidate-1/e2e
T=$W/workbench/tests/test_t133_t134_records_metrics_e2e.py
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; echo "$name exit=$?" >> $E/exits.txt; }
run green $T &
run red-parent $T --revision 7dd585c92 &
run mutant-intervention-unmarked $T --mutant intervention-unmarked &
wait
run mutant-requested-as-observed $T --mutant requested-as-observed &
run mutant-intervention-ignored $T --mutant intervention-ignored &
run mutant-error-shown-as-empty $T --mutant error-shown-as-empty &
wait
run t122-green $W/workbench/tests/test_t122_claude_worker_e2e.py
