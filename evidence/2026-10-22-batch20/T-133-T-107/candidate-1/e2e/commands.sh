#!/bin/zsh
# T-133 option A and T-107 #2 #4 #5, candidate 1 (code 36fa74f6a; tests as of c24d58955), run from a clean detached worktree:
# git worktree add --detach /private/tmp/a2a-t133-c1 c24d58955 (node_modules linked to the main checkout's).
# red-parent runs the new test against the code before this change (836b9eeb0). The other tests are regressions of
# the areas this change touches: records page (T-133/T-134), live sidebar (T-107), role requests (T-121),
# the terminal socket (T-126) and a terminal controller whose CLI now loads the plugin's hooks (T-124).
set -u
W=/private/tmp/a2a-t133-c1
E=/Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-133-T-107/candidate-1/e2e
T=$W/workbench/tests/test_t133_t107_terminal_controller_e2e.py
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; echo "$name exit=$?" >> $E/exits.txt; }
run green $T &
run red-parent $T --revision 836b9eeb0 &
run mutant-recorded-without-role $T --mutant recorded-without-role &
wait
run mutant-terminal-state-unknown $T --mutant terminal-state-unknown &
run mutant-parent-not-saved $T --mutant parent-not-saved &
run t133-t134-green $W/workbench/tests/test_t133_t134_records_metrics_e2e.py &
wait
run t107-live-green $W/workbench/tests/test_t107_live_sidebar_e2e.py &
run t107-live-mutant-terminal-shown-idle $W/workbench/tests/test_t107_live_sidebar_e2e.py --mutant terminal-shown-idle &
run t121-green $W/workbench/tests/test_t121_role_request_e2e.py &
wait
run t126-green $W/workbench/tests/test_t126_terminal_socket_e2e.py &
run t124-green $W/workbench/tests/test_t124_controller_e2e.py &
wait
