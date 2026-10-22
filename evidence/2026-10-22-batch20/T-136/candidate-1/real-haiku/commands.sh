#!/bin/zsh
# T-136 real run: the user's own Claude Code (claude-haiku-5-5), started from the desktop's 立即复盘, from the clean
# detached worktree of 01e0effd7. The project directory is a path the user's own Claude already trusts and does not
# exist beforehand; it is removed afterwards.
set -u
W=/private/tmp/a2a-t136-c1
E=/Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-1/real-haiku
python3 $W/workbench/tests/run_t136_real_haiku.py --repo /private/tmp/t121-ui-UpJ0/repos/demo --summary $E/run-01.json > $E/run-01.log 2>&1
echo "run-01 exit=$?" >> $E/exits.txt
# run-02: after git -C $W checkout --detach cae0e4c81 (USER/LOGNAME passed; run 01's Claude was not logged in).
python3 $W/workbench/tests/run_t136_real_haiku.py --repo /private/tmp/t121-ui-UpJ0/repos/demo --summary $E/run-02.json > $E/run-02.log 2>&1
echo "run-02 exit=$?" >> $E/exits.txt
