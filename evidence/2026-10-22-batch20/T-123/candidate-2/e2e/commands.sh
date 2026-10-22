#!/bin/zsh
# T-123 candidate 2 end-to-end evidence: run from workbench/. Each group runs its commands in parallel, at most three at a time.
E=../evidence/2026-10-22-batch20/T-123/candidate-2/e2e
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; print "$name exit=$?" >> $E/exits.txt; }
# green: the T-123 scenario on the candidate.
run green-01 tests/test_t123_project_identity_e2e.py
# red: the same scenario on the parent revision (global task ids), and known-bad implementations.
# The parent has no migration, so it and global-task-id run the same-name scenario alone (--scenario same-name).
run red-01-parent tests/test_t123_project_identity_e2e.py --revision 4116c8b44 --scenario same-name &
run red-02-global-task-id tests/test_t123_project_identity_e2e.py --mutant global-task-id --scenario same-name &
run red-03-ambiguous-name-picks-first tests/test_t123_project_identity_e2e.py --mutant ambiguous-name-picks-first &
wait
run red-05-migration-skips-events tests/test_t123_project_identity_e2e.py --mutant migration-skips-events &
run red-06-gone-only-first-restart tests/test_t123_project_identity_e2e.py --mutant gone-only-first-restart &
run red-07-full-id-ignores-project tests/test_t123_project_identity_e2e.py --mutant full-id-ignores-project &
wait
run red-08-migration-ignores-drafts tests/test_t123_project_identity_e2e.py --mutant migration-ignores-drafts &
run red-09-cli-refuses-project tests/test_t123_project_identity_e2e.py --mutant cli-refuses-project &
run red-10-snapshot-raw-name tests/test_t123_project_identity_e2e.py --mutant snapshot-raw-name &
wait
# regressions: suites whose expectations changed with the task id, and T-128's restart variants.
run t121-green tests/test_t121_role_request_e2e.py &
run t121-red-foreign-key-unchecked tests/test_t121_role_request_e2e.py --mutant foreign-key-unchecked &
run t122-green tests/test_t122_claude_worker_e2e.py &
wait
run t124-gui-green tests/test_t124_controller_e2e.py --gui &
run t124-restart-working tests/test_t124_controller_e2e.py --end restart-working &
run t124-restart-verified tests/test_t124_controller_e2e.py --end restart-verified &
wait
run t127-green tests/test_t127_codex_home_e2e.py
