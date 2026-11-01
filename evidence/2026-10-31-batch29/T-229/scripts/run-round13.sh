#!/bin/zsh
# T-229 round 13, after review 10: a successful UserPromptSubmit keeps the draft reserved when any input was admitted after
# its Enter (inputGeneration vs submitGeneration), an IME composition with nothing committed yet included. New case
# composition-after-enter; draft-released-on-submit also runs against it. Then the whole set again, unit tests included.
# Retries only while an attempt fails at daemon_start (hc extracted per fixture), up to four; each attempt's fixture is noted in
# fixtures-r13.tsv and then deleted (status-only archiving; disk is short).
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
  local fx=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1])).get("fixture") or "")' $E/$name-$i.json 2>/dev/null)
  echo "$name-$i\t$code\t$fx" >> $E/fixtures-r13.tsv
  [[ $fx == /private/tmp/t* && $fx != /private/tmp/t229-head* ]] && rm -rf $fx
  grep -q 'daemon_start:' $E/$name-$i.log $E/$name-$i.json 2>/dev/null || return; done; }
for cli in claude codex; do
  attempt r13-composition-after-enter-$cli $PY $T --cli $cli --case composition-after-enter
  attempt r13-mutant-draft-released-on-submit-c-$cli $PY $T --cli $cli --case composition-after-enter --mutant draft-released-on-submit
  for c in draft-after-enter after-record-fails result-fails; do attempt r13-$c-$cli $PY $T --cli $cli --case $c; done
  attempt r13-mutant-draft-released-on-submit-$cli $PY $T --cli $cli --case draft-after-enter --mutant draft-released-on-submit
  attempt r13-mutant-record-then-block-a-$cli $PY $T --cli $cli --case after-record-fails --mutant record-then-block
  attempt r13-mutant-record-then-block-r-$cli $PY $T --cli $cli --case result-fails --mutant record-then-block
done
for cli in claude codex; do
  for m in no-claim attach-too; do attempt r13-mutant-$m-$cli $PY $T --cli $cli --mutant $m; done
  attempt r13-mutant-hook-error-passes-$cli $PY $T --cli $cli --case request-fails --mutant hook-error-passes
  attempt r13-mutant-no-observer-mark-$cli $PY $T --cli $cli --case query-fails --mutant no-observer-mark
  attempt r13-mutant-enter-starts-turn-$cli $PY $T --cli $cli --case request-fails --mutant enter-starts-turn
  attempt r13-mutant-late-handled-$cli $PY $T --cli $cli --case request-hangs --mutant late-handled
  attempt r13-mutant-no-deadline-$cli $PY $T --cli $cli --case request-hangs --mutant no-deadline
  for c in request-hangs record-fails query-fails diagnostic-fails request-fails; do attempt r13-$c-$cli $PY $T --cli $cli --case $c; done
  attempt r13-$cli $PY $T --cli $cli
done
attempt r13-t206 $PY $W/test_t206_input_on_send_e2e.py
attempt r13-reg-t167-receipt $PY $W/test_t167_codex_start_e2e.py --scenario receipt
attempt r13-reg-t167-dialog-open $PY $W/test_t167_codex_start_e2e.py --scenario dialog-open
attempt r13-reg-t157-stop-input $PY $W/test_t157_stop_input_e2e.py
attempt r13-reg-t157-stale-recover $PY $W/test_t157_stale_turn_e2e.py --scenario recover
attempt r13-reg-t157-stale-expired $PY $W/test_t157_stale_turn_e2e.py --scenario expired
attempt r13-reg-t165-ordered $PY $W/test_t165_queued_stop_e2e.py --scenario ordered
attempt r13-reg-t165-unrelated-stop $PY $W/test_t165_queued_stop_e2e.py --scenario unrelated-stop
attempt r13-reg-t166-separate $PY $W/test_t166_busy_input_e2e.py --scenario separate
attempt r13-reg-t166-absorbed $PY $W/test_t166_busy_input_e2e.py --scenario absorbed
attempt r13-reg-t133-t134 $PY $W/test_t133_t134_records_metrics_e2e.py
attempt r13-reg-t207 $PY $W/test_t207_user_turn_delivery_e2e.py
attempt r13-reg-t216-issue-push $PY $W/test_t216_issue_push_e2e.py --gui
attempt r13-reg-t216-provenance-claude $PY $W/test_t216_prompt_provenance_e2e.py --cli claude --case provenance
attempt r13-reg-t216-provenance-codex $PY $W/test_t216_prompt_provenance_e2e.py --cli codex --case provenance
attempt r13-opencode python3 $W/test_t229_managed_input_e2e.py --cli opencode
attempt r13-agy python3 $W/test_t229_managed_input_e2e.py --cli agy
mkdir -p $E/r13-unit/e; (cd workbench; for f in tests/test_t078_claude_signals.ts tests/test_t078_pane_runtime.ts tests/test_t108_questions.mjs; do n=${f:t:r}; perl -e 'alarm shift; exec @ARGV' 300 node $f $E/r13-unit/e/$n.json > $E/r13-unit/e/$n.log 2>&1; echo "$n exit=$?" >> $E/r13-unit/e/exits.txt; done; node $E/r5-unit/run-answer-lifecycle.mjs $PWD $E/r13-unit/e/answer-lifecycle.json > $E/r13-unit/e/answer-lifecycle.log 2>&1; echo "answer-lifecycle exit=$?" >> $E/r13-unit/e/exits.txt)
mkdir -p $E/r13-unit/c; for t in t157_turn_identity t166_queued_input; do python3 -B $W/test_$t.py --summary $E/r13-unit/c/$t.json > $E/r13-unit/c/$t.log 2>&1; echo "$t exit=$?" >> $E/r13-unit/c/exits.txt; done
mkdir -p /private/tmp/t229-u165; node $W/test_t165_queued_stop.ts $PWD /private/tmp/t229-u165 > $E/r13-unit/c/t165.log 2>&1; echo "t165 exit=$?" >> $E/r13-unit/c/exits.txt
rm -rf /private/tmp/t108-* /private/tmp/t78-* /private/tmp/t157-identity-* /private/tmp/t166-queued-* /private/tmp/t229-u165
echo "round13 done $(date +%T)" >> $E/runs.log
