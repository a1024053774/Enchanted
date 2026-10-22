#!/bin/zsh
# T-131 candidate 1 (8f584d45c). Run from the repository root; each run writes its own summary.
set -u
E=evidence/2026-10-22-batch20/T-131/candidate-1/e2e
T=workbench/tests/test_t131_parallel_workers_e2e.py
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; echo "$name exit=$?" >> $E/exits.txt; }
run green $T &
run foreign-ref $T --foreign-ref &
run red-parent $T --revision 03b2d66a3 &
wait
run mutant-strict-ref-equality $T --mutant strict-ref-equality &
run mutant-integration-chain-ignored $T --mutant integration-chain-ignored &
run mutant-any-ref-accepted $T --foreign-ref --mutant any-ref-accepted &
wait
run t122-green workbench/tests/test_t122_claude_worker_e2e.py
