#!/bin/zsh
# T-130 candidate 1 end-to-end evidence: run from workbench/. Real daemon and Claude Code with a scripted Messages
# endpoint whose replies name a model other than the requested one. At most three runs at a time.
E=../evidence/2026-10-22-batch20/T-130/candidate-1/e2e
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; print "$name exit=$?" >> $E/exits.txt; }
t=tests/test_t122_claude_worker_e2e.py
run t122-green $t &
run red-parent $t --revision 04354734b &
run t127-green tests/test_t127_codex_home_e2e.py &
wait
# the T-129 scenarios share this test file, which T-130 changed.
run t129-malformed $t --review-result malformed &
run t129-rejected $t --review-result rejected &
wait
