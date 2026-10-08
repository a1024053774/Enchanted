#!/usr/bin/env python3
"""Append one user message per thread with thread.turn.start. Providers are disabled and CODEX_HOME is empty, so no model turn can run;
the point is only to have real Synara message rows (real message ids) for the intervention marker."""
import json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
here = Path(__file__).resolve().parent
f = json.loads((here / 'fixture.json').read_text())
env = {**os.environ, 'A2A_SYNARA_SLOT': 't043'}
now = lambda: datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
texts = {'worker': '先按 CONTRACT.md 补齐游标分页，再跑一遍 oracle。', 'reviewer': '只审查 worker 的提交，不要改代码。', 'monitor': '记录每次提交与验收，不要介入。'}
out = {}
for role, tid in f['threads'].items():
    mid = f"{tid}-msg-1"
    cmd = {'type': 'thread.turn.start', 'commandId': f"{tid}-turn-1", 'threadId': tid,
           'message': {'messageId': mid, 'role': 'user', 'text': texts[role], 'attachments': []}, 'runtimeMode': 'approval-required', 'interactionMode': 'default', 'createdAt': now()}
    path = here / f'msg-{role}-input.json'; path.write_text(json.dumps(cmd, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    p = subprocess.run(['./a2a/scripts/bun', str(here / 'rpc.mjs'), f'msg-{role}', 'http://127.0.0.1:5816', str(path)], cwd='/Users/luckye/Documents/Code/synara', env=env, text=True, capture_output=True)
    print(role, p.stdout.strip()[:300]); out[role] = mid
(here / 'messages.json').write_text(json.dumps(out, indent=2) + '\n')
