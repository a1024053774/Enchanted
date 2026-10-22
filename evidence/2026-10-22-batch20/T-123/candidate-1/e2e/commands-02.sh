#!/bin/zsh
# T-123 candidate 1, second pass: the T-123 green and reds after the test reads gate refusals as failed request_result
# (see superseded-02-rejection-record-form/README.txt). Run from workbench/; the regression suites in commands.sh stand.
E=../evidence/2026-10-22-batch20/T-123/candidate-1/e2e
run() { local name=$1; shift; python3 "$@" --summary $E/$name.json > $E/$name.log 2>&1; print "$name exit=$?" >> $E/exits.txt; }
run green-01 tests/test_t123_project_identity_e2e.py &
run red-01-parent tests/test_t123_project_identity_e2e.py --revision 4116c8b44 --scenario same-name &
run red-02-global-task-id tests/test_t123_project_identity_e2e.py --mutant global-task-id --scenario same-name &
wait
run red-03-ambiguous-name-picks-first tests/test_t123_project_identity_e2e.py --mutant ambiguous-name-picks-first &
run red-05-migration-skips-events tests/test_t123_project_identity_e2e.py --mutant migration-skips-events &
run red-06-gone-only-first-restart tests/test_t123_project_identity_e2e.py --mutant gone-only-first-restart &
wait
run red-07-full-id-ignores-project tests/test_t123_project_identity_e2e.py --mutant full-id-ignores-project
