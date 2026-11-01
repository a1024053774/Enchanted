#!/bin/zsh
# T-230 regression set, run from the main checkout with the T-230 working-tree changes.
cd /Users/luckye/Documents/Code/a2a
E=/Users/luckye/Documents/Code/a2a-worktrees/T-230-evidence
export TMPDIR=/private/tmp ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/a2a-worktrees/hc-cache
PY=/Applications/Xcode.app/Contents/Developer/usr/bin/python3
run() { local name=$1; shift; echo "start $name $(date +%T)" >> $E/regression-runs.log; "$@" > $E/$name.log 2>&1; echo "end $name exit=$? $(date +%T)" >> $E/regression-runs.log; }
run green-boundaries python3 workbench/tests/test_t212_hc_boundaries_e2e.py --output $E/green-boundaries
run mutant-leak-xdg python3 workbench/tests/test_t212_hc_boundaries_e2e.py --mutant leak-xdg --output $E/mutant-leak-xdg
run t212-core-crash python3 workbench/tests/test_t212_shell_hc_e2e.py --core-crash --output $E/t212-core-crash
run t212-electron $PY workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --mismatched-screen --output $E/t212-electron
run t228-holder python3 workbench/tests/test_t228_core_identity_e2e.py --case holder --output $E/t228-holder
run t228-foreign python3 workbench/tests/test_t228_core_identity_e2e.py --case foreign --output $E/t228-foreign
run t216-provenance-claude $PY workbench/tests/test_t216_prompt_provenance_e2e.py --cli claude --case provenance --summary $E/t216-provenance-claude.json
run t216-provenance-codex $PY workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case provenance --summary $E/t216-provenance-codex.json
run t216-history-codex $PY workbench/tests/test_t216_prompt_provenance_e2e.py --cli codex --case history --summary $E/t216-history-codex.json
run t216-issue-push $PY workbench/tests/test_t216_issue_push_e2e.py --gui --summary $E/t216-issue-push.json
run t216-r2-online $PY workbench/tests/test_t216_round2_e2e.py --case routing-online --summary $E/t216-r2-online.json
run t216-codex-local $PY workbench/tests/test_t216_real_cli_delivery_e2e.py --cli codex --summary $E/t216-codex-local.json
run t216-recover $PY workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case recover-unknown --summary $E/t216-recover.json
run t216-unknown-gui $PY workbench/tests/test_t216_hc_delivery_e2e.py --cli opencode --case unknown --gui --summary $E/t216-unknown-gui.json
echo "all done $(date +%T)" >> $E/regression-runs.log
