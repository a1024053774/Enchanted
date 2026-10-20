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
test "$(git rev-parse HEAD)" = f3a4a5416213e912076437cfd8ce6f69a0e3091f
if ! git diff --cached --quiet; then
  print -u2 'Existing staged changes: preserve them and stop.'
  exit 1
fi
/usr/bin/python3 -B - <<'CHECK'
import json
from pathlib import Path
r=json.loads(Path('evidence/2026-10-20-batch18/T-108/review04-fix-local.summary.json').read_text(encoding='utf-8'))
assert r['status']=='PASS' and r['model_calls']==0 and r['vendor_calls']==0
assert r['parent']=='f3a4a5416213e912076437cfd8ce6f69a0e3091f'
assert r['checks']['questions']['cases']==429
assert r['checks']['known_bad']['cases']==429 and r['checks']['known_bad']['rejected']==9
assert set(r['checks']['questions']['positive_cases'])=={'permission_self_full','permission_self_matching_id','permission_self_sending'}
assert all(value['status']=='PASS' for value in r['checks'].values())
CHECK
git diff --check
git add --sparse -- \
  workbench/README.md workbench/src/questions.ts workbench/tests/t108_hook_failure_contracts.mjs \
  evidence/2026-10-20-batch18/T-108/RESULTS.md \
  evidence/2026-10-20-batch18/T-108/review04-fix-local.summary.json \
  evidence/2026-10-20-batch18/T-108/replay_review04_red.py \
  evidence/2026-10-20-batch18/T-108/project-map-review04-final.txt \
  evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-RECHECK-04.sh \
  evidence/2026-10-20-batch18/T-108/RUN-OUTSIDE-COMMIT-06.sh
git diff --cached --check
git commit -m 'fix(workbench): require complete question proof for permission exception'
git show --no-patch --format=full HEAD
