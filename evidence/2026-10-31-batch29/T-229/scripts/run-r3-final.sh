#!/bin/zsh
# T-229 candidate after review 01: its own tests and the regression set touching worker input and Claude prompt hooks.
cd /Users/luckye/Documents/Code/a2a
E=/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence
export TMPDIR=/private/tmp ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/a2a-worktrees/hc-cache
PY=/Applications/Xcode.app/Contents/Developer/usr/bin/python3
T=workbench/tests
run() { local name=$1; shift; echo "start $name $(date +%T)" >> $E/runs.log; "$@" > $E/$name.log 2>&1; echo "end $name exit=$? $(date +%T)" >> $E/runs.log; }
run r3-final-opencode python3 $T/test_t229_managed_input_e2e.py --cli opencode --summary $E/r3-final-opencode.json
run r3-final-agy python3 $T/test_t229_managed_input_e2e.py --cli agy --summary $E/r3-final-agy.json
run r3-final-t206 $PY $T/test_t206_input_on_send_e2e.py --summary $E/r3-final-t206.json
run r3-reg-t166-separate $PY $T/test_t166_busy_input_e2e.py --scenario separate --summary $E/r3-reg-t166-separate.json
run r3-reg-t166-absorbed $PY $T/test_t166_busy_input_e2e.py --scenario absorbed --summary $E/r3-reg-t166-absorbed.json
run r3-reg-t165-ordered $PY $T/test_t165_queued_stop_e2e.py --scenario ordered --summary $E/r3-reg-t165-ordered.json
run r3-reg-t157 $PY $T/test_t157_stop_input_e2e.py --summary $E/r3-reg-t157.json
run r3-reg-t207 $PY $T/test_t207_user_turn_delivery_e2e.py --summary $E/r3-reg-t207.json
run r3-reg-t187-opencode python3 $T/test_t187_managed_worker_e2e.py --cli opencode --summary $E/r3-reg-t187-opencode.json
run r3-reg-t216-issue-push $PY $T/test_t216_issue_push_e2e.py --gui --summary $E/r3-reg-t216-issue-push.json
run r3-reg-t216-provenance-claude $PY $T/test_t216_prompt_provenance_e2e.py --cli claude --case provenance --summary $E/r3-reg-t216-provenance-claude.json
echo "r3-final done $(date +%T)" >> $E/runs.log
