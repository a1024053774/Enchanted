#!/bin/bash
set -euo pipefail

# 主控 #104：沙箱外继续固定停点一次；后续冲突保留现场。
cd /Users/luckye/Documents/Code/a2a-wt-t077
python3 - <<'PY'
from pathlib import Path
import subprocess

root = Path('/Users/luckye/Documents/Code/a2a-wt-t077')
expected_head = '9f9bca77bbb9901702cc28ecf6834505ce4dc2d4'
expected_stop = '2e2291acfee0e9b4f20c7ff952a5484c4262e20b'
expected_files = ['workbench/src/panes.ts']
def git(*args):
    return subprocess.check_output(['git', *args], cwd=root)
assert git('rev-parse', 'HEAD').decode().strip() == expected_head, 'HEAD changed'
assert git('rev-parse', 'REBASE_HEAD').decode().strip() == expected_stop, 'Different rebase stop'
rebase_dir = Path(git('rev-parse', '--git-path', 'rebase-merge').decode().strip())
assert (rebase_dir / 'head-name').read_text().strip() == 'refs/heads/exec/t077'
actual_files = sorted(filter(None, git('diff', '--name-only', '--diff-filter=U', '-z').decode().split('\0')))
assert actual_files == expected_files, {'expected': expected_files, 'actual': actual_files}
name = expected_files[0]
content = (root / name).read_bytes()
saved = root / 'evidence/2026-10-11-batch13/T-077/rebase-stop-05/resolved' / name
assert content == saved.read_bytes() == git('show', 'HEAD:' + name), 'Resolution changed'
assert not any(line.startswith(('<<<<<<<', '=======', '>>>>>>>')) for line in content.decode().splitlines())
subprocess.run(['node', '--check', name], cwd=root, check=True)
print('Expected fifth-commit stop and resolved pane file confirmed.', flush=True)
PY

git add workbench/src/panes.ts
GIT_EDITOR=true git rebase --continue
