#!/usr/bin/env python3
"""Preserve only probe records and remove only the homes created by probe.py."""
import datetime as dt
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

BASE = Path(__file__).resolve().parent
for label in sys.argv[1:]:
    out = BASE / label
    manifest = json.loads((out / 'launch.json').read_text(encoding='utf-8'))
    temp = Path(manifest['temp_root'])
    home = Path(manifest['codex_home'])
    if not temp.name.startswith('a2a-t074-') or home.parent != temp:
        raise SystemExit('Refusing cleanup outside owned probe root')
    if not home.exists():
        raise SystemExit('Probe already archived; keep existing artifacts')
    processes = subprocess.check_output(['/bin/ps', '-axo', 'pid,ppid,pgid,command'], text=True)
    live = [line for line in processes.splitlines() if str(temp) in line or str(temp.resolve()) in line]
    if live:
        raise SystemExit('Owned processes still alive; preserve home: ' + repr(live))
    archive = out / 'native-rollouts'
    archive.mkdir(exist_ok=True)
    for file in home.glob('sessions/**/*.jsonl'):
        destination = archive / file.name
        if destination.exists():
            if destination.read_bytes() != file.read_bytes():
                raise SystemExit('Archived rollout differs; refuse overwrite')
        else:
            shutil.copyfile(file, destination)
    copied = {}
    for name in ['config.toml', 'rules/default.rules', 'history.jsonl']:
        file = home / name
        if file.exists():
            copied[name] = file.read_text(encoding='utf-8')
    (out / 'isolation-files.json').write_text(json.dumps(copied, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    connection = sqlite3.connect('file:' + str(home / 'thread_history_1.sqlite') + '?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    turns = [dict(row) for row in connection.execute('SELECT thread_id,turn_id,status,started_at,completed_at,duration_ms FROM thread_turns ORDER BY rollout_ordinal')]
    connection.close()
    (out / 'native-turns.json').write_text(json.dumps(turns, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    logs = sqlite3.connect('file:' + str(home / 'logs_2.sqlite') + '?mode=ro', uri=True)
    logs.row_factory = sqlite3.Row
    diagnostics = [dict(row) for row in logs.execute('SELECT id,ts,ts_nanos,level,target,feedback_log_body FROM logs WHERE level IN ("WARN","ERROR") ORDER BY id')]
    logs.close()
    (out / 'warning-error-log.json').write_text(json.dumps(diagnostics, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    shutil.rmtree(temp)
    receipt = dict(cleaned_at=dt.datetime.now(dt.timezone.utc).isoformat(), temp_root=str(temp),
                   entire_created_root_removed=not temp.exists(), auth_copied_to_evidence=False,
                   live_processes_before_cleanup=live)
    (out / 'cleanup.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt))
