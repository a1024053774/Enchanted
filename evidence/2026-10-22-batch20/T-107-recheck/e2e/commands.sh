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
# Focus of a pane opened from the sidebar (89cc73645). Green from a clean detached worktree of 89cc73645
# (/private/tmp/a2a-t107-focus); the mutant from a second one (/private/tmp/a2a-t107-focus-red) with only
# workbench/app/renderer.tsx put back to 89cc73645^ (focus requested while the replay is hidden). Both with
# workbench/node_modules linked to the main checkout's. T-109 runs on the main checkout at 89cc73645 (it requires a real
# node_modules directory).
D=/Users/luckye/Documents/Code/a2a/workbench/node_modules
X=$D/electron/dist
python3 /private/tmp/a2a-t107-focus/workbench/tests/run_t107_sidebar.py --source /private/tmp/a2a-t107-focus --dependencies $D \
  --electron-dist $X --summary $E/t107-sidebar-rerun-08.json > $E/t107-sidebar-rerun-08.log 2>&1
echo "t107-sidebar-rerun-08 exit=$?" >> $E/exits.txt
python3 /private/tmp/a2a-t107-focus-red/workbench/tests/run_t107_sidebar.py --source /private/tmp/a2a-t107-focus-red --dependencies $D \
  --electron-dist $X --summary $E/t107-sidebar-mutant-focus-while-hidden.json > $E/t107-sidebar-mutant-focus-while-hidden.log 2>&1
echo "t107-sidebar-mutant-focus-while-hidden exit=$?" >> $E/exits.txt
python3 /private/tmp/a2a-t107-focus/workbench/tests/test_t107_live_sidebar_e2e.py --summary $E/live-green-89cc.json > $E/live-green-89cc.log 2>&1
echo "live-green-89cc exit=$?" >> $E/exits.txt
python3 /Users/luckye/Documents/Code/a2a/workbench/tests/run_t109_hierarchy.py --source /Users/luckye/Documents/Code/a2a --electron-dist $X \
  --summary $E/t109-hierarchy-89cc.json > $E/t109-hierarchy-89cc.log 2>&1
echo "t109-hierarchy-89cc exit=$?" >> $E/exits.txt
# The three runs above that failed did so on a full disk (git: "Out of diskspace"; the readonly probe's cpSync), not on a
# check: 53 probe runs had each left a ~500 MB node_modules copy in /private/tmp (fixed in b76847c24). Rerun at b76847c24,
# same worktrees moved to that commit, the mutant again with only renderer.tsx put back to 89cc73645^:
python3 /private/tmp/a2a-t107-focus/workbench/tests/run_t107_sidebar.py --source /private/tmp/a2a-t107-focus --dependencies $D \
  --electron-dist $X --summary $E/t107-sidebar-rerun-09.json > $E/t107-sidebar-rerun-09.log 2>&1
echo "t107-sidebar-rerun-09 exit=$?" >> $E/exits.txt
python3 /private/tmp/a2a-t107-focus-red/workbench/tests/run_t107_sidebar.py --source /private/tmp/a2a-t107-focus-red --dependencies $D \
  --electron-dist $X --summary $E/t107-sidebar-mutant-focus-while-hidden-02.json > $E/t107-sidebar-mutant-focus-while-hidden-02.log 2>&1
echo "t107-sidebar-mutant-focus-while-hidden-02 exit=$?" >> $E/exits.txt
python3 /Users/luckye/Documents/Code/a2a/workbench/tests/run_t109_hierarchy.py --source /Users/luckye/Documents/Code/a2a --electron-dist $X \
  --summary $E/t109-hierarchy-b768.json > $E/t109-hierarchy-b768.log 2>&1
echo "t109-hierarchy-b768 exit=$?" >> $E/exits.txt
# T-107 project-row summary ("有等待用户回答的项目行最醒目，回答后恢复"), checks added to the Codex terminal controller test
# at df8f972a4 (scripted model, no model calls); green and the mutant that drops the row's count, worktree /private/tmp/a2a-t107-focus at df8f972a4:
python3 /private/tmp/a2a-t107-focus/workbench/tests/test_t133_codex_terminal_controller_e2e.py --summary $E/codex-row-green.json > $E/codex-row-green.log 2>&1; echo "codex-row-green exit=$?" >> $E/exits.txt
python3 /private/tmp/a2a-t107-focus/workbench/tests/test_t133_codex_terminal_controller_e2e.py --mutant project-needs-hidden --summary $E/codex-row-mutant-project-needs-hidden.json > $E/codex-row-mutant-project-needs-hidden.log 2>&1
echo "codex-row-mutant-project-needs-hidden exit=$?" >> $E/exits.txt
