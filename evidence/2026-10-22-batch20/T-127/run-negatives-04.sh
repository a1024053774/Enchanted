#!/bin/zsh
# T-127 round 04: reviewers running elsewhere (unbound, then with a runtime that binds them anyway,
# then with the gate check removed too), and scan timings with many earlier sessions.
cd "$(dirname $0)/../../../workbench"
E=../evidence/2026-10-22-batch20/T-127
T=tests/test_t127_codex_home_e2e.py
r() { local name=$1; shift; python3 -B $T --summary $E/$name.json "$@" >/dev/null 2>&1; echo "$name $?"; }
{
  r e2e-case-session-folder-differs-03 --reviewer-case session-folder-differs
  r e2e-case-session-folder-differs-runtime-mutant-01 --reviewer-case session-folder-differs --mutant reviewer-folder-unbound
  r e2e-case-session-folder-differs-runtime-gate-mutant-01 --reviewer-case session-folder-differs --mutant reviewer-folder-unbound gate-folder-unchecked
  r e2e-case-resume-worker-hidden-02 --reviewer-case resume-worker-hidden
} &
{
  r e2e-case-resume-worker-hidden-runtime-mutant-01 --reviewer-case resume-worker-hidden --mutant reviewer-folder-unbound
  r e2e-timing-fix-20000-01 --old-sessions 20000
  r e2e-timing-whole-home-400-01 --old-sessions 400 --mutant scan-whole-home
  r e2e-timing-whole-home-20000-01 --old-sessions 20000 --mutant scan-whole-home
} &
wait
