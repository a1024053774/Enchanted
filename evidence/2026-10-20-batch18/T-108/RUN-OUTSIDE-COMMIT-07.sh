#!/bin/zsh
set -eu
cd /Users/luckye/Documents/Code/a2a-wt-t108
export LC_ALL=C
unset GIT_DIR GIT_WORK_TREE
# Exact public worker identity; the existing hook validates its launch record.
# No manual trailers, Git config writes, hook changes, submit or push.
export A2A_PROJECT=a2a
export A2A_TASK=T-108
export A2A_ATTEMPT=a1
export A2A_SESSION=d07960e3-56d6-4b80-9f31-cc10605b69c8
export A2A_ROLE=worker
export A2A_LAUNCH=launch-eb74ca1d5e8e4cfc877a2819bc0afe76
export A2A_LAUNCHES=/Users/luckye/Documents/Code/a2a/records/launches.jsonl
export CODEX_THREAD_ID=01a157cc-f9c2-70d3-849e-42883fe1e09c
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a/scripts/git-hooks
test "$(git branch --show-current)" = exec/t108
test "$(git rev-parse HEAD)" = f533fd16e608cb73f666246700206fe28e21503c
if ! git diff --cached --quiet; then
  print -u2 'Existing staged changes: preserve them and stop.'
  exit 1
fi
/usr/bin/python3 -B - <<'CHECK'
import json
from pathlib import Path
r=json.loads(Path('evidence/2026-10-20-batch18/T-108/review05-fix-local.summary.json').read_text(encoding='utf-8'))
assert r['status']=='PASS' and r['model_calls']==0 and r['vendor_calls']==0
assert r['parent']=='f533fd16e608cb73f666246700206fe28e21503c'
assert r['checks']['questions']['hook_cases']==429
assert r['checks']['questions']['lifecycle_cases']==14
assert r['checks']['known_bad']['exit_code']==1 and r['checks']['known_bad']['driver_exit_code']==1
assert set(r['checks']['known_bad']['focused'])=={'early','early_stop','recorder_refused'}
assert r['checks']['driver']['cases']==9
assert all(value['status']=='PASS' for value in r['checks'].values())
CHECK
git diff --check
git add --sparse -- \
  workbench/README.md \
  workbench/app/main.ts \
  workbench/src/panes.ts \
  workbench/src/questions.ts \
  workbench/src/daemon.ts \
  workbench/tests/test_t108_questions.mjs \
  workbench/tests/t108_answer_lifecycle_contracts.mjs \
  workbench/tests/t108_answer_receipt.mjs \
  workbench/tests/test_t108_driver.mjs \
  workbench/tests/t108_questions_driver.mjs \
  workbench/tests/run_t108_native_e2e.py \
  evidence/2026-10-20-batch18/T-108/RESULTS.md \
  evidence/2026-10-20-batch18/T-108/review05-fix-local.summary.json \
  evidence/2026-10-20-batch18/T-108/project-map-review05-final.txt \
  evidence/2026-10-20-batch18/T-108/replay_review03_red.py \
  evidence/2026-10-20-batch18/T-108/replay_review04_red.py \
  evidence/2026-10-20-batch18/T-108/replay_review05_red.py \
  evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-RECHECK-05.sh \
  evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-07.sh
git diff --cached --check
git commit -m 'fix(workbench): complete early native answers without poisoning input queues'
git show --no-patch --format=full HEAD
