#!/bin/zsh
# T-168: green x2, two mutants, T-161 read-only focus, T-139/T-143 views, T-091 IPC, build.
# 0 model requests (controlled PTY). Expected: PASS rows pass, mutants fail.
set -u
cd ${0:A:h:h:h:h} || exit 2
OUT=$(mktemp -d /private/tmp/t168-regression.XXXXXX); print -r -- "OUT=$OUT"
export PYTHONPYCACHEPREFIX=/private/tmp/a2a-merge-pycache
run() { local name=$1; shift; "$@" > "$OUT/$name.log" 2>&1; print -r -- "$name exit=$?" | tee -a "$OUT/exits.txt"; }
run build node workbench/app/build.mjs --slot t168-$(date -u +%Y%m%dT%H%M%SZ)
run t168-green-2 python3 -B workbench/tests/test_t168_readonly_size_e2e.py --summary $OUT/t168-green-2.json
run t168-green-3 python3 -B workbench/tests/test_t168_readonly_size_e2e.py --summary $OUT/t168-green-3.json
run t168-mutant-fits-view python3 -B workbench/tests/test_t168_readonly_size_e2e.py --mutant readonly-fits-view --summary $OUT/t168-mutant-fits-view.json
run t168-mutant-resizes-pty python3 -B workbench/tests/test_t168_readonly_size_e2e.py --mutant readonly-resizes-pty --summary $OUT/t168-mutant-resizes-pty.json
run t161 python3 -B workbench/tests/test_t161_readonly_role_e2e.py --summary $OUT/t161.json
run t139-t143 python3 -B workbench/tests/test_t139_t143_views_perf_e2e.py --summary $OUT/t139-t143.json
run t143-focus node workbench/tests/test_t143_retained_focus.mjs $OUT/t143-focus.json
run t139-layout node --experimental-vm-modules workbench/tests/test_t139_layout_store.mjs $OUT/t139-layout.json
run t139-selection node --experimental-vm-modules workbench/tests/test_t139_selection.mjs $OUT/t139-selection.json
run t091 node --experimental-vm-modules workbench/tests/test_t091_pane_ipc.mjs --summary $OUT/t091.json
