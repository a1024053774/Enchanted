#!/bin/zsh
# T-229 round 7d (resumed after the pause): the round-7b runs that hit the daemon start deadline (load 8-9 from other apps). Each case is retried
# only while its run fails at daemon_start, up to three attempts; every attempt keeps its own log and summary.
cd /Users/luckye/Documents/Code/a2a
E=/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence
export TMPDIR=/private/tmp ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/a2a-worktrees/hc-cache
PY=/Applications/Xcode.app/Contents/Developer/usr/bin/python3
T=workbench/tests/test_t229_worker_input_e2e.py
attempt() { local name=$1; shift; local i; for i in 1 2 3; do
  echo "start $name-$i $(date +%T) load $(sysctl -n vm.loadavg)" >> $E/runs.log
  "$@" --summary $E/$name-$i.json > $E/$name-$i.log 2>&1; local code=$?
  echo "end $name-$i exit=$code $(date +%T)" >> $E/runs.log
  pkill -f '^/private/tmp/t[0-9][0-9A-Za-z_-]+/state/hc/bin/herdr-core'
  grep -q 'daemon_start:' $E/$name-$i.log || return; done; }
for c in request-hangs record-fails request-fails; do attempt r7d-$c-claude $PY $T --cli claude --case $c; done
for c in request-hangs query-fails; do attempt r7d-$c-codex $PY $T --cli codex --case $c; done
attempt r7d-codex $PY $T --cli codex
echo "round7d done $(date +%T)" >> $E/runs.log
