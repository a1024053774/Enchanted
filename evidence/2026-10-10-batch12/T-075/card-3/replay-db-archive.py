#!/usr/bin/env python3
"""Replay only the archive/cleanup finally against copies of retained probe data."""
import argparse
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--receipt', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
original = Path(json.loads((args.receipt / 'setup.json').read_text(encoding='utf-8'))['state'])
assert not (original / 'daemon.pid').exists(), 'Source daemon must already be stopped'
root = Path(tempfile.mkdtemp(prefix='a2a-archive-replay-', dir='/tmp'))
state = root / 'state'; state.mkdir()
isolated = root / 'empty-home'; isolated.mkdir()
inputs = {p.name: p.read_bytes() for p in original.glob('state.sqlite3*') if not p.name.endswith('-shm')}
for name, raw in inputs.items(): (state / name).write_bytes(raw)
source = Path(__file__).resolve().parents[4] / 'workbench/tests/fixture_artifacts.py'
spec = importlib.util.spec_from_file_location('probe', source)
probe = importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
namespace = dict(vars(probe), started=False, state=state, output=args.output, isolated=isolated,
                 cleanup_pids=set(), listeners=[], run=lambda *args, **kwargs: None, verdict={'status': 'INCOMPLETE'},
                 save=lambda name, value: (args.output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'))
probe.archive_and_cleanup(state, args.output, isolated, set(), namespace['run'], namespace['save'], namespace['verdict'])
assert not namespace['verdict'].get('archive_error'), namespace['verdict']
db = sqlite3.connect((args.output / 'state.sqlite3').resolve().as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
try:
    rows = [dict(row) for row in db.execute('SELECT * FROM orchestration_events ORDER BY seq')]
    for row in rows: row['data'] = json.loads(row['data'])
    expected = json.loads((args.receipt / 'all-events-before-stop.json').read_text(encoding='utf-8'))['events']
    assert rows[:len(expected)] == expected
    assert db.execute('PRAGMA journal_mode').fetchone()[0] == 'delete'
    assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
finally: db.close()
assert all((original / name).read_bytes() == raw for name, raw in inputs.items())
record = {'status': 'PASS', 'scope': 'archive-only replay, no daemon or model execution',
          'matched_event_prefix': len(expected), 'archived_events': len(rows), 'source_unchanged': True,
          'isolated_fixture_removed': not isolated.exists(), 'copy_root': str(root)}
(args.output / 'results.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, ensure_ascii=False, indent=2))
