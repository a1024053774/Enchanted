#!/bin/zsh
# T-127 round 05: the runtime binds the reviewer's session by the review worktree (narrow mutant);
# the gate must refuse at the result, and must not once its folder check is removed.
cd "$(dirname $0)/../../../workbench"
E=../evidence/2026-10-22-batch20/T-127
T=tests/test_t127_codex_home_e2e.py
r() { local name=$1; shift; python3 -B $T --summary $E/$name.json "$@" >/dev/null 2>&1; echo "$name $?"; }
r e2e-case-session-folder-differs-runtime-mutant-02 --reviewer-case session-folder-differs --mutant reviewer-folder-unbound &
r e2e-case-session-folder-differs-runtime-gate-mutant-02 --reviewer-case session-folder-differs --mutant reviewer-folder-unbound gate-folder-unchecked &
wait
