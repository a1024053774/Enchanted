#!/bin/bash
# 只完成主控 #20 已开始的 merge；保留 main 已暂存的文件，不 abort/reset。
set -euo pipefail
cd /Users/luckye/Documents/Code/a2a-wt-t104
[[ "$(git branch --show-current)" == exec/t104 ]]
[[ "$(git rev-parse HEAD)" == c6dd956f0* ]]
[[ "$(git rev-parse MERGE_HEAD)" == ea206484b8bcdae19fa4edd91b7553af22ff757b ]]
python3 - <<'PY'
from pathlib import Path
import subprocess
expected={'workbench/src/daemon.ts','workbench/src/gates/cli.ts'}
unmerged=set(subprocess.check_output(['git','diff','--name-only','--diff-filter=U'],text=True).splitlines())
assert unmerged==expected, f'冲突集合与主控回传不符：{unmerged}'
unstaged=set(subprocess.check_output(['git','diff','--name-only'],text=True).splitlines())
assert unstaged<=expected, f'合并之外还有未暂存改动，保留现场：{unstaged-expected}'
for name in expected:
 text=Path(name).read_text(encoding='utf-8')
 assert not any(line.startswith(('<<<<<<<','=======','>>>>>>>')) for line in text.splitlines()), name
PY
node --check workbench/src/daemon.ts
node --check workbench/src/gates/cli.ts
export A2A_PROJECT=a2a A2A_TASK=T-104 A2A_ATTEMPT=a1 A2A_ROLE=worker
export A2A_SESSION=8fbb58f9-18ea-43e8-a0e3-facbc7edcaad
export A2A_LAUNCH=launch-04f00c94021d4e9c9618c151af840bde
export A2A_LAUNCHES=/Users/luckye/Documents/Code/a2a/records/launches.jsonl
export CODEX_THREAD_ID=01a1527f-e702-7c20-9ee3-6758a25c911c
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath
export GIT_CONFIG_VALUE_0=/Users/luckye/Documents/Code/a2a/scripts/git-hooks
test -x "$GIT_CONFIG_VALUE_0/prepare-commit-msg"
git add --sparse -- workbench/src/daemon.ts workbench/src/gates/cli.ts
git diff --cached --check
git commit -m 'merge main into exec/t104: preserve picker and shell commands'
git log -1 --format=fuller
git status --short --branch
