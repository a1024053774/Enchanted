"""Read the controller-preserved failed fixture, without changing storage."""
import contextlib
import json
from pathlib import Path
import sqlite3
import sys

root = Path(sys.argv[1]).resolve()
with contextlib.closing(sqlite3.connect((root / 'state/state.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
    db.row_factory = sqlite3.Row
    task = json.loads(db.execute('SELECT data FROM tasks').fetchone()['data'])
    runs = [json.loads(row['data']) for row in db.execute('SELECT data FROM runs')]
    events = [dict(row) for row in db.execute("SELECT seq,type,details FROM events WHERE type IN ('runtime_bound','rejected','run_started','run_phase','run_finished') ORDER BY seq")]
    for row in events: row['details'] = json.loads(row['details'])
    rejects = [dict(row) for row in db.execute("SELECT seq,type,data FROM orchestration_events WHERE type='request_rejected' ORDER BY seq")]
    for row in rejects: row['data'] = json.loads(row['data'])
record = {'database': str(root / 'state/state.sqlite3'), 'phase': 'after executor #12 forced cleanup, read-only',
    'task_state': task['state'], 'attempt': task['current_attempt'], 'runs': runs,
    'selected_gate_events': events, 'orchestration_rejections': rejects, 'real_codex_turns': 0}
with Path(sys.argv[2]).open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps({'state': task['state'], 'identity': task['current_attempt']['runtime_identity'],
    'runs': [{'phase': r['phase'], 'outcome': r['outcome']} for r in runs],
    'gate_rejections': [e['details'].get('error') for e in events if e['type'] == 'rejected'],
    'orchestration_rejections': [e['data']['result']['error'] for e in rejects]}, ensure_ascii=False))
