#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
test "$(git rev-parse HEAD)" = 6f0cfdb2c042ac27251dd979b56c792e4874f720
test ! -e evidence/2026-10-11-batch13/T-078/source-freeze-09a3r2.json
test -z "$(git diff -- workbench/src workbench/app workbench/hooks)"
git diff --check
git add -- workbench/tests/electron_driver.mjs workbench/tests/p1_window_receipts.py workbench/tests/p1_simulated_actions.py workbench/tests/run_t078_p1.py workbench/tests/regenerate_t078_p1.py workbench/tests/test_t078_window_binding.mjs workbench/tests/test_t078_simulated_draft.py evidence/2026-10-11-batch13/T-078
git diff --cached --stat
git commit -m 'test(T-078): simulate approved draft clearing and empty declaration'
python3 -B -c 'import json,pathlib,subprocess; b=pathlib.Path("evidence/2026-10-11-batch13/T-078"); revision=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(); (b/"source-freeze-09a3r2.json").open("x",encoding="utf-8").write(json.dumps({"revision":revision,"prior_revision":"6f0cfdb2c042ac27251dd979b56c792e4874f720","real_model_turns":0,"automation_source":"test-simulated-user"},indent=2)+"\n")'
git status --short
