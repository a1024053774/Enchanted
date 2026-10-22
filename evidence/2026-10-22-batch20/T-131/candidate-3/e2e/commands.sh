#!/bin/zsh
# T-131 candidate 3 (d436fd390), run from a clean detached worktree of that commit:
# git worktree add --detach /private/tmp/a2a-t131-c3 d436fd390, with workbench/node_modules linked to the main checkout's.
# The red run on candidate 2 (red-candidate-2-retained) used the main checkout's test with --revision ea68df9d9 before the fix.
set -u
W=/private/tmp/a2a-t131-c3
E=/Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-131/candidate-3/e2e
T=$W/workbench/tests/test_t131_parallel_workers_e2e.py
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; echo "$name exit=$?" >> $E/exits.txt; }
run green $T &
run retained-ref $T --retained-ref &
run foreign-other-task $T --foreign-ref other-task &
wait
run foreign-plain $T --foreign-ref plain &
run mutant-strict-ref-equality $T --mutant strict-ref-equality &
run mutant-other-namespace-prefix-only $T --foreign-ref other-task --mutant other-namespace-prefix-only &
wait
run mutant-integration-chain-ignored $T --mutant integration-chain-ignored &
run mutant-any-ref-accepted $T --foreign-ref plain --mutant any-ref-accepted &
run t122-green $W/workbench/tests/test_t122_claude_worker_e2e.py &
wait
