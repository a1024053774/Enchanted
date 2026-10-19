#!/bin/bash
# 只提交已通过 06 的候选；现有 hook 加尾注，不 push。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t104
SUMMARY=${1:?传入本票 ui-编号-summary.json}
[[ "$(git branch --show-current)" == exec/t104 ]]
[[ "$(git rev-parse HEAD)" == edd469f6b9d2d34bedb3a9479159fbb917dc43d5 ]]
git diff --cached --quiet || { echo '暂存区已有内容，保留现场。' >&2; exit 1; }
python3 - "$SUMMARY" <<'PY'
import json,subprocess,sys
from pathlib import Path
source=Path.cwd();summary=Path(sys.argv[1]).resolve(strict=True)
assert summary.parent==source/'evidence/2026-10-19-batch17/T-104'
report=json.loads(summary.read_text(encoding='utf-8'))
assert report['status']=='PASS' and all(c['exit']==0 and c['status']=='PASS' for c in report['checks'])
assert report['revision']==subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
accepted=Path(report['archive'])/'ui'
ui=json.loads((accepted/'run.json').read_text(encoding='utf-8'))
assert ui['status']=='PASS' and ui['cleanup_complete'] and len(ui['screenshots'])>=5
for name in ui['source_files']:
 assert (source/name).read_bytes()==(accepted/'source-snapshot'/name).read_bytes(), '已通过的候选输入改变：'+name
for path in summary.parent.rglob('*'):
 if path.is_dir():continue
 assert not path.is_symlink() and path.suffix in ('.md','.json','.py','.sh','.txt'),f'不提交原始大块证据：{path}'
 assert path.stat().st_size<512*1024,f'证据过大：{path}'
PY
export A2A_PROJECT=a2a A2A_TASK=T-104 A2A_ATTEMPT=a1 A2A_ROLE=worker
export A2A_SESSION=8fbb58f9-18ea-43e8-a0e3-facbc7edcaad
export A2A_LAUNCH=launch-04f00c94021d4e9c9618c151af840bde
export A2A_LAUNCHES=/Users/luckye/Documents/Code/a2a/records/launches.jsonl
export CODEX_THREAD_ID=01a1527f-e702-7c20-9ee3-6758a25c911c
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a/scripts/git-hooks
test -x "$GIT_CONFIG_VALUE_0/prepare-commit-msg"
git add --sparse -- workbench/app/main.ts workbench/app/preload.ts workbench/app/renderer.tsx \
  workbench/app/style.css workbench/src/daemon.ts workbench/README.md \
  workbench/tests/test_t104_shell_e2e.py workbench/tests/test_t091_pane_ipc.mjs \
  workbench/tests/test_electron_e2e.py workbench/tests/run_t104_shell_ui.py \
  workbench/tests/t104_shell_driver.mjs evidence/2026-10-19-batch17/T-104/
git diff --cached --check
git commit -m 'feat(T-104): create project terminals from the workbench'
git log -1 --format=fuller
git status --short --branch
