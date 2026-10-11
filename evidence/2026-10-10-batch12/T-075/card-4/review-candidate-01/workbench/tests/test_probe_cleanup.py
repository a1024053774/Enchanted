#!/usr/bin/env python3
"""Run the probe's actual finally body without launching a model or a daemon.

Failure cases: an existing backup is overwritten; backup failure prevents home
cleanup; an unconfirmed live daemon's home is deleted; a closed WAL source cannot
be opened read-only; committed WAL rows are omitted. No model or service starts.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace

def no_process(*args, **kwargs):
    raise AssertionError('This archive-only case must not invoke a process')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).with_name('fixture_artifacts.py')
    spec = importlib.util.spec_from_file_location('probe', source)
    probe = importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
    evidence = []
    for case in ('backup-error', 'existing-backup', 'live-daemon', 'backup-success', 'wal-closed', 'wal-pending', 'delayed-process-exit'):
        root = Path(tempfile.mkdtemp(prefix='a2a-cleanup-', dir='/tmp'))
        state = root / 'state'; output = root / 'output'; isolated = root / 'codex-home'
        for p in (state, output, isolated): p.mkdir()
        (isolated / 'fixture-marker').write_text('isolated data', encoding='utf-8')
        fixture_db = sqlite3.connect(state / 'state.sqlite3')
        if case.startswith('wal-'): fixture_db.execute('PRAGMA journal_mode=WAL')
        fixture_db.execute('CREATE TABLE fixture(value TEXT)'); fixture_db.execute("INSERT INTO fixture VALUES ('source')")
        fixture_db.commit()
        expected_rows = [('source',)]
        if case == 'wal-pending':
            fixture_db.execute("INSERT INTO fixture VALUES ('committed-in-wal')"); fixture_db.commit()
            expected_rows.append(('committed-in-wal',))
        else:
            fixture_db.close()
        source_bytes = {p.name: p.read_bytes() for p in state.glob('state.sqlite3*') if not p.name.endswith('-shm')}
        dest = output / 'state.sqlite3'
        if case == 'backup-error': dest.mkdir()
        if case == 'existing-backup':
            with sqlite3.connect(dest) as db:
                db.execute('CREATE TABLE sentinel(value TEXT)'); db.execute("INSERT INTO sentinel VALUES ('original')")
        if case == 'live-daemon': (state / 'daemon.pid').write_text('fixture-live\n')
        namespace = dict(vars(probe), started=False, state=state, output=output, isolated=isolated,
                         cleanup_pids=set(), listeners=[], run=no_process, verdict={'status': 'BLOCKED', 'fixture': case},
                         save=lambda name, value: (output / name).write_text(json.dumps(value), encoding='utf-8'))
        observations = []
        if case == 'delayed-process-exit':
            namespace['cleanup_pids'] = {123}
            def process_readback(argv, **kwargs):
                stdout = '123 1 123 (fixture-helper)\n' if len(observations) < 2 else ''
                observations.append({'argv': argv, 'stdout': stdout})
                return SimpleNamespace(stdout=stdout, returncode=0 if stdout else 1)
            namespace['run'] = process_readback
        exception = None
        try:
            probe.archive_and_cleanup(state, output, isolated, namespace['cleanup_pids'], namespace['run'], namespace['save'], namespace['verdict'])
        except Exception as error:  # Test records the actual failure; it never turns an exception into PASS.
            exception = repr(error)
        failures = []
        if exception: failures.append('finally escaped: ' + exception)
        if isolated.exists() != (case == 'live-daemon'): failures.append('wrong home retention')
        if case == 'existing-backup':
            try:
                with sqlite3.connect(dest) as db:
                    if db.execute('SELECT value FROM sentinel').fetchall() != [('original',)]: failures.append('backup changed')
            except sqlite3.Error: failures.append('existing backup overwritten')
        if not (output / 'verdict.json').exists(): failures.append('final verdict missing')
        if case in ('backup-success', 'wal-closed', 'wal-pending', 'delayed-process-exit'):
            if namespace['verdict'].get('archive_error'): failures.append('archive_error: ' + namespace['verdict']['archive_error'])
            try:
                db = sqlite3.connect(dest.resolve().as_uri() + '?mode=ro', uri=True)
                try:
                    if db.execute('SELECT value FROM fixture ORDER BY rowid').fetchall() != expected_rows:
                        failures.append('archived rows differ from independent fixture values')
                    if db.execute('PRAGMA journal_mode').fetchone() != ('delete',): failures.append('archive is not standalone')
                    if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]: failures.append('archive integrity failed')
                finally: db.close()
            except sqlite3.Error as error: failures.append('archive readback failed: ' + str(error))
            for name, before in source_bytes.items():
                if (state / name).read_bytes() != before: failures.append('source bytes changed: ' + name)
        if case == 'wal-pending': fixture_db.close()
        evidence.append({'case': case, 'root': str(root), 'failures': failures, 'exception': exception, 'process_readbacks': observations})
    record = {'status': 'PASS' if all(not item['failures'] for item in evidence) else 'INCOMPLETE', 'cases': evidence}
    (args.output / 'results.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
