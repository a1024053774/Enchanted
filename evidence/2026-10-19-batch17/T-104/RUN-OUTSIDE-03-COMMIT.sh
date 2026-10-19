#!/bin/bash
# 主控在沙箱外提交第一段候选；尾注只由现有钩子生成，不 push。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t104
[[ "$(git branch --show-current)" == exec/t104 ]]
[[ "$(git rev-parse HEAD)" == cc18d93dbbcf2ee641dc92befe68e5b0609b4807 ]] || {
  echo '起点已改变，请先核对历史；保留现场。' >&2
  exit 1
}
git diff --cached --quiet || { echo '暂存区已有内容，保留现场。' >&2; exit 1; }
python3 - <<'PY'
from pathlib import Path
for path in Path('evidence/2026-10-19-batch17/T-104').rglob('*'):
    if path.is_dir():
        continue
    assert path.is_file() and not path.is_symlink(), f'不提交链接或特殊文件：{path}'
    assert path.suffix in ['.md','.json','.py','.sh','.txt'], f'不提交原始大块证据：{path}'
    assert path.stat().st_size < 512*1024, f'证据过大：{path}'
PY
export A2A_PROJECT=a2a A2A_TASK=T-104 A2A_ATTEMPT=a1 A2A_ROLE=worker
export A2A_SESSION=8fbb58f9-18ea-43e8-a0e3-facbc7edcaad
export A2A_LAUNCH=launch-04f00c94021d4e9c9618c151af840bde
export A2A_LAUNCHES=/Users/luckye/Documents/Code/a2a/records/launches.jsonl
export CODEX_THREAD_ID=01a1527f-e702-7c20-9ee3-6758a25c911c
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a/scripts/git-hooks
test -x "$GIT_CONFIG_VALUE_0/prepare-commit-msg"
git add --sparse -- \
  workbench/src/panes.ts workbench/src/daemon.ts workbench/src/store.ts workbench/src/gates/cli.ts \
  workbench/tests/test_t104_shell_e2e.py workbench/tests/test_pane_dispatch_state.ts \
  workbench/tests/test_conflict_panes.ts workbench/README.md evidence/2026-10-19-batch17/T-104/
git diff --cached --check
git commit -m 'feat(T-104): add project zsh panes to the daemon'
git log -1 --format=fuller
git status --short --branch
