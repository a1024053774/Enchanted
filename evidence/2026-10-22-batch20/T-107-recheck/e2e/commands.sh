#!/bin/zsh
# T-107 recheck after T-131, test at 03dff08c1, run from a clean detached worktree of that commit:
# git worktree add --detach /private/tmp/a2a-t107-re 03dff08c1, with workbench/node_modules linked to the main checkout's.
# red-before-t131 runs the test against 03b2d66a3 (before T-131: one worker at a time).
set -u
W=/private/tmp/a2a-t107-re
E=/Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-107-recheck/e2e
T=$W/workbench/tests/test_t107_live_sidebar_e2e.py
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; echo "$name exit=$?" >> $E/exits.txt; }
run green $T &
run red-before-t131 $T --revision 03b2d66a3 &
wait
run mutant-terminal-shown-idle $T --mutant terminal-shown-idle &
run mutant-parent-launch-ignored $T --mutant parent-launch-ignored &
wait
# (t107-sidebar-rerun ran at 03dff08c1; t107-sidebar-rerun-02 after git -C $W checkout --detach cd8037ba4, the harness fix.)
# The 2026-10-19 sidebar run (saved launch facts replayed through real recovery: unrestored states, focus of historical
# panes, read-only sidebar), rerun on the current code:
python3 $W/workbench/tests/run_t107_sidebar.py --source $W --dependencies /Users/luckye/Documents/Code/a2a/workbench/node_modules \
  --electron-dist /Users/luckye/Documents/Code/a2a/workbench/node_modules/electron/dist --summary $E/t107-sidebar-rerun.json > $E/t107-sidebar-rerun.log 2>&1
echo "t107-sidebar-rerun exit=$?" >> $E/exits.txt
