#!/usr/bin/env python3
"""A second, gate-less task with five threads, to check horizontal layout and scrolling beyond three columns."""
import json, os, subprocess, urllib.request
from datetime import datetime, timezone
from pathlib import Path
here = Path(__file__).resolve().parent
f = json.loads((here / 'fixture.json').read_text())
now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
env = {**os.environ, 'A2A_SYNARA_SLOT': 't043'}
roles = ['worker', 'reviewer', 'monitor', 'worker', 'reviewer']
members = []
for i, role in enumerate(roles):
    tid = f"{f['task']}-wide-{i + 1}"
    path = here / f'seed2-thread-{i + 1}-input.json'
    path.write_text(json.dumps({'type': 'thread.create', 'commandId': tid, 'threadId': tid, 'projectId': f['project'], 'title': f'{role} · 长任务 {i + 1}',
        'modelSelection': {'provider': 'codex', 'model': 'gpt-6.1-sol', 'options': {'reasoningEffort': 'xhigh', 'fastMode': True}},
        'runtimeMode': 'approval-required', 'interactionMode': 'default', 'envMode': 'local', 'branch': None, 'worktreePath': None, 'createdAt': now}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    p = subprocess.run(['./a2a/scripts/bun', str(here / 'rpc.mjs'), f'seed2-thread-{i + 1}', 'http://127.0.0.1:5816', str(path)], cwd='/Users/luckye/Documents/Code/synara', env=env, text=True, capture_output=True)
    print(p.stdout.strip()[:120]); members.append({'threadId': tid, 'role': role})
task = {'taskId': f['task'] + '-wide', 'projectId': f['project'], 'title': '长任务 · 五个会话', 'revision': 0, 'members': members}
req = urllib.request.Request('http://127.0.0.1:5816/api/a2a/membership', data=json.dumps({'command': 'save', 'task': task}).encode(), headers={'Content-Type': 'application/json'})
print(urllib.request.urlopen(req).read().decode()[:200])
