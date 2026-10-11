"""Same runtime owner across receipt turns; reject different runtime owners.

The real CLI, socket, daemon handler, gates, Git and SQLite are exercised.
Runtime facts are controlled externally and are not real PTY/provider evidence.
"""
import argparse
import contextlib
import datetime
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest

import test_task_cards_e2e as previous

SOURCE = None
OUT = None
CHECK_CONSISTENCY = False


class MultiTurn(previous.TaskCardsCLI):
    def setUp(self):
        super().setUp()
        self.card['executor'] = {'cli': 'Codex', 'model': 'gpt-6.1-sol', 'effort': 'xhigh'}
        self.control = self.root / 'control'; self.control.mkdir()
        self.runtime_file = self.control / 'runtime.json'
        self.runtime_file.write_text(json.dumps({'threads': {}, 'closes': []}) + '\n', encoding='utf-8')
        ready = self.root / 'ready.json'
        self.artifact = previous.ARTIFACTS[-1]
        self.host_stdout = (self.root / 'host.stdout.txt').open('xb')
        self.host_stderr = (self.root / 'host.stderr.txt').open('xb')
        argv = ['node', Path(__file__).with_name('multiturn_identity_host.ts'), SOURCE, self.state, self.control, ready]
        self.host = subprocess.Popen(list(map(str, argv)), env=self.env, stdout=self.host_stdout,
                                     stderr=self.host_stderr, start_new_session=True)
        self.addCleanup(self.stop_host)
        end = time.monotonic() + 10
        while not ready.exists():
            if self.host.poll() is not None or time.monotonic() > end:
                raise RuntimeError('Isolated host did not become ready; inspect its stderr')
            time.sleep(0.05)
        self.artifact.update(host=json.loads(ready.read_text()), runtime=str(self.runtime_file))
        self.run_process = None

    def capture_readback(self):
        database = (self.state / 'state.sqlite3').resolve()
        if not database.is_file():
            raise RuntimeError('Live fixture database is missing before host stop')
        with contextlib.closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as db:
            db.row_factory = sqlite3.Row
            with db:
                tables = {table: [dict(row) for row in db.execute('SELECT * FROM ' + table)]
                          for table in ('tasks', 'attempts', 'verifications', 'runs', 'events')}
        snapshot = {'test': self.artifact['test'], 'database': str(database),
                    'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'phase': 'before-host-stop', 'host_pid': self.host.pid, 'tables': tables}
        path = OUT / 'readbacks' / (self.root.name + '.json')
        with path.open('x', encoding='utf-8') as stream:
            json.dump(snapshot, stream, ensure_ascii=False, indent=2); stream.write('\n')
        self.artifact['state_readback'] = str(path)
        if CHECK_CONSISTENCY and self._testMethodName == 'test_reclaim_after_receipt_turn':
            frozen = OUT / ('databases-' + self.root.name)
            backup = self.process(['node', Path(__file__).with_name('snapshot_state.ts'), self.state, frozen])
            if backup.returncode:
                raise RuntimeError('Cannot preserve live fixture databases through SQLite backup')
            self.artifact['database_snapshot'] = str(frozen)
            report_path = OUT / ('consistency-' + self.root.name + '.json')
            result = self.process(['node', SOURCE / 'workbench/src/stateConsistency.ts', '--state', self.state,
                                   '--output', report_path])
            if result.returncode not in (0, 1) or not report_path.is_file():
                raise RuntimeError('Consistency diagnostic failed without its report')
            report = json.loads(report_path.read_text(encoding='utf-8'))
            self.artifact['consistency_report'] = str(report_path)
            self.artifact['consistency_status'] = report['status']

    def stop_host(self):
        try:
            if self.host.poll() is None:
                try:
                    if getattr(self, 'run_process', None) and self.run_process.poll() is None:
                        self.run_process.communicate(timeout=30)
                    # Keep the live writer/WAL available. Persist literal rows
                    # outside the fixture before daemon_stop closes SQLite.
                    self.capture_readback()
                finally:
                    stopped = self.process(['node', previous.GATE, '--state', self.state, 'daemon_stop'])
                    self.assertEqual(stopped.returncode, 0, previous.COMMANDS[-1])
                    self.host.wait(timeout=10)
            self.assertEqual(self.host.returncode, 0, 'Owned host shutdown must succeed')
        finally:
            self.host_stdout.close(); self.host_stderr.close()

    def create_task(self):
        self.save_card()
        self.cli('create', '--repo', self.repo, '--branch', 'refs/heads/main', '--card-version', '1', '--project', 'fixture')

    def change_live(self, thread, **changes):
        value = json.loads(self.runtime_file.read_text(encoding='utf-8'))
        value['threads'][thread].update(changes)
        temporary = self.control / 'update.json'
        temporary.write_text(json.dumps(value) + '\n', encoding='utf-8')
        temporary.replace(self.runtime_file)
        return value['threads'][thread]

    def original_live(self, a):
        return json.loads(self.runtime_file.read_text())['threads'][a['thread_id']]

    def delivery(self):
        self.create_task()
        a = self.cli('dispatch', '--runtime-mode', 'workspace-write')['attempt']
        c = self.commit(a)
        self.submit(a, c)
        self.change_live(a['thread_id'], turn='receipt-B', running=False)
        return a, c

    def test_reclaim_after_receipt_turn(self):
        a, c = self.delivery()
        self.cli('verify', '--attempt', a['attempt_id'])
        self.cli('integrate', '--attempt', a['attempt_id'])
        self.cli('reclaim', '--attempt', a['attempt_id'])
        current = self.cli('status')['task']
        self.assertEqual(current['candidate_commit'], c)
        self.assertEqual(current['current_attempt']['turn_id'], 'delivery-A', 'Receipt cannot change the delivery binding')
        self.assertTrue(current['current_attempt']['reclaimed'])
        self.assertEqual(json.loads(self.runtime_file.read_text())['closes'], [a['thread_id']])

    def test_run_after_receipt_turn(self):
        self.create_task()
        argv = ['node', previous.GATE, '--state', self.state, 'run', '--task', self.task,
                '--runtime-mode', 'workspace-write', '--wait-seconds', '15']
        self.run_process = subprocess.Popen(list(map(str, argv)), cwd=self.root, env=self.env,
                                            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            start_new_session=True)
        until = time.monotonic() + 8
        while True:
            task = self.cli('status')['task']
            if task['state'] == 'claimed' and task['current_attempt'].get('turn_id') == 'delivery-A':
                break
            if self.run_process.poll() is not None or time.monotonic() > until:
                raise RuntimeError('Run failed before reaching its independently observed dispatch boundary')
            time.sleep(0.05)
        a = task['current_attempt']; c = self.commit(a)
        # Keep the external worker running until the receipt turn is supplied.
        # A fast verify/integrate still cannot reclaim before this transition.
        self.submit(a, c)
        self.change_live(a['thread_id'], turn='receipt-B', running=False)
        stdout, stderr = self.run_process.communicate(timeout=30)
        previous.COMMANDS.append({'test': self.id(), 'argv': list(map(str, argv)), 'cwd': str(self.root),
                                  'exit': self.run_process.returncode, 'stdout': stdout, 'stderr': stderr})
        reply = json.loads(stdout)
        self.assertEqual(self.run_process.returncode, 0, reply)
        self.assertEqual(reply['run']['outcome'], 'completed', reply)
        self.assertTrue(reply['run']['reclaimed'], reply)
        self.assertEqual(reply['task']['current_attempt']['turn_id'], 'delivery-A')
        self.assertEqual(json.loads(self.runtime_file.read_text())['closes'], [a['thread_id']])

    def foreign(self, field, replacement):
        self.create_task()
        a = self.cli('dispatch', '--runtime-mode', 'workspace-write')['attempt']
        live = self.original_live(a)
        # Keep the turn identical, so a turn-only identity check cannot pass.
        identity = {**live['runtime_identity'], field: replacement}
        self.change_live(a['thread_id'], runtime_identity=identity, running=False)
        self.cli('reclaim', '--attempt', a['attempt_id'], ok=False, error='identity_conflict')
        self.assertEqual(json.loads(self.runtime_file.read_text())['closes'], [])
        self.assertEqual(self.oid(ref='refs/heads/main'), self.base)
        self.assertTrue(any(e['type'] == 'rejected' and e['details']['error'] == 'identity_conflict' for e in self.events()))

    def test_other_native_session_rejected(self):
        self.foreign('native_session', 'another-native-session')

    def test_other_leader_rejected(self):
        self.foreign('leader_pid', 12002)


def read_state(artifacts):
    snapshots = []
    for item in artifacts:
        snapshot = json.loads(Path(item['state_readback']).read_text(encoding='utf-8'))
        expected_database = str((Path(item['root']) / 'state/state.sqlite3').resolve())
        if (snapshot['test'] != item['test'] or snapshot['database'] != expected_database or
                snapshot['phase'] != 'before-host-stop'):
            raise RuntimeError('Persisted readback does not belong to this test and fixture')
        snapshots.append(snapshot)
    return snapshots


def main():
    global SOURCE, OUT, CHECK_CONSISTENCY
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', choices=['all', 'reclaim', 'run', 'native', 'leader'], default='all')
    parser.add_argument('--check-consistency', action='store_true')
    args = parser.parse_args()
    CHECK_CONSISTENCY = args.check_consistency
    SOURCE = args.source.resolve(); OUT = args.output.resolve(); OUT.mkdir(parents=True, exist_ok=False)
    (OUT / 'readbacks').mkdir()
    previous.GATE = SOURCE / 'workbench/src/gates/cli.ts'
    previous.ARTIFACT_ROOT = Path(tempfile.mkdtemp(prefix='m76-', dir='/tmp'))
    methods = {'reclaim': 'test_reclaim_after_receipt_turn', 'run': 'test_run_after_receipt_turn',
               'native': 'test_other_native_session_rejected', 'leader': 'test_other_leader_rejected'}
    selected = list(methods.values()) if args.case == 'all' else [methods[args.case]]
    with (OUT / 'stdout.txt').open('x', encoding='utf-8') as stdout, (OUT / 'stderr.txt').open('x', encoding='utf-8') as stderr:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(MultiTurn(n) for n in selected))
    record = {'status': 'PASS' if result.wasSuccessful() else 'INCOMPLETE', 'source': str(SOURCE),
              'argv': sys.argv, 'tests_run': result.testsRun, 'failures': len(result.failures),
              'errors': len(result.errors), 'skipped': len(result.skipped),
              'failure_text': [{'test': test.id(), 'text': text} for test, text in result.failures],
              'error_text': [{'test': test.id(), 'text': text} for test, text in result.errors],
              'commands': previous.COMMANDS, 'artifacts': previous.ARTIFACTS,
              'real_codex_turns': 0, 'evidence_layer': 'real gates and transport with controlled external runtime'}
    # A collection error must not erase the completed business assertions or
    # their exact command replies. Preserve this record before postprocessing.
    with (OUT / 'test-result.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
    try:
        record['readbacks'] = read_state(previous.ARTIFACTS)
        with tarfile.open(OUT / 'fixtures.tar.gz', 'x:gz') as archive:
            archive.add(previous.ARTIFACT_ROOT, arcname=previous.ARTIFACT_ROOT.name)
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        record.update(status='INCOMPLETE', collection_error=repr(error))
    with (OUT / 'run.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({key: record[key] for key in ('status', 'tests_run', 'failures', 'errors', 'skipped')}))
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
