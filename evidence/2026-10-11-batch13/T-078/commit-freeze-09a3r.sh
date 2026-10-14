#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
test "$(git rev-parse HEAD)" = 567d7748c40ca511f170997d7fe216063fb7c4f1
test ! -e evidence/2026-10-11-batch13/T-078/source-freeze-09a3r.json
test -z "$(git diff -- workbench)"
git diff --check
git add -- evidence/2026-10-11-batch13/T-078/rebased-outside-regression-02-09a3 evidence/2026-10-11-batch13/T-078/regression-02-source-freeze.json evidence/2026-10-11-batch13/T-078/regression02-readback-09a3r.json evidence/2026-10-11-batch13/T-078/read-regression02-for-09a3r.py evidence/2026-10-11-batch13/T-078/commit-freeze-09a3r.sh
git diff --cached --stat
git commit -m 'docs(T-078): freeze passing rebased regression for 09A-3R'
python3 -B -c 'import json,pathlib,subprocess; b=pathlib.Path("evidence/2026-10-11-batch13/T-078"); revision=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(); (b/"source-freeze-09a3r.json").open("x",encoding="utf-8").write(json.dumps({"revision":revision,"regression_revision":"567d7748c40ca511f170997d7fe216063fb7c4f1","real_model_turns":0},indent=2)+"\n")'
git status --short
