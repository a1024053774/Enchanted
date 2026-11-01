#!/bin/zsh
# T-229 round 9, after review 06 and two fixes found in round 8 (Claude returns the blocked text to its prompt, so the pane keeps the user draft; a blocked UserPromptSubmit drains the pane like any signal): a blocked UserPromptSubmit puts the pane back to its state before the window Enter
# (panes.submissionBlocked), and the hook's reply no longer waits for inbox feedback. Every fault case now checks the
# pane is idle after the block and, with a healthy observer, that a dispatch after it reaches the CLI. Each run is retried
# only while it fails at daemon_start (hc extracted per fixture), up to four attempts; every attempt keeps its files.
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
  grep -q 'daemon_start:' $E/$name-$i.log || return; done; }
for cli in claude codex; do
  attempt r9-mutant-no-restore-$cli $PY $T --cli $cli --case request-fails --mutant no-restore
  attempt r9-mutant-late-handled-$cli $PY $T --cli $cli --case request-hangs --mutant late-handled
  attempt r9-mutant-no-deadline-$cli $PY $T --cli $cli --case request-hangs --mutant no-deadline
  for c in request-hangs record-fails query-fails diagnostic-fails request-fails; do attempt r9-$c-$cli $PY $T --cli $cli --case $c; done
  attempt r9-$cli $PY $T --cli $cli
done
attempt r9-t206 $PY $W/test_t206_input_on_send_e2e.py
attempt r9-reg-t166-separate $PY $W/test_t166_busy_input_e2e.py --scenario separate
attempt r9-reg-t165-ordered $PY $W/test_t165_queued_stop_e2e.py --scenario ordered
attempt r9-reg-t207 $PY $W/test_t207_user_turn_delivery_e2e.py
attempt r9-reg-t216-issue-push $PY $W/test_t216_issue_push_e2e.py --gui
attempt r9-reg-t216-provenance-claude $PY $W/test_t216_prompt_provenance_e2e.py --cli claude --case provenance
attempt r9-reg-t216-provenance-codex $PY $W/test_t216_prompt_provenance_e2e.py --cli codex --case provenance
echo "round9 done $(date +%T)" >> $E/runs.log
