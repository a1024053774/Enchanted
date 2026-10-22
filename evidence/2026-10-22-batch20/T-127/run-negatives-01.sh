#!/bin/zsh
# T-127 negatives: parent revision, known-bad mutants, reviewer refusals and their gate mutants.
cd "$(dirname $0)/../../../workbench"
E=../evidence/2026-10-22-batch20/T-127
python3 -B tests/test_t127_codex_home_e2e.py --summary $E/e2e-red-head-01.json --revision 64f9c24d2 >/dev/null 2>&1; echo "red-head $?"
for m in restricted-unanswered untrusted-config-missing project-trusted scan-any-folder; do
  python3 -B tests/test_t127_codex_home_e2e.py --summary $E/e2e-mutant-$m-01.json --mutant $m >/dev/null 2>&1; echo "mutant $m $?"
done
for c in trust-other-folder session-folder-differs; do
  python3 -B tests/test_t127_codex_home_e2e.py --summary $E/e2e-case-$c-01.json --reviewer-case $c >/dev/null 2>&1; echo "case $c $?"
done
python3 -B tests/test_t127_codex_home_e2e.py --summary $E/e2e-case-trust-other-folder-gate-mutant-01.json --reviewer-case trust-other-folder --mutant gate-trust-unchecked >/dev/null 2>&1; echo "case+gate trust $?"
python3 -B tests/test_t127_codex_home_e2e.py --summary $E/e2e-case-session-folder-differs-gate-mutant-01.json --reviewer-case session-folder-differs --mutant gate-folder-unchecked >/dev/null 2>&1; echo "case+gate folder $?"
