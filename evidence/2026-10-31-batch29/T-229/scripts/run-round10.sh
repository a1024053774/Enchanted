#!/bin/zsh
# T-229 round 10, after review 07: the snapshot is kept by the first unsettled Enter (??=), dropped by Stop and Esc, and settled by the
# final reply (ok drops it, failure restores it); the after-close drain reports failures through recordFailure. request-hangs also
# presses a second, empty Enter. New mutants: snapshot-overwritten; no-claim with its locator fixed. Retries as in round 9.
# only while it fails at daemon_start (hc extracted per fixture), up to four attempts; every attempt keeps its files.
cd /Users/luckye/Documents/Code/a2a
E=/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence
export TMPDIR=/private/tmp ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/a2a-worktrees/hc-cache
PY=/Applications/Xcode.app/Contents/Developer/usr/bin/python3
W=workbench/tests
T=$W/test_t229_worker_input_e2e.py
attempt() { local name=$1; shift; local i; for i in 1 2 3 4; do
  echo "start $name-$i $(date +%T) load $(sysctl -n vm.loadavg)" >> $E/runs.log
  "$@" --summary $E/$name-$i.json > $E/$name-$i.log 2>&1; local code=$?
  echo "end $name-$i exit=$code $(date +%T)" >> $E/runs.log
  pkill -f '^/private/tmp/t[0-9][0-9A-Za-z_-]+/state/hc/bin/herdr-core'
  grep -q 'daemon_start:' $E/$name-$i.log || return; done; }
for cli in claude codex; do
  attempt r10-mutant-snapshot-overwritten-$cli $PY $T --cli $cli --case request-hangs --mutant snapshot-overwritten
  attempt r10-mutant-no-claim-$cli $PY $T --cli $cli --mutant no-claim
  attempt r10-mutant-no-restore-$cli $PY $T --cli $cli --case request-fails --mutant no-restore
  attempt r10-mutant-late-handled-$cli $PY $T --cli $cli --case request-hangs --mutant late-handled
  attempt r10-mutant-no-deadline-$cli $PY $T --cli $cli --case request-hangs --mutant no-deadline
  for c in request-hangs record-fails query-fails diagnostic-fails request-fails; do attempt r10-$c-$cli $PY $T --cli $cli --case $c; done
  attempt r10-$cli $PY $T --cli $cli
done
attempt r10-t206 $PY $W/test_t206_input_on_send_e2e.py
attempt r10-reg-t166-separate $PY $W/test_t166_busy_input_e2e.py --scenario separate
attempt r10-reg-t165-ordered $PY $W/test_t165_queued_stop_e2e.py --scenario ordered
attempt r10-reg-t207 $PY $W/test_t207_user_turn_delivery_e2e.py
attempt r10-reg-t216-issue-push $PY $W/test_t216_issue_push_e2e.py --gui
attempt r10-reg-t216-provenance-claude $PY $W/test_t216_prompt_provenance_e2e.py --cli claude --case provenance
attempt r10-reg-t216-provenance-codex $PY $W/test_t216_prompt_provenance_e2e.py --cli codex --case provenance
attempt r10-opencode python3 $W/test_t229_managed_input_e2e.py --cli opencode
attempt r10-agy python3 $W/test_t229_managed_input_e2e.py --cli agy
mkdir -p $E/r10-unit; (cd workbench; for f in tests/test_t078_claude_signals.ts tests/test_t078_pane_runtime.ts tests/test_t108_questions.mjs; do n=${f:t:r}; perl -e 'alarm shift; exec @ARGV' 300 node $f $E/r10-unit/$n.json > $E/r10-unit/$n.log 2>&1; echo "$n exit=$?" >> $E/r10-unit/exits.txt; done; node $E/r5-unit/run-answer-lifecycle.mjs $PWD $E/r10-unit/answer-lifecycle.json > $E/r10-unit/answer-lifecycle.log 2>&1)
echo "round10 done $(date +%T)" >> $E/runs.log
