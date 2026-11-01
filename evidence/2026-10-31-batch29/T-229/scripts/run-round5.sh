#!/bin/zsh
# T-229 after review 03: the hook command blocks any submission the daemon did not confirm; noteSubmission marks the
# observer failed and rethrows. Mutants first, then every fault case, the main flow, and the regression set.
cd /Users/luckye/Documents/Code/a2a
E=/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence
export TMPDIR=/private/tmp ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/a2a-worktrees/hc-cache
PY=/Applications/Xcode.app/Contents/Developer/usr/bin/python3
W=workbench/tests
T=$W/test_t229_worker_input_e2e.py
run() { local name=$1; shift; echo "start $name $(date +%T)" >> $E/runs.log; "$@" > $E/$name.log 2>&1; echo "end $name exit=$? $(date +%T)" >> $E/runs.log; }
run r5-mutant-hook-error-passes-claude $PY $T --cli claude --case request-fails --mutant hook-error-passes --summary $E/r5-mutant-hook-error-passes-claude.json
run r5-mutant-hook-error-passes-codex $PY $T --cli codex --case request-fails --mutant hook-error-passes --summary $E/r5-mutant-hook-error-passes-codex.json
run r5-mutant-no-observer-mark-claude $PY $T --cli claude --case query-fails --mutant no-observer-mark --summary $E/r5-mutant-no-observer-mark-claude.json
run r5-mutant-no-claim-codex $PY $T --cli codex --mutant no-claim --summary $E/r5-mutant-no-claim-codex.json
run r5-mutant-attach-too-codex $PY $T --cli codex --mutant attach-too --summary $E/r5-mutant-attach-too-codex.json
for cli in claude codex; do
  for c in record-fails query-fails diagnostic-fails request-fails; do run r5-$c-$cli $PY $T --cli $cli --case $c --summary $E/r5-$c-$cli.json; done
  run r5-$cli $PY $T --cli $cli --summary $E/r5-$cli.json
done
run r5-opencode python3 $W/test_t229_managed_input_e2e.py --cli opencode --summary $E/r5-opencode.json
run r5-agy python3 $W/test_t229_managed_input_e2e.py --cli agy --summary $E/r5-agy.json
run r5-t206 $PY $W/test_t206_input_on_send_e2e.py --summary $E/r5-t206.json
run r5-reg-t166-separate $PY $W/test_t166_busy_input_e2e.py --scenario separate --summary $E/r5-reg-t166-separate.json
run r5-reg-t166-absorbed $PY $W/test_t166_busy_input_e2e.py --scenario absorbed --summary $E/r5-reg-t166-absorbed.json
run r5-reg-t165-ordered $PY $W/test_t165_queued_stop_e2e.py --scenario ordered --summary $E/r5-reg-t165-ordered.json
run r5-reg-t157 $PY $W/test_t157_stop_input_e2e.py --summary $E/r5-reg-t157.json
run r5-reg-t207 $PY $W/test_t207_user_turn_delivery_e2e.py --summary $E/r5-reg-t207.json
run r5-reg-t187-opencode python3 $W/test_t187_managed_worker_e2e.py --cli opencode --summary $E/r5-reg-t187-opencode.json
run r5-reg-t216-issue-push $PY $W/test_t216_issue_push_e2e.py --gui --summary $E/r5-reg-t216-issue-push.json
run r5-reg-t216-provenance-claude $PY $W/test_t216_prompt_provenance_e2e.py --cli claude --case provenance --summary $E/r5-reg-t216-provenance-claude.json
run r5-reg-t216-provenance-codex $PY $W/test_t216_prompt_provenance_e2e.py --cli codex --case provenance --summary $E/r5-reg-t216-provenance-codex.json
echo "round5 done $(date +%T)" >> $E/runs.log
