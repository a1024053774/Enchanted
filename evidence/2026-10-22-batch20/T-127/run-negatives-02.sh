#!/bin/zsh
# T-127 negatives round 02: the session-folder case now starts its reviewer; the two launch mutants are
# judged by behaviour first (the argv check moved last); a fresh green on the final test file.
cd "$(dirname $0)/../../../workbench"
E=../evidence/2026-10-22-batch20/T-127
T=tests/test_t127_codex_home_e2e.py
python3 -B $T --summary $E/e2e-case-session-folder-differs-02.json --reviewer-case session-folder-differs >/dev/null 2>&1; echo "case session-folder-differs $?"
python3 -B $T --summary $E/e2e-case-session-folder-differs-gate-mutant-02.json --reviewer-case session-folder-differs --mutant gate-folder-unchecked >/dev/null 2>&1; echo "case+gate folder $?"
for m in untrusted-config-missing project-trusted; do
  python3 -B $T --summary $E/e2e-mutant-$m-02.json --mutant $m >/dev/null 2>&1; echo "mutant $m $?"
done
python3 -B $T --summary $E/e2e-green-04.json >/dev/null 2>&1; echo "green $?"
