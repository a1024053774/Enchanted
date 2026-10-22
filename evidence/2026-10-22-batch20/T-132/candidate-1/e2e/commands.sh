#!/bin/zsh
# T-132 candidate 1 (dc4d2e257). Run from the repository root; each run writes its own summary, and the fixture's
# out/ directory holds the screenshots.
set -u
E=evidence/2026-10-22-batch20/T-132/candidate-1/e2e
T=workbench/tests/test_t132_issues_panel_e2e.py
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; echo "$name exit=$?" >> $E/exits.txt; }
run green $T &
run red-parent $T --revision 85b212a60 &
run mutant-error-shown-as-empty $T --mutant error-shown-as-empty &
wait
run mutant-disposition-as-executor $T --mutant disposition-as-executor &
run t122-green workbench/tests/test_t122_claude_worker_e2e.py &
wait
# Harness fix 07dc957c3 (source copies lacked LICENSE.synara; first attempt kept in harness-failure-01/): rerun the three copied-source runs.
run red-parent $T --revision 85b212a60 &
run mutant-error-shown-as-empty $T --mutant error-shown-as-empty &
run mutant-disposition-as-executor $T --mutant disposition-as-executor &
wait
