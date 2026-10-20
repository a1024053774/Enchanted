"""Read the real Node contract's closed database from Python 3.9.

Failure cases: WAL side-file recreation fails, missing database is created,
or immutable reads silently ignore a still-live WAL. No native sandbox or model.
"""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import traceback
from run_t112_native import closed_fixture_launches


def check(report):
    with tempfile.TemporaryDirectory(prefix='t112-closed-read-', dir='/private/tmp') as raw:
        root = Path(raw)
        output = root / 'contract.json'
        command = ['node', str(Path(__file__).with_name('test_t112_execution.mjs')), str(output)]
        env = dict(os.environ, T112_FIXTURE_PREFIX=str(root / 'policy-'))
        result = subprocess.run(command, env=env, text=True, capture_output=True, timeout=30)
        report['producer'] = dict(argv=command, exit=result.returncode, stdout=result.stdout, stderr=result.stderr)
        assert result.returncode == 0, report['producer']
        policy = json.loads(output.read_text(encoding='utf-8'))
        fixture = Path(policy['fixture'])
        files = sorted(path.name for path in fixture.glob('state.sqlite3*'))
        report['closed_database'] = dict(path=str(fixture / 'state.sqlite3'), files=files,
                                         bytes=(fixture / 'state.sqlite3').stat().st_size)
        assert files == ['state.sqlite3'], 'Producer must close all its SQLite connections'
        records = closed_fixture_launches(fixture)
        assert len(records) == 3
        review = next(row for row in records if row['role'] == 'reviewer')
        assert review['effort_requested'] == 'low'
        assert review['argv'][review['argv'].index('--sandbox') + 1] == 'workspace-write'
        assert Path(review['worktree']).is_dir(), 'Native sandbox probe still needs its candidate directory'
        assert sorted(path.name for path in fixture.glob('state.sqlite3*')) == files
        report['checks'].append('real_closed_node_database_read_without_side_file_writes')
        missing = root / 'missing'; missing.mkdir()
        try:
            closed_fixture_launches(missing)
        except (AssertionError, sqlite3.OperationalError):
            pass
        else:
            raise AssertionError('Missing database must fail')
        assert not (missing / 'state.sqlite3').exists()
        report['checks'].append('missing_database_refused_without_creation')
        live = root / 'live'; live.mkdir()
        db = sqlite3.connect(str(live / 'state.sqlite3'))
        try:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('CREATE TABLE launch_records(data TEXT)')
            db.execute('INSERT INTO launch_records VALUES (?)', (json.dumps({'sentinel': 'uncheckpointed'}),))
            db.commit()
            assert (live / 'state.sqlite3-wal').stat().st_size > 0
            try:
                closed_fixture_launches(live)
            except AssertionError:
                pass
            else:
                raise AssertionError('Live WAL must not be read as an immutable snapshot')
        finally:
            db.close()
        report['checks'].append('live_wal_refused_before_immutable_read')
    report['fixture_removed'] = not root.exists()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--summary', required=True, type=Path)
    args = parser.parse_args()
    assert not args.summary.exists(), 'Preserve earlier evidence'
    report = dict(status='INCOMPLETE', model_calls=0, checks=[], python=sys.version,
                  sqlite=sqlite3.sqlite_version, argv=sys.argv)
    try:
        check(report)
        report['status'] = 'PASS'
    except Exception as error:
        report.update(error=str(error), traceback=traceback.format_exc())
    args.summary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0 if report['status'] == 'PASS' else 1)
