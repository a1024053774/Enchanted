#!/bin/zsh
# T-229 round 7e: request-hangs on codex after the no-turn check was limited to Claude (a Codex pane's turn comes from the
# window Enter and its rollout, T-234), and query-fails on codex, which hit the daemon start deadline three times in 7d.
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
attempt r7e-mutant-late-handled-codex $PY $T --cli codex --case request-hangs --mutant late-handled
attempt r7e-request-hangs-codex $PY $T --cli codex --case request-hangs
attempt r7e-query-fails-codex $PY $T --cli codex --case query-fails
echo "round7e done $(date +%T)" >> $E/runs.log
