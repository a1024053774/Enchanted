#!/bin/zsh
# T-167: real Codex CLI + scripted Responses (94% used), real Electron/daemon/PTY. 0 vendor model turns.
# Expected: receipt PASS; dialog-open PASS; mutant fails display checks; base revision reproduces red.
# Regression: Claude worker paste submit (T-157 stop-input, T-165 ordered), T-127 Codex home, build.
set -u
cd ${0:A:h:h:h:h} || exit 2
OUT=$(mktemp -d /private/tmp/t167-run01.XXXXXX); print -r -- "OUT=$OUT"
export PYTHONPYCACHEPREFIX=/private/tmp/a2a-merge-pycache
run() { local name=$1; shift; "$@" > "$OUT/$name.log" 2>&1; print -r -- "$name exit=$?" | tee -a "$OUT/exits.txt"; }
T=workbench/tests/test_t167_codex_start_e2e.py
run build node workbench/app/build.mjs --slot t167-$(date -u +%Y%m%dT%H%M%SZ)
run receipt-1 python3 -B $T --summary $OUT/receipt-1.json
run receipt-2 python3 -B $T --summary $OUT/receipt-2.json
run dialog-open-1 python3 -B $T --scenario dialog-open --summary $OUT/dialog-open-1.json
run dialog-open-2 python3 -B $T --scenario dialog-open --summary $OUT/dialog-open-2.json
run mutant-no-start-check python3 -B $T --scenario dialog-open --mutant no-start-check --summary $OUT/mutant-no-start-check.json
run red-base python3 -B $T --revision a808c1137 --summary $OUT/red-base.json
run t157-stop-input python3 -B workbench/tests/test_t157_stop_input_e2e.py --summary $OUT/t157-stop-input.json
run t165-ordered python3 -B workbench/tests/test_t165_queued_stop_e2e.py --summary $OUT/t165-ordered.json
run t127 python3 -B workbench/tests/test_t127_codex_home_e2e.py --summary $OUT/t127.json
