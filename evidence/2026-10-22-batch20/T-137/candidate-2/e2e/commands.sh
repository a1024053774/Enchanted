#!/bin/zsh
# Candidate 2 of T-133/T-107 and T-137 (code fbf68c404; tests and harness as of f602d95b1), after reviews 01.
# Run from a clean detached worktree: git -C /private/tmp/a2a-t133-c1 checkout --detach f602d95b1 (node_modules linked to the main checkout's).
# One script for both tickets; each summary goes to its ticket's candidate-2/e2e directory.
set -u
W=/private/tmp/a2a-t133-c1
B=/Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20
T133=$W/workbench/tests/test_t133_t107_terminal_controller_e2e.py
T137=$W/workbench/tests/test_t137_reflect_e2e.py
run() { local dir=$1 name=$2; shift 2; python3 "$@" --summary $B/$dir/candidate-2/e2e/$name.json > $B/$dir/candidate-2/e2e/$name.log 2>&1; echo "$name exit=$?" >> $B/$dir/candidate-2/e2e/exits.txt; }
run T-133-T-107 green $T133 &
run T-137 green $T137 &
run T-137 red-parent $T137 --revision c24d58955 &
wait
run T-133-T-107 red-parent $T133 --revision 836b9eeb0 &
run T-133-T-107 mutant-recorded-without-role $T133 --mutant recorded-without-role &
run T-137 mutant-defaults-overwrite-saved $T137 --mutant defaults-overwrite-saved &
wait
run T-137 mutant-role-by-terminal-only $T137 --mutant role-by-terminal-only &
run T-137 mutant-ended-not-listed $T137 --mutant ended-not-listed &
run T-137 mutant-score-on-attempt $T137 --mutant score-on-attempt &
wait
run T-137 mutant-schedule-on-by-default $T137 --mutant schedule-on-by-default &
run T-137 t136-green $W/workbench/tests/test_t136_retrospective_e2e.py &
run T-133-T-107 t133-t134-green $W/workbench/tests/test_t133_t134_records_metrics_e2e.py &
wait
run T-133-T-107 t107-live-green $W/workbench/tests/test_t107_live_sidebar_e2e.py

# T-133 green failed once on operation_busy from answer_issue (green.json, kept). After cb6e7d75c (the test retries only that error):
# git -C $W checkout --detach cb6e7d75c
# run T-133-T-107 green-02 $T133 & run T-133-T-107 mutant-recorded-without-role-02 $T133 --mutant recorded-without-role & wait
