#!/bin/bash
# 主控 #30：先提交测试同步修复，再由主控连续两次运行后台套件。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t104
[[ "$(git branch --show-current)" == exec/t104 ]]
[[ "$(git rev-parse HEAD)" == 45c127b5af03bfdc50802579bda50b88a98dc2c7 ]]
git diff --cached --quiet || { echo '暂存区已有内容，保留现场。' >&2; exit 1; }
python3 - <<'PY'
import ast,json,subprocess
from pathlib import Path
folder=Path('evidence/2026-10-19-batch17/T-104');path='workbench/tests/test_t104_shell_e2e.py'
changed=set(subprocess.check_output(['git','diff','--name-only'],text=True).splitlines())
assert changed=={path},f'测试同步之外有受控文件改动，保留现场：{changed}'
report=json.loads((folder/'readiness-check-30.json').read_text(encoding='utf-8'))
assert report['status']=='PASS' and report['candidate_diff']==subprocess.check_output(['git','diff','--',path],text=True)
source=Path(path).read_text(encoding='utf-8');ast.parse(source)
exact="assert [line for line in lines if line.startswith('A2A_')] == ['A2A_PROJECT=t104-alpha']"
assert source.count(exact)==1 and subprocess.check_output(['git','show','HEAD:'+path],text=True).count(exact)==1
PY
export A2A_PROJECT=a2a A2A_TASK=T-104 A2A_ATTEMPT=a1 A2A_ROLE=worker
export A2A_SESSION=8fbb58f9-18ea-43e8-a0e3-facbc7edcaad
export A2A_LAUNCH=launch-04f00c94021d4e9c9618c151af840bde
export A2A_LAUNCHES=/Users/luckye/Documents/Code/a2a/records/launches.jsonl
export CODEX_THREAD_ID=01a1527f-e702-7c20-9ee3-6758a25c911c
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a/scripts/git-hooks
test -x "$GIT_CONFIG_VALUE_0/prepare-commit-msg"
git add --sparse -- workbench/tests/test_t104_shell_e2e.py \
  evidence/2026-10-19-batch17/T-104/PROBE-REPLAY-28.py \
  evidence/2026-10-19-batch17/T-104/REPLAY-DIAGNOSIS-28.md \
  evidence/2026-10-19-batch17/T-104/replay-diagnosis-28.json \
  evidence/2026-10-19-batch17/T-104/replay-diagnosis-static-28.json \
  evidence/2026-10-19-batch17/T-104/CHECK-READINESS-30.py \
  evidence/2026-10-19-batch17/T-104/readiness-check-30.json \
  evidence/2026-10-19-batch17/T-104/READBACK-SYNC-30.md \
  evidence/2026-10-19-batch17/T-104/readiness-static-30.json \
  evidence/2026-10-19-batch17/T-104/RUN-OUTSIDE-10-COMMIT-SYNC.sh
git diff --cached --check
git commit -m 'test(T-104): wait for shell environment completion marker'
git log -1 --format=fuller
git status --short --branch
