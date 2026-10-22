#!/bin/zsh
# T-127 negatives round 03: the reviewer resumes the worker's session, recorded or hidden.
cd "$(dirname $0)/../../../workbench"
E=../evidence/2026-10-22-batch20/T-127
T=tests/test_t127_codex_home_e2e.py
for c in resume-worker-in-argv resume-worker-hidden; do
  python3 -B $T --summary $E/e2e-case-$c-01.json --reviewer-case $c >/dev/null 2>&1; echo "case $c $?"
done
