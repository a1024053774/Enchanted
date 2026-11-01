#!/bin/zsh
# T-229 after review 04: the hook command stops waiting for the daemon 8 s into a UserPromptSubmit and blocks; the
# request-hangs case and its mutant, every fault case, the main flow, and the regressions on the hook path.
cd /Users/luckye/Documents/Code/a2a
E=/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence
export TMPDIR=/private/tmp ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/a2a-worktrees/hc-cache
PY=/Applications/Xcode.app/Contents/Developer/usr/bin/python3
W=workbench/tests
T=$W/test_t229_worker_input_e2e.py
run() { local name=$1; shift; echo "start $name $(date +%T)" >> $E/runs.log; "$@" > $E/$name.log 2>&1; echo "end $name exit=$? $(date +%T)" >> $E/runs.log; pkill -f '^/private/tmp/t[0-9][0-9A-Za-z_-]+/state/hc/bin/herdr-core'; }
for cli in claude codex; do run r6-mutant-no-deadline-$cli $PY $T --cli $cli --case request-hangs --mutant no-deadline --summary $E/r6-mutant-no-deadline-$cli.json; done
for cli in claude codex; do
  for c in request-hangs record-fails query-fails diagnostic-fails request-fails; do run r6-$c-$cli $PY $T --cli $cli --case $c --summary $E/r6-$c-$cli.json; done
  run r6-$cli $PY $T --cli $cli --summary $E/r6-$cli.json
done
run r6-t206 $PY $W/test_t206_input_on_send_e2e.py --summary $E/r6-t206.json
run r6-reg-t166-separate $PY $W/test_t166_busy_input_e2e.py --scenario separate --summary $E/r6-reg-t166-separate.json
run r6-reg-t165-ordered $PY $W/test_t165_queued_stop_e2e.py --scenario ordered --summary $E/r6-reg-t165-ordered.json
run r6-reg-t207 $PY $W/test_t207_user_turn_delivery_e2e.py --summary $E/r6-reg-t207.json
run r6-reg-t216-issue-push $PY $W/test_t216_issue_push_e2e.py --gui --summary $E/r6-reg-t216-issue-push.json
run r6-reg-t216-provenance-claude $PY $W/test_t216_prompt_provenance_e2e.py --cli claude --case provenance --summary $E/r6-reg-t216-provenance-claude.json
run r6-reg-t216-provenance-codex $PY $W/test_t216_prompt_provenance_e2e.py --cli codex --case provenance --summary $E/r6-reg-t216-provenance-codex.json
echo "round6 done $(date +%T)" >> $E/runs.log
