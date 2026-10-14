#!/bin/bash
set -euo pipefail

# 主控 #102：只由执行主控在沙箱外运行本脚本。无 retry/skip/abort。
cd /Users/luckye/Documents/Code/a2a-wt-t077
python3 - <<'PY'
from pathlib import Path
import ast
import subprocess

root = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
expected_head = '7a1ecae84121b4dc43ddf79b595d6ff4917ab6c9'
expected_stop = '446f25c3de00925dfcc2f1c3f1375713676e166b'
expected_files = sorted([
    'acceptance/test_run_e2e.py',
    'workbench/src/contracts/a2aGates.ts',
    'workbench/src/gates/cli.ts',
    'workbench/src/gates/core.ts',
    'workbench/src/panes.ts',
])
def git(*args):
    return subprocess.check_output(['git', *args], cwd=root).decode().strip()
assert git('rev-parse', 'HEAD') == expected_head, 'HEAD changed'
assert git('rev-parse', 'main') == expected_head, 'main changed'
assert git('rev-parse', 'REBASE_HEAD') == expected_stop, 'Different rebase stop'
rebase_dir = Path(git('rev-parse', '--git-path', 'rebase-merge'))
assert (rebase_dir / 'head-name').read_text().strip() == 'refs/heads/exec/t077'
actual_files = sorted(p for p in git('diff', '--name-only', '--diff-filter=U', '-z').split('\0') if p)
assert actual_files == expected_files, {'expected': expected_files, 'actual': actual_files}
saved = root / 'evidence/2026-10-11-batch13/T-077/rebase-stop-01/resolved-final'
for name in expected_files:
    path = root / name
    assert path.read_bytes() == (saved / name).read_bytes(), f'Resolved file changed: {name}'
    assert not any(line.startswith(('<<<<<<<', '=======', '>>>>>>>'))
                   for line in path.read_text().splitlines()), f'Conflict marker in {name}'
    if path.suffix == '.ts':
        subprocess.run(['node', '--check', str(path)], check=True, cwd=root)
    else:
        ast.parse(path.read_text(), filename=str(path))
print('Expected first stop, five resolved files and syntax confirmed; continuing once.', flush=True)
PY

git add acceptance/test_run_e2e.py workbench/src/contracts/a2aGates.ts workbench/src/gates/cli.ts workbench/src/gates/core.ts workbench/src/panes.ts
GIT_EDITOR=true git rebase --continue
