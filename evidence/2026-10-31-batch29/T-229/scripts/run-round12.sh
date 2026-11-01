#!/bin/zsh
# T-229 round 12, after review 09: a successful UserPromptSubmit keeps the draft reserved for input typed after its Enter
# (draftHeld); once a user submission is recorded, later failures in its request mark the pane failed instead of blocking it.
# New cases draft-after-enter, after-record-fails, result-fails; new mutants draft-released-on-submit, record-then-block. Then
# the whole round 11 set again, since product code changed. The retry also reads daemon_start from the summary JSON.
# Retries only while an attempt fails at daemon_start (hc extracted per fixture), up to four; each attempt's fixture is noted in
# fixtures-r12.tsv and then deleted (status-only archiving; disk is short).
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
  echo "$name-$i\t$code\t$fx" >> $E/fixtures-r12.tsv
  [[ $fx == /private/tmp/t* && $fx != /private/tmp/t229-head* ]] && rm -rf $fx
  grep -q 'daemon_start:' $E/$name-$i.log $E/$name-$i.json 2>/dev/null || return; done; }
for cli in claude codex; do
  for c in draft-after-enter after-record-fails result-fails; do attempt r12-$c-$cli $PY $T --cli $cli --case $c; done
  attempt r12-mutant-draft-released-on-submit-$cli $PY $T --cli $cli --case draft-after-enter --mutant draft-released-on-submit
  attempt r12-mutant-record-then-block-a-$cli $PY $T --cli $cli --case after-record-fails --mutant record-then-block
  attempt r12-mutant-record-then-block-r-$cli $PY $T --cli $cli --case result-fails --mutant record-then-block
done
for cli in claude codex; do
  for m in no-claim attach-too; do attempt r12-mutant-$m-$cli $PY $T --cli $cli --mutant $m; done
  attempt r12-mutant-hook-error-passes-$cli $PY $T --cli $cli --case request-fails --mutant hook-error-passes
  attempt r12-mutant-no-observer-mark-$cli $PY $T --cli $cli --case query-fails --mutant no-observer-mark
  attempt r12-mutant-enter-starts-turn-$cli $PY $T --cli $cli --case request-fails --mutant enter-starts-turn
  attempt r12-mutant-late-handled-$cli $PY $T --cli $cli --case request-hangs --mutant late-handled
  attempt r12-mutant-no-deadline-$cli $PY $T --cli $cli --case request-hangs --mutant no-deadline
  for c in request-hangs record-fails query-fails diagnostic-fails request-fails; do attempt r12-$c-$cli $PY $T --cli $cli --case $c; done
  attempt r12-$cli $PY $T --cli $cli
done
attempt r12-t206 $PY $W/test_t206_input_on_send_e2e.py
attempt r12-reg-t167-receipt $PY $W/test_t167_codex_start_e2e.py --scenario receipt
attempt r12-reg-t167-dialog-open $PY $W/test_t167_codex_start_e2e.py --scenario dialog-open
attempt r12-reg-t157-stop-input $PY $W/test_t157_stop_input_e2e.py
attempt r12-reg-t157-stale-recover $PY $W/test_t157_stale_turn_e2e.py --scenario recover
attempt r12-reg-t157-stale-expired $PY $W/test_t157_stale_turn_e2e.py --scenario expired
attempt r12-reg-t165-ordered $PY $W/test_t165_queued_stop_e2e.py --scenario ordered
attempt r12-reg-t165-unrelated-stop $PY $W/test_t165_queued_stop_e2e.py --scenario unrelated-stop
attempt r12-reg-t166-separate $PY $W/test_t166_busy_input_e2e.py --scenario separate
attempt r12-reg-t166-absorbed $PY $W/test_t166_busy_input_e2e.py --scenario absorbed
attempt r12-reg-t133-t134 $PY $W/test_t133_t134_records_metrics_e2e.py
attempt r12-reg-t207 $PY $W/test_t207_user_turn_delivery_e2e.py
attempt r12-reg-t216-issue-push $PY $W/test_t216_issue_push_e2e.py --gui
attempt r12-reg-t216-provenance-claude $PY $W/test_t216_prompt_provenance_e2e.py --cli claude --case provenance
attempt r12-reg-t216-provenance-codex $PY $W/test_t216_prompt_provenance_e2e.py --cli codex --case provenance
attempt r12-opencode python3 $W/test_t229_managed_input_e2e.py --cli opencode
attempt r12-agy python3 $W/test_t229_managed_input_e2e.py --cli agy
mkdir -p $E/r12-unit/e; (cd workbench; for f in tests/test_t078_claude_signals.ts tests/test_t078_pane_runtime.ts tests/test_t108_questions.mjs; do n=${f:t:r}; perl -e 'alarm shift; exec @ARGV' 300 node $f $E/r12-unit/e/$n.json > $E/r12-unit/e/$n.log 2>&1; echo "$n exit=$?" >> $E/r12-unit/e/exits.txt; done; node $E/r5-unit/run-answer-lifecycle.mjs $PWD $E/r12-unit/e/answer-lifecycle.json > $E/r12-unit/e/answer-lifecycle.log 2>&1; echo "answer-lifecycle exit=$?" >> $E/r12-unit/e/exits.txt)
echo "round11 done $(date +%T)" >> $E/runs.log
