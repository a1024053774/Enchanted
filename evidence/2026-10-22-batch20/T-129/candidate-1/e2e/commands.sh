#!/bin/zsh
# T-129 candidate 1 end-to-end evidence: run from workbench/. Real daemon, real Claude Code in node-pty, a scripted
# Messages endpoint (no provider calls). At most three runs at a time.
E=../evidence/2026-10-22-batch20/T-129/candidate-1/e2e
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; print "$name exit=$?" >> $E/exits.txt; }
t=tests/test_t122_claude_worker_e2e.py
# green: a reviewer result the protocol refuses, and one the gate refuses; the normal T-122 flow.
run green-malformed $t --review-result malformed &
run green-rejected $t --review-result rejected &
run t122-green $t &
wait
# red: the parent revision (400db6611) in both scenarios, and the fix removed at each failure path.
run red-parent-malformed $t --review-result malformed --revision 400db6611 &
run red-parent-rejected $t --review-result rejected --revision 400db6611 &
run red-protocol-failure-unbound $t --review-result malformed --mutant protocol-failure-unbound &
wait
run red-rejection-unbound $t --review-result rejected --mutant rejection-unbound &
# regressions: Codex reviewers go through the same calls.
run t124-restart-verified tests/test_t124_controller_e2e.py --end restart-verified &
run t127-green tests/test_t127_codex_home_e2e.py &
wait
