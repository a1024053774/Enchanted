#!/bin/zsh
# T-229 round 11, option 1 after review 08: on Claude Code and Codex the window Enter only reserves the draft; the turn starts when
# the daemon handles the UserPromptSubmit. The beforeSubmit snapshot is gone, so its mutants (snapshot-overwritten, no-restore) are
# dropped and enter-starts-turn replaces them. Adds the related regressions (T-167, T-157, T-165, T-166, T-133/T-134, T-207).
# Retries only while an attempt fails at daemon_start (hc extracted per fixture), up to four; each attempt's fixture is noted in
# fixtures-r11.tsv and then deleted (status-only archiving; disk is short).
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
  echo "$name-$i\t$code\t$fx" >> $E/fixtures-r11.tsv
  [[ $fx == /private/tmp/t* && $fx != /private/tmp/t229-head* ]] && rm -rf $fx
  grep -q 'daemon_start:' $E/$name-$i.log || return; done; }
for cli in claude codex; do
  for m in no-claim attach-too; do attempt r11-mutant-$m-$cli $PY $T --cli $cli --mutant $m; done
  attempt r11-mutant-hook-error-passes-$cli $PY $T --cli $cli --case request-fails --mutant hook-error-passes
  attempt r11-mutant-no-observer-mark-$cli $PY $T --cli $cli --case query-fails --mutant no-observer-mark
  attempt r11-mutant-enter-starts-turn-$cli $PY $T --cli $cli --case request-fails --mutant enter-starts-turn
  attempt r11-mutant-late-handled-$cli $PY $T --cli $cli --case request-hangs --mutant late-handled
  attempt r11-mutant-no-deadline-$cli $PY $T --cli $cli --case request-hangs --mutant no-deadline
  for c in request-hangs record-fails query-fails diagnostic-fails request-fails; do attempt r11-$c-$cli $PY $T --cli $cli --case $c; done
  attempt r11-$cli $PY $T --cli $cli
done
attempt r11-t206 $PY $W/test_t206_input_on_send_e2e.py
attempt r11-reg-t167-receipt $PY $W/test_t167_codex_start_e2e.py --scenario receipt
attempt r11-reg-t167-dialog-open $PY $W/test_t167_codex_start_e2e.py --scenario dialog-open
attempt r11-reg-t157-stop-input $PY $W/test_t157_stop_input_e2e.py
attempt r11-reg-t157-stale-recover $PY $W/test_t157_stale_turn_e2e.py --scenario recover
attempt r11-reg-t157-stale-expired $PY $W/test_t157_stale_turn_e2e.py --scenario expired
attempt r11-reg-t165-ordered $PY $W/test_t165_queued_stop_e2e.py --scenario ordered
attempt r11-reg-t165-unrelated-stop $PY $W/test_t165_queued_stop_e2e.py --scenario unrelated-stop
attempt r11-reg-t166-separate $PY $W/test_t166_busy_input_e2e.py --scenario separate
attempt r11-reg-t166-absorbed $PY $W/test_t166_busy_input_e2e.py --scenario absorbed
attempt r11-reg-t133-t134 $PY $W/test_t133_t134_records_metrics_e2e.py
attempt r11-reg-t207 $PY $W/test_t207_user_turn_delivery_e2e.py
attempt r11-reg-t216-issue-push $PY $W/test_t216_issue_push_e2e.py --gui
attempt r11-reg-t216-provenance-claude $PY $W/test_t216_prompt_provenance_e2e.py --cli claude --case provenance
attempt r11-reg-t216-provenance-codex $PY $W/test_t216_prompt_provenance_e2e.py --cli codex --case provenance
attempt r11-opencode python3 $W/test_t229_managed_input_e2e.py --cli opencode
attempt r11-agy python3 $W/test_t229_managed_input_e2e.py --cli agy
mkdir -p $E/r11-unit/e; (cd workbench; for f in tests/test_t078_claude_signals.ts tests/test_t078_pane_runtime.ts tests/test_t108_questions.mjs; do n=${f:t:r}; perl -e 'alarm shift; exec @ARGV' 300 node $f $E/r11-unit/e/$n.json > $E/r11-unit/e/$n.log 2>&1; echo "$n exit=$?" >> $E/r11-unit/e/exits.txt; done; node $E/r5-unit/run-answer-lifecycle.mjs $PWD $E/r11-unit/e/answer-lifecycle.json > $E/r11-unit/e/answer-lifecycle.log 2>&1; echo "answer-lifecycle exit=$?" >> $E/r11-unit/e/exits.txt)
echo "round11 done $(date +%T)" >> $E/runs.log
