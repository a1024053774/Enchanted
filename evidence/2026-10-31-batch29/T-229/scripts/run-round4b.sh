#!/bin/zsh
# T-229 round 4b: diagnostic-fails waits a fixed time so a mutant fails on the business checks.
cd /Users/luckye/Documents/Code/a2a
E=/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence
export TMPDIR=/private/tmp ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/a2a-worktrees/hc-cache
PY=/Applications/Xcode.app/Contents/Developer/usr/bin/python3
T=workbench/tests/test_t229_worker_input_e2e.py
run() { local name=$1; shift; echo "start $name $(date +%T)" >> $E/runs.log; "$@" > $E/$name.log 2>&1; echo "end $name exit=$? $(date +%T)" >> $E/runs.log; }
run r4b-mutant-diagnostic-unguarded-claude $PY $T --cli claude --case diagnostic-fails --mutant diagnostic-unguarded --summary $E/r4b-mutant-diagnostic-unguarded-claude.json
run r4b-mutant-diagnostic-unguarded-codex $PY $T --cli codex --case diagnostic-fails --mutant diagnostic-unguarded --summary $E/r4b-mutant-diagnostic-unguarded-codex.json
run r4b-diag-claude $PY $T --cli claude --case diagnostic-fails --summary $E/r4b-diag-claude.json
run r4b-diag-codex $PY $T --cli codex --case diagnostic-fails --summary $E/r4b-diag-codex.json
echo "round4b done $(date +%T)" >> $E/runs.log
