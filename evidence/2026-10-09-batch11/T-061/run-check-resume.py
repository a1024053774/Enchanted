#!/usr/bin/env python3
"""Save one bounded T-061 command without replacing earlier evidence."""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys

evidence = Path(__file__).resolve().parent
fork = Path('/Users/luckye/Documents/Code/synara-t045')
label, *command = sys.argv[1:]
if not command or not label.replace('-', '').isalnum():
    raise SystemExit('usage: run-check.py LABEL COMMAND [ARG ...]')
log_path = evidence / (label + '.log')
receipt_path = evidence / (label + '.command.json')
if log_path.exists() or receipt_path.exists():
    raise SystemExit('evidence already exists: ' + label)
env = os.environ.copy()
env['A2A_SYNARA_SLOT'] = 't061'
receipt = {
    'task': 'T-061', 'ready_rev': 2, 'worker': 's11-t061b',
    'cwd': str(fork), 'argv': command, 'A2A_SYNARA_SLOT': 't061',
    'started_at': dt.datetime.now(dt.timezone.utc).isoformat(),
    'fork_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=fork, text=True).strip(),
    'fork_diff': subprocess.check_output(['git', 'diff'], cwd=fork, text=True),
}
with log_path.open('x', encoding='utf-8') as output:
    result = subprocess.run(command, cwd=fork, env=env, stdout=output, stderr=subprocess.STDOUT)
receipt['exit_code'] = result.returncode
receipt['ended_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({ 'label': label, 'exit_code': result.returncode, 'log': str(log_path) }))
raise SystemExit(result.returncode)
