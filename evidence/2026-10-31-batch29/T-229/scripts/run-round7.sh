#!/bin/zsh
# T-229 after review 05: the daemon refuses a UserPromptSubmit request past its submit_deadline (1 s before the hook gives
# up), so a blocked submission is never recorded or started as a turn. request-hangs and its two mutants, the other fault
# cases and the main flow on both CLIs, T-206, and the regressions on the hook path.
cd /Users/luckye/Documents/Code/a2a
E=/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence
export TMPDIR=/private/tmp ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/a2a-worktrees/hc-cache
PY=/Applications/Xcode.app/Contents/Developer/usr/bin/python3
W=workbench/tests
T=$W/test_t229_worker_input_e2e.py
run() { local name=$1; shift; echo "start $name $(date +%T)" >> $E/runs.log; "$@" > $E/$name.log 2>&1; echo "end $name exit=$? $(date +%T)" >> $E/runs.log; pkill -f '^/private/tmp/t[0-9][0-9A-Za-z_-]+/state/hc/bin/herdr-core'; }
for cli in claude codex; do
  run r7-mutant-late-handled-$cli $PY $T --cli $cli --case request-hangs --mutant late-handled --summary $E/r7-mutant-late-handled-$cli.json
  run r7-mutant-no-deadline-$cli $PY $T --cli $cli --case request-hangs --mutant no-deadline --summary $E/r7-mutant-no-deadline-$cli.json
  for c in request-hangs record-fails query-fails diagnostic-fails request-fails; do run r7-$c-$cli $PY $T --cli $cli --case $c --summary $E/r7-$c-$cli.json; done
  run r7-$cli $PY $T --cli $cli --summary $E/r7-$cli.json
done
run r7-t206 $PY $W/test_t206_input_on_send_e2e.py --summary $E/r7-t206.json
run r7-reg-t166-separate $PY $W/test_t166_busy_input_e2e.py --scenario separate --summary $E/r7-reg-t166-separate.json
run r7-reg-t165-ordered $PY $W/test_t165_queued_stop_e2e.py --scenario ordered --summary $E/r7-reg-t165-ordered.json
run r7-reg-t207 $PY $W/test_t207_user_turn_delivery_e2e.py --summary $E/r7-reg-t207.json
run r7-reg-t216-issue-push $PY $W/test_t216_issue_push_e2e.py --gui --summary $E/r7-reg-t216-issue-push.json
run r7-reg-t216-provenance-claude $PY $W/test_t216_prompt_provenance_e2e.py --cli claude --case provenance --summary $E/r7-reg-t216-provenance-claude.json
run r7-reg-t216-provenance-codex $PY $W/test_t216_prompt_provenance_e2e.py --cli codex --case provenance --summary $E/r7-reg-t216-provenance-codex.json
echo "round7 done $(date +%T)" >> $E/runs.log
