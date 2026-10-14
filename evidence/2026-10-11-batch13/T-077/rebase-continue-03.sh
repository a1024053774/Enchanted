#!/bin/bash
set -euo pipefail

# 主控 #103：只由执行主控在沙箱外运行；继续一次，后续冲突保留现场。
cd /Users/luckye/Documents/Code/a2a-wt-t077
python3 - <<'PY'
from pathlib import Path
import ast
import subprocess

root = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
expected_head = '0b194a55b260d5ab342e2cd50b9b49674ee25405'
expected_stop = 'f6bc3ed99c87e6ea20eaf144b6a073266a5decb2'
expected_main = '7a1ecae84121b4dc43ddf79b595d6ff4917ab6c9'
expected_files = sorted(['workbench/src/panes.ts', 'workbench/tests/run_pane_lifecycle.py',
                         'workbench/tests/run_t076_real.py'])
def git(*args):
    return subprocess.check_output(['git', *args], cwd=root)
assert git('rev-parse', 'HEAD').decode().strip() == expected_head, 'HEAD changed'
assert git('rev-parse', 'REBASE_HEAD').decode().strip() == expected_stop, 'Different rebase stop'
assert git('rev-parse', 'main').decode().strip() == expected_main, 'main changed'
rebase_dir = Path(git('rev-parse', '--git-path', 'rebase-merge').decode().strip())
assert (rebase_dir / 'head-name').read_text().strip() == 'refs/heads/exec/t077'
actual_files = sorted(filter(None, git('diff', '--name-only', '--diff-filter=U', '-z').decode().split('\0')))
assert actual_files == expected_files, {'expected': expected_files, 'actual': actual_files}
saved = root / 'evidence/2026-10-11-batch13/T-077/rebase-stop-03/resolved'
for name in expected_files:
    path = root / name
    content = path.read_bytes()
    assert content == (saved / name).read_bytes() == git('show', 'HEAD:' + name), f'Resolution changed: {name}'
    assert not any(line.startswith(('<<<<<<<', '=======', '>>>>>>>'))
                   for line in content.decode().splitlines()), f'Conflict marker in {name}'
    if name.endswith('.py'):
        assert content == git('show', 'main:' + name), f'T-076 script changed: {name}'
        ast.parse(content.decode(), filename=name)
    else:
        subprocess.run(['node', '--check', name], cwd=root, check=True)
print('Expected fourth commit stop and three unchanged HEAD-side files confirmed.', flush=True)
PY

git add workbench/src/panes.ts workbench/tests/run_pane_lifecycle.py workbench/tests/run_t076_real.py
GIT_EDITOR=true git rebase --continue
