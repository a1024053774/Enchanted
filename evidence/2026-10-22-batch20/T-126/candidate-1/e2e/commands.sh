#!/bin/zsh
# T-126 candidate 1 end-to-end evidence (source entry): run from workbench/. At most three runs at a time.
E=../evidence/2026-10-22-batch20/T-126/candidate-1/e2e
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; print "$name exit=$?" >> $E/exits.txt; }
run green-01 tests/test_t126_terminal_socket_e2e.py
# red: the parent revision (terminal exports A2A_STATE) and three known-bad implementations.
run red-01-parent tests/test_t126_terminal_socket_e2e.py --revision 04d632694 &
run red-02-socket-accepts-all tests/test_t126_terminal_socket_e2e.py --mutant socket-accepts-all &
run red-03-state-exported tests/test_t126_terminal_socket_e2e.py --mutant state-exported &
wait
run red-04-refusal-unmarked tests/test_t126_terminal_socket_e2e.py --mutant refusal-unmarked &
# regressions: suites that start project terminals or workers.
run t121-green tests/test_t121_role_request_e2e.py &
run t122-green tests/test_t122_claude_worker_e2e.py &
wait
run t124-gui-green tests/test_t124_controller_e2e.py --gui &
run t124-restart-working tests/test_t124_controller_e2e.py --end restart-working &
run t124-restart-verified tests/test_t124_controller_e2e.py --end restart-verified &
wait
run t127-green tests/test_t127_codex_home_e2e.py
