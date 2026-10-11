#!/usr/bin/env python3
"""Deterministic PTY byte receiver; no vendor executable, API, model or tools.

The version reply is a fixture-only input to the existing fixed-version launcher.
Only session_meta is synthesized, to permit its final archival read. This fixture
does not produce Claude signals or claim to test a real Codex turn.
"""
import json
import os
from pathlib import Path
import sys
import tty
import uuid

if sys.argv[1:] == ['--version']:
    print('codex-cli 0.162.1')
    raise SystemExit(0)

home = Path(os.environ['CODEX_HOME'])
session = str(uuid.uuid4())
native = home / 'sessions' / ('rollout-' + session + '.jsonl')
native.parent.mkdir(parents=True, exist_ok=True)
with native.open('x', encoding='utf-8') as stream:
    stream.write(json.dumps({'type':'session_meta','payload':{'source':'cli','id':session}})+'\n')
with (home / 'receiver-started.json').open('x', encoding='utf-8') as stream:
    json.dump({'pid':os.getpid(),'argv':sys.argv,'fixture':True,'model_turns':0},stream)
tty.setraw(sys.stdin.fileno())
os.write(sys.stdout.fileno(), b'T078_DETERMINISTIC_RECEIVER_READY\r\n\x1b[?2004h')
with (home / 'received.bin').open('xb', buffering=0) as stream:
    while True:
        data = os.read(sys.stdin.fileno(), 65536)
        if not data:
            break
        stream.write(data)
