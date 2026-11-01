#!/bin/zsh
# T-229 after review 01: resend-claimed-dispatch scenario, record-fails fault case, and mutants.
cd /Users/luckye/Documents/Code/a2a
E=/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence
export TMPDIR=/private/tmp ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/a2a-worktrees/hc-cache
PY=/Applications/Xcode.app/Contents/Developer/usr/bin/python3
T=workbench/tests/test_t229_worker_input_e2e.py
run() { local name=$1; shift; echo "start $name $(date +%T)" >> $E/runs.log; "$@" > $E/$name.log 2>&1; echo "end $name exit=$? $(date +%T)" >> $E/runs.log; }
run r3-claude $PY $T --cli claude --summary $E/r3-claude.json
run r3-codex $PY $T --cli codex --summary $E/r3-codex.json
run r3-fails-claude $PY $T --cli claude --case record-fails --summary $E/r3-fails-claude.json
run r3-fails-codex $PY $T --cli codex --case record-fails --summary $E/r3-fails-codex.json
run r3-mutant-no-block-claude $PY $T --cli claude --case record-fails --mutant no-block --summary $E/r3-mutant-no-block-claude.json
run r3-mutant-no-block-codex $PY $T --cli codex --case record-fails --mutant no-block --summary $E/r3-mutant-no-block-codex.json
run r3-mutant-no-claim-codex $PY $T --cli codex --mutant no-claim --summary $E/r3-mutant-no-claim-codex.json
echo "round3 done $(date +%T)" >> $E/runs.log
