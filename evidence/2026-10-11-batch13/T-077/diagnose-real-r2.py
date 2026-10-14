#!/usr/bin/env python3
"""Extract a stopped experiment's evidence; no processes, retries or API calls."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tarfile

ROOT = Path(__file__).resolve().parent
source = ROOT / 'real-conflict-02/attempt-1'
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
events = json.loads((source / 'events-after-stop.json').read_text(encoding='utf-8'))
run = json.loads((source / 'run.json').read_text(encoding='utf-8'))
launch = json.loads((source / 'launch-record.json').read_text(encoding='utf-8'))
timeline = []
for event in events:
    kind, data = event['type'], event['data']
    row = {'seq': event['seq'], 'time': event['time'], 'type': kind}
    if kind == 'native_record':
        record = data['record']; payload = record['payload']; subtype = payload.get('type')
        row.update(raw_timestamp=record.get('timestamp'), ordinal=record.get('ordinal'))
        if record['type'] == 'turn_context':
            row.update(type='turn_context', turn=payload['turn_id'], model=payload['model'], effort=payload.get('effort'))
        elif subtype in ('task_started', 'task_complete'):
            row.update(type=subtype, turn=payload['turn_id'])
        elif subtype == 'thread_settings_applied':
            settings = payload['thread_settings']
            row.update(type=subtype, model=settings['model'], effort=settings.get('reasoning_effort'), tier=settings.get('service_tier'))
        elif 'rate_limits' in payload:
            row.update(type='rate_limits', limits=payload['rate_limits'])
        else:
            continue
    elif kind in ('relay_processed', 'relay_rejected'):
        row.update(key=data['key'], ok=data['result']['ok'], error=data['result'].get('error'))
    elif kind in ('dispatch_queued', 'paste_written', 'turn_submit_intent', 'turn_submitted', 'pane_idle', 'pane_exit', 'native_final_read'):
        row.update(data={k: v for k, v in data.items() if k not in ('text', 'stop')})
    else:
        continue
    timeline.append(row)
with tarfile.open(source / 'fixture-artifacts.tar.gz') as archive:
    pty = next(m for m in archive if m.isfile() and m.name.endswith('/pty.raw'))
    raw = archive.extractfile(pty).read()
    # Locate an excerpt for human inspection; this is not a semantic classifier
    # or an acceptance oracle. Keep original ANSI bytes and their offset.
    offset = raw.find(b'Approaching rate limits')
    excerpt_start = max(0, offset - 200) if offset >= 0 else max(0, len(raw) - 5000)
    excerpt = raw[excerpt_start:]
    (args.output / 'pty-tail.bin').write_bytes(excerpt)
    (args.output / 'pty-tail-repr.txt').write_text(repr(excerpt.decode('utf-8', errors='replace')) + '\n', encoding='utf-8')
    rollouts = [m for m in archive if m.isfile() and m.name.startswith('codex-home/sessions/') and m.name.endswith('.jsonl')]
    rollout = rollouts[0]
    records = [json.loads(line) for line in archive.extractfile(rollout).read().splitlines()]
with closing(sqlite3.connect((source / 'databases-after-stop/state.sqlite3').resolve().as_uri() + '?mode=ro&immutable=1', uri=True)) as db:
    task = json.loads(db.execute('SELECT data FROM tasks').fetchone()[0])
    gates = db.execute("SELECT type FROM events WHERE type IN ('submitted','verified','integrated')").fetchall()
    intents = db.execute('SELECT key,launch,request_id FROM relay_requests').fetchall()
result = {'status': 'INCOMPLETE', 'scope': 'Read-only retrospective diagnosis; no new acceptance verdict',
    'candidate': run['product_revision'], 'launch': launch['id'], 'native': task['current_attempt']['runtime_identity']['native_session'],
    'task_state': task['state'], 'candidate_commit': task['candidate_commit'], 'verification': task['verification'],
    'gate_events': gates, 'relay_intents': intents, 'timeline': timeline,
    'protocol_error_events': [{'seq': e['seq'], 'type': e['type']} for e in events if e['type'] in
        ('permission_wait', 'dispatch_unknown', 'stop_transfer_failed', 'queue_stopped', 'native_final_read_failed', 'terminal_protocol_failed')],
    'pty': {'archive': str(source / 'fixture-artifacts.tar.gz'), 'member': pty.name, 'bytes': len(raw),
            'excerpt_start': excerpt_start, 'reminder_text_offset': offset, 'excerpt': 'pty-tail.bin'},
    'rollout': {'member': rollout.name, 'bytes': rollout.size, 'last_timestamp': records[-1]['timestamp'],
                'last_ordinal': records[-1]['ordinal'], 'root_starts': sum(r['type'] == 'event_msg' and r['payload'].get('type') == 'task_started' for r in records)},
    'budget': {'old_observed': 4, 'new_observed': run['observed_root_turns'], 'new_reserved': run['real_turns_reserved'],
               'new_reserved_not_released': True, 'ledger': str(ROOT / 'real-turn-budget-02.jsonl')},
    'isolated_home_removed': run['isolated_home_removed'], 'new_real_turns': 0,
    'sources': [str(source / name) for name in ('run.json', 'events-after-stop.json', 'launch-record.json', 'fixture-artifacts.tar.gz', 'databases-after-stop/state.sqlite3')]}
with (args.output / 'diagnosis.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps({'status': result['status'], 'task_state': result['task_state'], 'root_starts': result['rollout']['root_starts'],
                  'pty_reminder_offset': offset, 'new_real_turns': 0}, ensure_ascii=False))
