#!/bin/zsh
# T-229 round 6b: rerun of round 6 after the internal disk filled (ENOSPC) from r6-request-hangs-codex on, plus
# query-fails on claude, which hit the daemon start deadline.
cd /Users/luckye/Documents/Code/a2a
E=/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence
export TMPDIR=/private/tmp ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/a2a-worktrees/hc-cache
PY=/Applications/Xcode.app/Contents/Developer/usr/bin/python3
W=workbench/tests
T=$W/test_t229_worker_input_e2e.py
run() { local name=$1; shift; echo "start $name $(date +%T)" >> $E/runs.log; "$@" > $E/$name.log 2>&1; echo "end $name exit=$? $(date +%T)" >> $E/runs.log; pkill -f '^/private/tmp/t[0-9][0-9A-Za-z_-]+/state/hc/bin/herdr-core'; }

run r6b-query-fails-claude $PY $T --cli claude --case query-fails --summary $E/r6b-query-fails-claude.json
for cli in codex; do
  for c in request-hangs record-fails query-fails diagnostic-fails request-fails; do run r6b-$c-$cli $PY $T --cli $cli --case $c --summary $E/r6b-$c-$cli.json; done
  run r6b-$cli $PY $T --cli $cli --summary $E/r6b-$cli.json
done
run r6b-t206 $PY $W/test_t206_input_on_send_e2e.py --summary $E/r6b-t206.json
run r6b-reg-t166-separate $PY $W/test_t166_busy_input_e2e.py --scenario separate --summary $E/r6b-reg-t166-separate.json
run r6b-reg-t165-ordered $PY $W/test_t165_queued_stop_e2e.py --scenario ordered --summary $E/r6b-reg-t165-ordered.json
run r6b-reg-t207 $PY $W/test_t207_user_turn_delivery_e2e.py --summary $E/r6b-reg-t207.json
run r6b-reg-t216-issue-push $PY $W/test_t216_issue_push_e2e.py --gui --summary $E/r6b-reg-t216-issue-push.json
run r6b-reg-t216-provenance-claude $PY $W/test_t216_prompt_provenance_e2e.py --cli claude --case provenance --summary $E/r6b-reg-t216-provenance-claude.json
run r6b-reg-t216-provenance-codex $PY $W/test_t216_prompt_provenance_e2e.py --cli codex --case provenance --summary $E/r6b-reg-t216-provenance-codex.json
echo "round6b done $(date +%T)" >> $E/runs.log
