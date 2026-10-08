#!/usr/bin/env python3
"""Create the project, three threads, the membership and one user message per thread through the published feature socket / HTTP routes."""
import json, os, subprocess, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path
here = Path(__file__).resolve().parent
f = json.loads((here / 'fixture.json').read_text())
endpoint = 'http://127.0.0.1:5816'
env = {**os.environ, 'A2A_SYNARA_SLOT': 't043'}
now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
def rpc(label, command):
    path = here / f'{label}-input.json'; path.write_text(json.dumps(command, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    p = subprocess.run(['./a2a/scripts/bun', str(here / 'rpc.mjs'), label, endpoint, str(path)], cwd='/Users/luckye/Documents/Code/synara', env=env, text=True, capture_output=True)
    print(label, p.stdout.strip()[:200], p.stderr.strip()[-200:]); return p
rpc('seed-project', {'type': 'project.create', 'commandId': f['task'] + '-project', 'projectId': f['project'], 'title': '分页交付', 'workspaceRoot': f['repo'], 'createdAt': now})
titles = {'worker': 'worker · 分页实现', 'reviewer': 'reviewer · 分页审查', 'monitor': 'monitor · 过程观察'}
for role, tid in f['threads'].items():
    rpc('seed-thread-' + role, {'type': 'thread.create', 'commandId': tid, 'threadId': tid, 'projectId': f['project'], 'title': titles[role],
        'modelSelection': {'provider': 'codex', 'model': 'gpt-6.1-sol', 'options': {'reasoningEffort': 'xhigh', 'fastMode': True}},
        'runtimeMode': 'approval-required', 'interactionMode': 'default', 'envMode': 'local', 'branch': None, 'worktreePath': None, 'createdAt': now})
task = {'taskId': f['task'], 'projectId': f['project'], 'title': '分页交付', 'revision': 0,
        'members': [{'threadId': t, 'role': r} for r, t in f['threads'].items()]}
req = urllib.request.Request(endpoint + '/api/a2a/membership', data=json.dumps({'command': 'save', 'task': task}).encode(), headers={'Content-Type': 'application/json'})
print(urllib.request.urlopen(req).read().decode()[:300])
