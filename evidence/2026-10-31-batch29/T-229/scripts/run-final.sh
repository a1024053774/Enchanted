#!/bin/zsh
# T-229 final candidate: its own tests and the regression set touching worker input and Claude prompt hooks.
cd /Users/luckye/Documents/Code/a2a
E=/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence
export TMPDIR=/private/tmp ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/a2a-worktrees/hc-cache
PY=/Applications/Xcode.app/Contents/Developer/usr/bin/python3
T=workbench/tests
run() { local name=$1; shift; echo "start $name $(date +%T)" >> $E/runs.log; "$@" > $E/$name.log 2>&1; echo "end $name exit=$? $(date +%T)" >> $E/runs.log; }
run final-claude $PY $T/test_t229_worker_input_e2e.py --cli claude --summary $E/final-claude.json
run final-codex $PY $T/test_t229_worker_input_e2e.py --cli codex --summary $E/final-codex.json
run final-opencode python3 $T/test_t229_managed_input_e2e.py --cli opencode --summary $E/final-opencode.json
run final-agy python3 $T/test_t229_managed_input_e2e.py --cli agy --summary $E/final-agy.json
run final-t206 $PY $T/test_t206_input_on_send_e2e.py --summary $E/final-t206.json
run reg-t166-separate $PY $T/test_t166_busy_input_e2e.py --scenario separate --summary $E/reg-t166-separate.json
run reg-t166-absorbed $PY $T/test_t166_busy_input_e2e.py --scenario absorbed --summary $E/reg-t166-absorbed.json
run reg-t165-ordered $PY $T/test_t165_queued_stop_e2e.py --scenario ordered --summary $E/reg-t165-ordered.json
run reg-t157 $PY $T/test_t157_stop_input_e2e.py --summary $E/reg-t157.json
run reg-t207 $PY $T/test_t207_user_turn_delivery_e2e.py --summary $E/reg-t207.json
run reg-t187-opencode python3 $T/test_t187_managed_worker_e2e.py --cli opencode --summary $E/reg-t187-opencode.json
run reg-t216-issue-push $PY $T/test_t216_issue_push_e2e.py --gui --summary $E/reg-t216-issue-push.json
run reg-t216-provenance-claude $PY $T/test_t216_prompt_provenance_e2e.py --cli claude --case provenance --summary $E/reg-t216-provenance-claude.json
echo "final done $(date +%T)" >> $E/runs.log
