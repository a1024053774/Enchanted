#!/bin/zsh
# T-229 round 7b: request-hangs (claude) and its late-handled mutant after the no-turn check was narrowed to the pane's own
# turn (T-234 out of scope), and every round-7 run that hit the daemon start deadline (load ~9).
cd /Users/luckye/Documents/Code/a2a
E=/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence
export TMPDIR=/private/tmp ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/a2a-worktrees/hc-cache
PY=/Applications/Xcode.app/Contents/Developer/usr/bin/python3
W=workbench/tests
T=$W/test_t229_worker_input_e2e.py
run() { local name=$1; shift; echo "start $name $(date +%T) load $(sysctl -n vm.loadavg)" >> $E/runs.log; "$@" > $E/$name.log 2>&1; echo "end $name exit=$? $(date +%T)" >> $E/runs.log; pkill -f '^/private/tmp/t[0-9][0-9A-Za-z_-]+/state/hc/bin/herdr-core'; }
run r7b-mutant-late-handled-claude $PY $T --cli claude --case request-hangs --mutant late-handled --summary $E/r7b-mutant-late-handled-claude.json
for c in request-hangs record-fails query-fails request-fails; do run r7b-$c-claude $PY $T --cli claude --case $c --summary $E/r7b-$c-claude.json; done
for c in request-hangs query-fails; do run r7b-$c-codex $PY $T --cli codex --case $c --summary $E/r7b-$c-codex.json; done
run r7b-codex $PY $T --cli codex --summary $E/r7b-codex.json
run r7b-reg-t166-separate $PY $W/test_t166_busy_input_e2e.py --scenario separate --summary $E/r7b-reg-t166-separate.json
run r7b-reg-t216-issue-push $PY $W/test_t216_issue_push_e2e.py --gui --summary $E/r7b-reg-t216-issue-push.json
echo "round7b done $(date +%T)" >> $E/runs.log
