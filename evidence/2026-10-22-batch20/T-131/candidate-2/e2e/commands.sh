#!/bin/zsh
# T-131 candidate 2 (c6921bf44), run from a clean detached worktree of that commit so uncommitted work in the
# main checkout cannot leak in: git worktree add --detach /private/tmp/a2a-t131-c2 c6921bf44, with workbench/node_modules
# linked to the main checkout's. Summaries are written into the main checkout's evidence directory.
set -u
W=/private/tmp/a2a-t131-c2
E=/Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-131/candidate-2/e2e
T=$W/workbench/tests/test_t131_parallel_workers_e2e.py
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; echo "$name exit=$?" >> $E/exits.txt; }
run green $T &
run foreign-plain $T --foreign-ref plain &
run foreign-other-task $T --foreign-ref other-task &
wait
run mutant-strict-ref-equality $T --mutant strict-ref-equality &
run mutant-integration-chain-ignored $T --mutant integration-chain-ignored &
run mutant-any-ref-accepted $T --foreign-ref plain --mutant any-ref-accepted &
wait
run mutant-other-namespace-prefix-only $T --foreign-ref other-task --mutant other-namespace-prefix-only &
run red-parent $T --revision 03b2d66a3 &
run t122-green $W/workbench/tests/test_t122_claude_worker_e2e.py &
wait
