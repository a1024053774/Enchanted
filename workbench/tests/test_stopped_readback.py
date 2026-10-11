"""Replay the three preserved collection failures without a daemon or model.

The old collector opens the closed original WAL file. The candidate reads its
standalone archive. Required final rows come from the pre-existing shutdown
contract: no acceptance/reclaim, original deadline retained, final event order.
"""
import argparse
import contextlib
import json
from pathlib import Path
import sqlite3
import sys
import tarfile
from types import SimpleNamespace

import test_startup_shutdown_e2e as candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--known-bad', type=Path, required=True)
    parser.add_argument('--failed-run', type=Path, required=True)
    parser.add_argument('--fixture-archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    old = {'__name__': 'known_bad_stopped_collector', '__file__': str(args.known_bad)}
    exec(compile(args.known_bad.read_text(encoding='utf-8'), str(args.known_bad), 'exec'), old)
    failed = json.loads(args.failed_run.read_text(encoding='utf-8'))
    error_tests = {row['test'] for row in failed['errors']}
    observations = []
    for item in failed['artifacts']:
        if item['test'] not in error_tests: continue
        assert item['host_exit'] == 0, 'The preserved writer must have exited'
        method = item['test'].rsplit('.', 1)[-1]
        value = candidate.StartupShutdown(method)
        value.case = out / method; value.case.mkdir()
        value.state = value.case / 'archived-input'; value.state.mkdir()
        # Read only regular DB/WAL members into this replay's new directory.
        # No original /tmp fixture, shared state or credential path is needed.
        prefix = Path(item['root']).name + '/state/'
        with tarfile.open(args.fixture_archive, 'r:gz') as archive:
            available = {member.name: member for member in archive.getmembers()}
            for name in ('state.sqlite3', 'state.sqlite3-wal'):
                member = available.get(prefix + name)
                if member is None:
                    assert name.endswith('-wal'), 'The preserved database member is required'
                    continue
                assert member.isfile(), 'A replay database cannot be a link'
                with (value.state / name).open('xb') as stream:
                    stream.write(archive.extractfile(member).read())
        value.host = SimpleNamespace(poll=lambda: 0)
        source_bytes = {path.name: path.read_bytes() for path in value.state.glob('state.sqlite3*')}
        counterfactual = None
        try:
            old['StartupShutdown'].readback(value, 'known-bad.json')
        except sqlite3.OperationalError as error:
            counterfactual = repr(error)
        assert counterfactual is not None, 'The preserved cold read must reject this known-bad collection path'
        tables = value.readback('candidate.json', archive_after_stop=True)
        states = [json.loads(row['data'])['state'] for row in tables['tasks']]
        if method == 'test_stop_drains_existing_gate_before_final_event':
            assert states == ['ready', 'ready'], states
            events = [{**row, 'data': json.loads(row['data'])} for row in tables['orchestration_events']]
            creates = [row for row in events if row['type'] == 'request_result' and row['data'].get('command') == 'create']
            ended = [row for row in events if row['type'] == 'daemon_stopped']
            assert len(creates) == 2 and len(ended) == 1
            assert ended[0]['seq'] > creates[-1]['seq']
        else:
            assert states == ['claimed'], states
            task = json.loads(tables['tasks'][0]['data'])
            assert task['candidate_commit'] is None and task['current_attempt']['reclaimed'] is False
            runs = [json.loads(row['data']) for row in tables['runs']]
            assert len(runs) == 1 and runs[0]['outcome'] != 'completed'
            expected = 'run_deadline' if method == 'test_stop_during_deadline_cleanup' else 'daemon_stopping'
            assert runs[0]['error'] == expected, runs
            assert len([row for row in tables['events'] if row['type'] == 'run_finished']) == 1
            assert len([row for row in tables['orchestration_events'] if row['type'] == 'pane_exit']) == 1
        assert not any(row['type'] in ('verified', 'integrated') for row in tables['events'])
        for name, before in source_bytes.items():
            assert (value.state / name).read_bytes() == before, 'Original source changed: ' + name
        saved = json.loads((value.case / 'candidate.json').read_text(encoding='utf-8'))
        assert saved['database'] != saved['source_database'] and saved['phase'] == 'after-writer-exit-archive'
        with contextlib.closing(sqlite3.connect(Path(saved['database']).as_uri() + '?mode=ro', uri=True)) as db:
            assert db.execute('PRAGMA journal_mode').fetchone() == ('delete',)
        observations.append({'test': item['test'], 'original_root': item['root'], 'input': str(value.state), 'counterfactual': counterfactual,
            'candidate_readback': str(value.case / 'candidate.json'), 'states': states, 'source_bytes_unchanged': True})
    assert len(observations) == 3, 'All three failed final collectors must be replayed'
    record = {'status': 'PASS', 'argv': sys.argv, 'real_codex_turns': 0, 'observations': observations,
              'scope': '已停止的原失败夹具读回；不把原 INCOMPLETE 改称完整通过'}
    with (out / 'run.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({'status': 'PASS', 'cases': 3, 'real_codex_turns': 0}))


if __name__ == '__main__':
    main()
