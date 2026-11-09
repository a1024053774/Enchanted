#!/usr/bin/env python3
"""只核对新 E2E 夹具的 Git 状态；不启动 Electron，不作为用户路径通过证据。"""
import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
source = ROOT / 'workbench/tests/test_t249_git_graph_e2e.py'
tree = ast.parse(source.read_text(encoding='utf-8'))
functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ('git', 'commit_env', 'build_detail_repos')]
ns = dict(os=os, subprocess=subprocess, Path=Path, uuid=uuid, T0=1700000000)
exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), 'exec'), ns)
tmp = Path(tempfile.mkdtemp(prefix='t249-detail-fixture-', dir=os.environ['A2A_REQUEST_DIR']))
history, unborn = tmp / 'history', tmp / 'unborn'
hashes = ns['build_detail_repos'](history, unborn)
git = ns['git']
status = git(unborn, 'status', '--porcelain=v1', '-z', '--untracked-files=all').split('\0')[:-1]
states = {entry[3:]: entry[:2] for entry in status}
assert states['file*.txt'] == 'A '
assert states['file[1].txt'] == 'AM'
assert states[':(glob)*.txt'] == ' A'
assert states['untracked.txt'] == '??'
head = subprocess.run(['git', '-C', str(unborn), 'rev-parse', '--verify', '-q', 'HEAD'], capture_output=True)
assert head.returncode == 1
assert git(history, 'rev-list', '--count', 'HEAD').strip() == '2'
assert len(git(history, 'status', '--porcelain=v1', '-z').split('\0')[:-1]) == 6
sizes = [p.stat().st_size for p in tmp.rglob('*') if p.is_file() and not p.is_symlink()]
result = dict(result='PASS: 仅夹具构造', hashes=hashes, unborn_states=states,
              history_status=git(history, 'status', '--porcelain=v1', '-z').split('\0')[:-1],
              directory=str(tmp), time=time.time(), files=len(sizes), bytes=sum(sizes))
with (OUT / 'fixture-probe.json').open('x', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
    f.write('\n')
shutil.rmtree(tmp)
print(json.dumps(result, ensure_ascii=False))
print('temporary_directory_removed=' + str(not tmp.exists()))
