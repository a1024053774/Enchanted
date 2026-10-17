"""Read only the preserved 09A output and archived database; no processes or sockets."""
import argparse, base64, datetime, json, sqlite3, tarfile, tempfile
from pathlib import Path
p = argparse.ArgumentParser(); p.add_argument('--output', type=Path, required=True); args = p.parse_args()
base = Path(__file__).resolve().parent
materials = base / 'p1-materials-09'
archive = Path(json.loads((base / 'external-archive-578c9fe0799847c19ce5020b5ec503d0.json').read_text())['files'][0]['archive'])
run = json.loads((materials / 'continue-esc/result.json').read_text())
with tarfile.open(archive) as arc, tempfile.TemporaryDirectory(prefix='t078-readback-', dir='/tmp') as temporary:
    dbname = next(n for n in arc.getnames() if n.endswith('/state/state.sqlite3'))
    dbpath = Path(temporary) / 'state.sqlite3'
    for n in [dbname, dbname + '-wal', dbname + '-shm']:
        if n in arc.getnames(): (Path(temporary) / Path(n).name).write_bytes(arc.extractfile(n).read())
    with sqlite3.connect(dbpath.as_uri() + '?mode=ro', uri=True) as db:
        events = [dict(seq=r[0], time=r[1], type=r[2], launch=r[3], data=json.loads(r[4])) for r in db.execute('SELECT seq,time,type,launch,data FROM orchestration_events ORDER BY seq')]
        inputs = [json.loads(r[0]) for r in db.execute('SELECT data FROM user_inputs')]
    raw = arc.extractfile(next(n for n in arc.getnames() if n.endswith('/pty.raw'))).read()
    cancel = json.loads(arc.extractfile(next(n for n in arc.getnames() if n.endswith('/api-cancelled-1.json'))).read())
chunks = [json.loads(line) for line in (materials / 'continue-esc/electron/received.ndjson').read_text().splitlines()]
window_output = b''.join(base64.b64decode(v['data_base64']) for v in chunks)
snapshots = [json.loads(line) for line in (materials / 'continue-esc/electron/snapshots.ndjson').read_text().splitlines()]
stages = [json.loads(line) for line in (materials / 'continue-esc/electron/stages.jsonl').read_text().splitlines()]
selected = [e for e in events if e['type'] in ['window_opened', 'window_closed', 'terminal_input_write_intent', 'terminal_input_written', 'claude_submission_retired', 'paste_intent', 'turn_submitted', 'turn_start_signal', 'turn_end_signal', 'pane_idle', 'pane_stop_intent', 'pane_exit', 'daemon_stopped']]
report = {'status': 'PASS', 'claim': '09A Esc was not admitted or written by the backend', 'argv': __import__('sys').argv,
          'archive': str(archive), 'launch': run['input']['launch'], 'code_revision': run['input']['code_revision'],
          'events': selected, 'user_inputs': inputs, 'all_event_types': sorted({e['type'] for e in events}),
          'snapshots_count': len(snapshots), 'input_enabled_values': sorted({v['input_enabled'] for v in snapshots}),
          'busy_correct_dispatch_snapshots': sum(v['pane']['state'] == 'busy' and v['pane'].get('active', {}).get('dispatch') == run['first_dispatch']['dispatch']['id'] for v in snapshots),
          'key_stages': [v for v in stages if v.get('command') == 'terminal-key'],
          'api_cancel': {**cancel, 'utc': datetime.datetime.fromtimestamp(cancel['observed_at'], datetime.timezone.utc).isoformat()},
          'cleanup_cli_exit': json.loads((materials / 'cleanup/result.json').read_text())['cli_exit_verdict'],
          'pty_output_bytes': len(raw), 'window_output_bytes': len(window_output), 'window_output_is_exact_prefix': raw[:len(window_output)] == window_output,
          'pty_scope': 'pty.raw and received.ndjson are terminal OUTPUT, not proof of input writes; database actions and write receipts determine admission.'}
assert not inputs and not any(e['type'] in ['terminal_input_write_intent', 'terminal_input_written', 'claude_submission_retired'] for e in events)
assert report['input_enabled_values'] == [False] and report['busy_correct_dispatch_snapshots'] > 0
assert report['window_output_is_exact_prefix']
with args.output.open('x', encoding='utf-8') as stream: json.dump(report, stream, ensure_ascii=False, indent=2)
print(json.dumps({k: report[k] for k in ['status', 'claim', 'snapshots_count', 'busy_correct_dispatch_snapshots', 'api_cancel', 'pty_output_bytes', 'window_output_bytes']}, ensure_ascii=False))
