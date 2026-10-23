#!/usr/bin/env python3
"""Count primary native turns, not reservations or tool/model requests.

Cross-check the before-stop event capture with the stopped database copy.
Reject an unknown launch, missing primary session, or incomplete turn.
"""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3

p = argparse.ArgumentParser()
p.add_argument('--run', type=Path, required=True)
p.add_argument('--summary', type=Path, required=True)
a = p.parse_args()
assert not a.summary.exists(), 'Preserve existing evidence'
runs = []
for name in ('registration', 'repeat-feedback', 'green'):
    result = json.loads((a.run / (name + '.json')).read_text(encoding='utf-8'))
    raw = Path(result['raw_artifacts'])
    captured = json.loads((raw / 'all-events-before-stop.json').read_text(encoding='utf-8'))['events']
    with closing(sqlite3.connect((raw / 'state.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
        stored = [{'type': t, 'launch': launch, 'data': json.loads(data)}
                  for t, launch, data in db.execute('SELECT type,launch,data FROM orchestration_events ORDER BY seq')]
    launches = []
    for file in ('launch-record.json', 'review-launch.json'):
        if not (raw / file).exists():
            continue  # Registration and pre-review mutants do not launch a reviewer.
        launch = json.loads((raw / file).read_text(encoding='utf-8'))
        bindings = {r['data']['native_session'] for r in stored if r['type'] == 'pane_native_session' and r['launch'] == launch['id']}
        assert len(bindings) == 1, 'Primary native session is unconfirmed'
        native = next(iter(bindings))

        def turns(rows, kind):
            return sorted({r['data']['record']['payload']['turn_id'] for r in rows
                           if r['type'] == 'native_record' and r['launch'] == launch['id']
                           and r['data']['file'].endswith(native + '.jsonl')
                           and r['data']['record']['type'] == 'event_msg'
                           and r['data']['record']['payload'].get('type') == kind})

        started, completed = turns(stored, 'task_started'), turns(stored, 'task_complete')
        intents = sum(r['type'] == 'turn_submit_intent' and r['launch'] == launch['id'] for r in stored)
        assert started == completed == turns(captured, 'task_started') == turns(captured, 'task_complete')
        assert len(started) == intents, 'Dispatch intents and completed native turns disagree'
        launches.append({'role': launch['role'], 'launch': launch['id'], 'native_session': native,
                         'started_turn_ids': started, 'completed_turn_ids': completed, 'turn_submit_intents': intents,
                         'real_turns': len(started)})
    known = {r['launch'] for r in launches}
    assert {r['launch'] for r in stored if r['type'] == 'native_record'} <= known, 'Uncounted native launch'
    runs.append({'run': name, 'outcome': result['status'], 'fixture': result['fixture'],
                 'cutoff': 'stopped SQLite archive, checked against all-events-before-stop.json',
                 'launches': launches, 'real_turns': sum(r['real_turns'] for r in launches)})
report = {'status': 'PASS', 'run': str(a.run), 'runs': runs,
          'real_turns_used': sum(r['real_turns'] for r in runs), 'reserved_maximum': 8,
          'arithmetic_unused': 8 - sum(r['real_turns'] for r in runs),
          'authorization_note': 'Authorization 02 was for one run; unused reservations do not authorize another run.'}
with a.summary.open('x', encoding='utf-8') as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps({'status': report['status'], 'real_turns_used': report['real_turns_used'],
                  'runs': [{k: r[k] for k in ('run', 'real_turns')} for r in runs]}, ensure_ascii=False))
