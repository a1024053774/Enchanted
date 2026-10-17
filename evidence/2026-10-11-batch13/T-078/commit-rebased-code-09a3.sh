#!/bin/sh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t078
git diff --check
git add -- workbench/tests/regenerate_t078_p1.py workbench/tests/t078_native_receiver.c workbench/tests/t078_terminal_receiver.py workbench/tests/test_t078_pane_runtime.ts evidence/2026-10-11-batch13/T-078 .project-map/inbox/20261014T142134Z-worker:t078-09a3r-report-001.md .project-map/inbox/20261014T143421Z-worker:t078-09a3r-report-001.md
git diff --cached --stat
git commit -m 'test(T-078): preserve rebase evidence and align fixture metadata'
git rev-parse HEAD > evidence/2026-10-11-batch13/T-078/rebased-source-freeze.txt
python3 -B -c 'import json,pathlib; b=pathlib.Path("evidence/2026-10-11-batch13/T-078"); revision=(b/"rebased-source-freeze.txt").read_text().strip(); (b/"rebased-source-freeze.json").open("x",encoding="utf-8").write(json.dumps({"revision":revision,"base_main":"87e954a2f4059d471e3e240872b565217e29b0b5","real_model_turns":0},indent=2))'
git status --short
