#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
test "$(git rev-parse HEAD)" = 0f754a6dfd555568cb377affbbe52655a13d3d4d
test ! -e evidence/2026-10-11-batch13/T-078/regression-02-source-freeze.json
git diff --check
git add -- workbench/tests/t078_worker_inbox_scenario.py workbench/tests/test_t078_worker_receipt_lookup.py evidence/2026-10-11-batch13/T-078 .project-map/inbox/20261014T172035Z-worker:t078-regression02-report-001.md
git diff --cached --stat
git commit -m 'test(T-078): resolve worker receipts by persisted launch ownership'
python3 -B -c 'import json,pathlib,subprocess; b=pathlib.Path("evidence/2026-10-11-batch13/T-078"); revision=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(); (b/"regression-02-source-freeze.json").open("x",encoding="utf-8").write(json.dumps({"revision":revision,"prior_revision":"0f754a6dfd555568cb377affbbe52655a13d3d4d","real_model_turns":0},indent=2))'
git status --short
