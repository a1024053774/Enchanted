#!/bin/zsh
# T-166 regression: T-157/T-165 scenarios and mutants, T-159/T-160/T-133 and build.
# 0 vendor model turns (local scripted Messages). Expected: PASS rows pass, mutants fail.
set -u
cd ${0:A:h:h:h:h} || exit 2
OUT=$(mktemp -d /private/tmp/t166-regression.XXXXXX); print -r -- "OUT=$OUT"
export PYTHONPYCACHEPREFIX=/private/tmp/a2a-merge-pycache
run() { local name=$1; shift; "$@" > "$OUT/$name.log" 2>&1; print -r -- "$name exit=$?" | tee -a "$OUT/exits.txt"; }
run build node workbench/app/build.mjs --slot t166-$(date -u +%Y%m%dT%H%M%SZ)
run t157-identity python3 -B workbench/tests/test_t157_turn_identity.py --summary $OUT/t157-identity.json
run t157-stop-input python3 -B workbench/tests/test_t157_stop_input_e2e.py --summary $OUT/t157-stop-input.json
run t157-stop-input-mutant python3 -B workbench/tests/test_t157_stop_input_e2e.py --mutant submit-never-active --summary $OUT/t157-stop-input-mutant.json
run t157-recover python3 -B workbench/tests/test_t157_stale_turn_e2e.py --scenario recover --summary $OUT/t157-recover.json
run t157-expired python3 -B workbench/tests/test_t157_stale_turn_e2e.py --scenario expired --summary $OUT/t157-expired.json
run t157-mutant-old-stop python3 -B workbench/tests/test_t157_stale_turn_e2e.py --mutant execute-old-stop --summary $OUT/t157-mutant-old-stop.json
run t165-ordered python3 -B workbench/tests/test_t165_queued_stop_e2e.py --summary $OUT/t165-ordered.json
run t165-unrelated python3 -B workbench/tests/test_t165_queued_stop_e2e.py --scenario unrelated-stop --summary $OUT/t165-unrelated.json
run t165-mutant python3 -B workbench/tests/test_t165_queued_stop_e2e.py --mutant drop-early-stop --summary $OUT/t165-mutant.json
run t159 python3 -B workbench/tests/test_t159_split_e2e.py --summary $OUT/t159.json
run t160-recovery python3 -B workbench/tests/test_t160_review_recovery_e2e.py --summary $OUT/t160-recovery.json
run t133-t107 python3 -B workbench/tests/test_t133_t107_terminal_controller_e2e.py --summary $OUT/t133-t107.json
run t161 python3 -B workbench/tests/test_t161_readonly_role_e2e.py --summary $OUT/t161.json
