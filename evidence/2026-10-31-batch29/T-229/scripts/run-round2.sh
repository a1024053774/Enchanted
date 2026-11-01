#!/bin/zsh
# T-229 managed-input greens with the Ctrl-C scenario, the draft mutants, and the updated T-206 test.
cd /Users/luckye/Documents/Code/a2a
E=/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence
export TMPDIR=/private/tmp ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/a2a-worktrees/hc-cache
PY=/Applications/Xcode.app/Contents/Developer/usr/bin/python3
M=workbench/tests/test_t229_managed_input_e2e.py
run() { local name=$1; shift; echo "start $name $(date +%T)" >> $E/runs.log; "$@" > $E/$name.log 2>&1; echo "end $name exit=$? $(date +%T)" >> $E/runs.log; }
run green-opencode-03 python3 $M --cli opencode --summary $E/green-opencode-03.json
run green-agy-03 python3 $M --cli agy --summary $E/green-agy-03.json
run mutant-cursor-ignored-opencode python3 $M --cli opencode --mutant cursor-ignored --summary $E/mutant-cursor-ignored-opencode.json
run mutant-ctrl-c-keeps-draft-agy python3 $M --cli agy --mutant ctrl-c-keeps-draft --summary $E/mutant-ctrl-c-keeps-draft-agy.json
run t206-green $PY workbench/tests/test_t206_input_on_send_e2e.py --summary $E/t206-green.json
run t206-mutant-record-every-key $PY workbench/tests/test_t206_input_on_send_e2e.py --mutant record-every-key --summary $E/t206-mutant-record-every-key.json
echo "round2 done $(date +%T)" >> $E/runs.log
