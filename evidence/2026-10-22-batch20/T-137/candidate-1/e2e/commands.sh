#!/bin/zsh
# T-137 candidate 1 (code e58d30957, README and score-row style 1f7dac8b9), run from a clean detached worktree:
# git -C /private/tmp/a2a-t133-c1 checkout --detach 1f7dac8b9 (node_modules linked to the main checkout's).
# red-parent runs the new test on the code before T-137 (c24d58955). t136-green reruns the retrospective test (moved into Reflect,
# schedule now turned on by the test itself); t133-t107-green reruns the terminal-controller test on this code.
set -u
W=/private/tmp/a2a-t133-c1
E=/Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-137/candidate-1/e2e
T=$W/workbench/tests/test_t137_reflect_e2e.py
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; echo "$name exit=$?" >> $E/exits.txt; }
run green $T &
run red-parent $T --revision c24d58955 &
run mutant-schedule-on-by-default $T --mutant schedule-on-by-default &
wait
run mutant-ended-not-listed $T --mutant ended-not-listed &
run mutant-role-by-terminal-only $T --mutant role-by-terminal-only &
run mutant-score-on-attempt $T --mutant score-on-attempt &
wait
run t136-green $W/workbench/tests/test_t136_retrospective_e2e.py &
run t133-t107-green $W/workbench/tests/test_t133_t107_terminal_controller_e2e.py &
run t107-live-green $W/workbench/tests/test_t107_live_sidebar_e2e.py &
wait
