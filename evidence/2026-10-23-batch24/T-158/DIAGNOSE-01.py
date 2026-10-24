"""Read the stopped RUN-OUTSIDE-01 fixture; retain the relevant timeline without copying its database."""
import argparse
import json
from pathlib import Path
import sqlite3

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--fixture', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
assert not args.output.exists(), 'Preserve prior evidence'
state = args.fixture / 'state'
assert not (state / 'daemon.pid').exists() and not (state / 'control.sock').exists(), 'Read only a stopped fixture'
summary = json.loads(Path('evidence/2026-10-23-batch24/T-158/t158-outside-01.YXVx70-flow-baseline.json').read_text(encoding='utf-8'))
old = summary['observed']['commands'][0]['result']['attempt']
types = ['pane_idle', 'dispatch_queued', 'paste_intent', 'paste_written', 'turn_submit_intent',
         'turn_submitted', 'turn_start_signal', 'turn_end_signal', 'pane_stop_intent', 'pane_exit']
with sqlite3.connect((state / 'state.sqlite3').as_uri() + '?mode=ro&immutable=1', uri=True) as db:
    db.row_factory = sqlite3.Row
    timeline = []
    for row in db.execute('SELECT seq,time,type,data FROM orchestration_events WHERE launch=? ORDER BY seq',
                          (old['runtime_identity']['launch'],)):
        if row['type'] not in types:
            continue
        data = json.loads(row['data'])
        timeline.append(dict(seq=row['seq'], time=row['time'], type=row['type'],
            data={k: v for k, v in data.items() if k in ['id', 'dispatch', 'context', 'submission', 'prompt_id', 'reason']}))
    gate = [dict(seq=row['seq'], time=row['time'], type=row['type'],
                 error=json.loads(row['details']).get('error'), reason=json.loads(row['details']).get('reason'))
            for row in db.execute("SELECT seq,time,type,details FROM events WHERE type IN ('rejected','revoked') ORDER BY seq")]
result = dict(fixture=str(args.fixture), attempt=old['attempt_id'], orchestration=timeline, gate=gate,
    conclusion='Fixture error: reclaim at 01:01:18.393Z ran inside repair paste 01:01:18.293Z to submit 01:01:18.594Z. '
               'The fixture idle predicate omitted writing=false; the gate correctly refused an in-flight input.')
with args.output.open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
