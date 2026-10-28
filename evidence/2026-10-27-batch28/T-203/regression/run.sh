#!/bin/zsh
# T-203 regression: the old tests updated to submit through review_submit. Run from workbench/tests.
E=../../evidence/2026-10-27-batch28/T-203/regression
for spec in "t187-managed-agy test_t187_managed_worker_e2e.py --cli agy" "t187-managed-opencode test_t187_managed_worker_e2e.py --cli opencode" \
            "t187-osc test_t187_osc_cli_e2e.py" "t160 test_t160_review_recovery_e2e.py" "t140 test_t140_extra_dirs_e2e.py" \
            "t141 test_t141_loosened_limits_e2e.py" "t179 test_t179_receipt_summary_e2e.py" "t122 test_t122_claude_worker_e2e.py" \
            "t187-guard test_t187_git_metadata_guard_e2e.py"; do
  parts=(${=spec}); name=$parts[1]; shift parts
  echo "== $name $(date +%T)"; python3 $parts --summary $E/$name-1.json 2>&1 | tail -3
done
