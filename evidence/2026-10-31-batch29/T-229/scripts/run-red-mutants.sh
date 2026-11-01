#!/bin/zsh
# T-229 red (baseline revision) and mutant runs, from the main checkout.
cd /Users/luckye/Documents/Code/a2a
E=/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence
export TMPDIR=/private/tmp ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/a2a-worktrees/hc-cache
PY=/Applications/Xcode.app/Contents/Developer/usr/bin/python3
T=workbench/tests/test_t229_worker_input_e2e.py
run() { local name=$1; shift; echo "start $name $(date +%T)" >> $E/runs.log; "$@" > $E/$name.log 2>&1; echo "end $name exit=$? $(date +%T)" >> $E/runs.log; }
run red-claude $PY $T --cli claude --revision 59815ea30 --summary $E/red-claude.json
run red-codex $PY $T --cli codex --revision 59815ea30 --summary $E/red-codex.json
run mutant-no-claim-claude $PY $T --cli claude --mutant no-claim --summary $E/mutant-no-claim-claude.json
run mutant-attach-too-codex $PY $T --cli codex --mutant attach-too --summary $E/mutant-attach-too-codex.json
echo "all done $(date +%T)" >> $E/runs.log
