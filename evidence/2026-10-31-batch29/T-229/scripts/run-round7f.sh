#!/bin/zsh
# T-229 round 7f: request-hangs on codex again at lower load; 7e hit the daemon start deadline three times (daemon up at 12 s).
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

attempt r7f-request-hangs-codex $PY $T --cli codex --case request-hangs

echo "round7f done $(date +%T)" >> $E/runs.log
