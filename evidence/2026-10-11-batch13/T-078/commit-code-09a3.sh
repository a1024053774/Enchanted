#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
sh evidence/2026-10-11-batch13/T-078/stop-local-probe-09a3.sh
git diff --check
git add -- workbench/README.md workbench/app/main.ts workbench/app/preload.ts workbench/app/renderer.tsx workbench/src/panes.ts workbench/src/daemon.ts workbench/src/gates/cli.ts workbench/tests/electron_driver.mjs workbench/tests/regenerate_t078_p1.py workbench/tests/run_t078_p1.py workbench/tests/test_t078_claude_epochs.ts workbench/tests/test_t078_pane_runtime.ts workbench/tests/test_t078_empty_declaration_entry.ts evidence/2026-10-11-batch13/T-078
git diff --cached --stat
git commit -m 'fix(T-078): bind empty declarations and block mismatched injections'
git status --short
