#!/bin/bash
# Controller reruns of T-212's acceptance tests, independent of the worker's runs.
C=/Users/luckye/Documents/Code/a2a-worktrees/T-212-controller
cd /Users/luckye/Documents/Code/a2a-worktrees/T-212
export TMPDIR=/private/tmp
run() { name=$1; shift; echo "== $name: $*" >> $C/runs.log; "$@" > $C/$name.log 2>&1; echo "== $name exit $?" >> $C/runs.log; }
run screen python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --output $C/screen-01
run screen-noreset python3 workbench/tests/test_t212_shell_hc_e2e.py --electron-screen --mutant no-reset --output $C/screen-noreset-01
run forget-token python3 workbench/tests/test_t212_shell_hc_e2e.py --mutant forget-token --output $C/forget-token-01
run boundaries python3 workbench/tests/test_t212_hc_boundaries_e2e.py --output $C/boundaries-01
run boundaries-leakxdg python3 workbench/tests/test_t212_hc_boundaries_e2e.py --mutant leak-xdg --output $C/boundaries-leakxdg-01
run t104 python3 workbench/tests/test_t104_shell_e2e.py --archive $C/t104-01-fixture --summary $C/t104-01.json
run regressions python3 $C/run-regressions-ctl.py t121 t107 t118 t126 t133 t133codex t142
echo "== all done" >> $C/runs.log
