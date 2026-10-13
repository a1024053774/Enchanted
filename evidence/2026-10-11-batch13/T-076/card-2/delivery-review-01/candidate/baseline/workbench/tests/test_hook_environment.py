#!/usr/bin/env python3
"""Tailer contract during the delivery-channel decision: no daemon query.

Failures: identity missing, newline injection, duplicate managed trailers,
launch-request model represented as observed, or a dependency on a live daemon.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
source = Path(__file__).resolve().parents[1] / 'hooks/hook.py'
spec = importlib.util.spec_from_file_location('hook', source)
hook = importlib.util.module_from_spec(spec); spec.loader.exec_module(hook)
root = Path(tempfile.mkdtemp(prefix='a2a-hook-env-', dir='/tmp'))
message = root / 'message.txt'
env = {'PATH': os.environ['PATH'], 'A2A_TASK': 'fixture', 'A2A_ATTEMPT': 'attempt', 'A2A_SESSION': 'session',
       'A2A_ROLE': 'worker', 'A2A_TOOL': 'codex-cli 0.162.1', 'A2A_LAUNCH': 'launch', 'CODEX_THREAD_ID': 'native'}
message.write_text('Subject\n\nA2A-Task: old\nA2A-Task: old-again\nSigned-off-by: Test\n', encoding='utf-8')
failures = []
try:
    with patch.dict(os.environ, env, clear=True), patch.object(sys, 'argv', ['prepare-commit-msg', str(message)]):
        hook.add_trailers()
    lines = subprocess.check_output(['git', 'interpret-trailers', '--parse', str(message)], text=True).splitlines()
    expected = ['A2A-Task: fixture', 'A2A-Attempt: attempt', 'A2A-Session: session', 'A2A-Role: worker',
                'A2A-Tool: codex-cli 0.162.1', 'A2A-Model: unknown', 'A2A-Effort: unknown',
                'A2A-Native-Session: native', 'A2A-Launch: launch']
    assert sorted(line for line in lines if line.startswith('A2A-')) == sorted(expected)
    assert 'Signed-off-by: Test' in lines
except Exception as error:
    failures.append(repr(error))
for key, replacement in [('A2A_SESSION', None), ('A2A_TASK', 'fixture\nA2A-Role: executor')]:
    bad = dict(env)
    if replacement is None: bad.pop(key)
    else: bad[key] = replacement
    before = message.read_bytes()
    try:
        with patch.dict(os.environ, bad, clear=True), patch.object(sys, 'argv', ['prepare-commit-msg', str(message)]):
            hook.add_trailers()
        failures.append('bad identity accepted: ' + key)
    except (KeyError, ValueError):
        if message.read_bytes() != before: failures.append('message changed before identity refusal')
record = {'status': 'PASS' if not failures else 'INCOMPLETE', 'root': str(root), 'failures': failures}
(args.output / 'results.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, ensure_ascii=False, indent=2))
raise SystemExit(0 if not failures else 1)
