#!/bin/zsh
# T-126 candidate 2 end-to-end evidence (source entry): run from workbench/. Candidate 2 changes only the daemon's
# start-failure path, so the T-126 scenario, its parent red and the suites that start terminals run again.
E=../evidence/2026-10-22-batch20/T-126/candidate-2/e2e
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; print "$name exit=$?" >> $E/exits.txt; }
run green-01 tests/test_t126_terminal_socket_e2e.py &
run red-01-parent tests/test_t126_terminal_socket_e2e.py --revision 04d632694 &
run t121-green tests/test_t121_role_request_e2e.py &
wait
run t124-restart-verified tests/test_t124_controller_e2e.py --end restart-verified &
run t122-green tests/test_t122_claude_worker_e2e.py &
wait
