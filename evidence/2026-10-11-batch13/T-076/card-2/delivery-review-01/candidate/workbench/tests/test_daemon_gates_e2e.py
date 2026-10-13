#!/usr/bin/env python3
"""Re-run card-2 assertions through the daemon CLI, with only lifecycle adaptation."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
import test_task_cards_e2e as previous
from legacy_quality_driver import QualityDriver, prepare_review_control


class DaemonCards(previous.TaskCardsCLI):
    def setUp(self):
        if getattr(self, '_daemon_state', None):
            self.stop_daemon()
        super().setUp()
        # The old non-fast-forward counterexample installs a Git fault after
        # claim. Keep that evidence injection in the daemon's inherited PATH.
        router = self.root / 'daemon-git'; router.mkdir()
        actual = shutil.which('git'); fault = self.root / 'wrapped-git/git'
        executable = router / 'git'
        executable.write_text('#!' + sys.executable + '\nimport os,sys\n'
                              + 'target=' + repr(str(fault)) + '\n'
                              + 'if not os.path.isfile(target): target=' + repr(actual) + '\n'
                              + 'os.execv(target,[target]+sys.argv[1:])\n', encoding='utf-8')
        executable.chmod(0o755)
        original = self.env['PATH']
        self.env['PATH'] = str(router) + os.pathsep + original
        boundary = self.root / 'worker-control'; boundary.mkdir()
        (boundary / 'store.json').write_text(json.dumps(dict(threads={}, next=0, scenario='done-no-submit', prompts=[], closes=[], archived={})) + '\n', encoding='utf-8')
        self.worker_control = boundary
        control = prepare_review_control(self.root)
        self.quality = QualityDriver(previous.GATE, self.state, control, self.env)
        self.integration_score = None
        ready = self.root / 'daemon-ready.json'
        self.host_stdout = (self.root / 'host.stdout').open('xb'); self.host_stderr = (self.root / 'host.stderr').open('xb')
        argv = ['node', Path(__file__).with_name('daemon_acceptance_host.ts'), self.state, boundary,
                ready, previous.ROOT / 'workbench/src/gates/core.ts', control]
        self.host = subprocess.Popen(list(map(str, argv)), env=self.env, stdout=self.host_stdout,
                                     stderr=self.host_stderr, start_new_session=True)
        self.env['PATH'] = original
        until = time.monotonic() + 10
        while not ready.exists():
            if self.host.poll() is not None or time.monotonic() >= until:
                raise RuntimeError('Controlled daemon host failed to start.')
            time.sleep(0.03)
        previous.ARTIFACTS[-1].update(evidence_layer='real daemon/Git; controlled external actors',
                                    host_argv=list(map(str, argv)), quality_driver=str(control / 'driver.jsonl'))
        self._daemon_state = self.state
        self.addCleanup(self.stop_daemon)

    def stop_daemon(self):
        state = getattr(self, '_daemon_state', None)
        if state is None: return
        p = self.process(['node', previous.GATE, '--state', state, 'daemon_stop'])
        self._daemon_state = None
        self.assertEqual(p.returncode, 0, previous.COMMANDS[-1])
        until = time.monotonic() + 10
        while (state / 'daemon.pid').exists() and time.monotonic() < until: time.sleep(0.05)
        self.assertFalse((state / 'daemon.pid').exists(), 'own daemon must stop before archiving')
        self.host.wait(timeout=10)
        self.host_stdout.close(); self.host_stderr.close()

    def cli(self, command, *args, **kwargs):
        if command == 'create' and '--project' not in args:
            args = (*args, '--project', 'fixture')
        if command == 'integrate' and self.integration_score and '--score-file' not in args:
            args = (*args, '--score-file', self.integration_score)
        result = super().cli(command, *args, **kwargs)
        if result['ok'] and command in ('claim', 'dispatch'):
            self.quality.preparation(self.task, result['attempt'], '手工 claim' if command == 'claim' else '受控 dispatch')
        if result['ok'] and command == 'verify' and result['task']['state'] == 'reviewing':
            self.quality.complete_review(self.task)
        return result

    def dispatch_candidate_attempt(self):
        a = self.cli('dispatch', '--runtime-mode', 'approval-required')['attempt']
        self.integration_score = self.quality.score_file(a)
        return a

    def managed_trailers(self, attempt):
        rows = [json.loads(line) for line in (self.worker_control / 'worker-creations.jsonl').read_text(encoding='utf-8').splitlines()]
        row = next(row for row in rows if row['attempt'] == attempt['attempt_id'])
        return {'Tool': row['cli_version'], 'Model': row['model'], 'Effort': row['effort'],
                'Native-Session': 'native-turn:' + attempt['thread_id'], 'Launch': row['id']}

    def test_new_tables_are_append_only(self):
        self.create()
        with sqlite3.connect(self.state / 'state.sqlite3') as db:
            for table, sql in [
                ('launch_records', "INSERT INTO launch_records VALUES ('fixture-launch','task','attempt','{}')"),
                ('dispatch_records', "INSERT INTO dispatch_records(id,launch,data) VALUES ('fixture-dispatch','fixture-launch','{}')"),
                ('orchestration_events', "INSERT INTO orchestration_events(time,type,data) VALUES ('time','fixture','{}')")]:
                db.execute(sql); db.commit()
                before = db.execute('SELECT * FROM ' + table).fetchall()
                for statement in ('UPDATE ' + table + " SET data='changed'", 'DELETE FROM ' + table):
                    with self.assertRaises(sqlite3.IntegrityError): db.execute(statement)
                    db.rollback()
                    self.assertEqual(db.execute('SELECT * FROM ' + table).fetchall(), before)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    previous.ARTIFACT_ROOT = Path(tempfile.mkdtemp(prefix='a2adc-', dir='/tmp'))
    names = unittest.defaultTestLoader.getTestCaseNames(DaemonCards)
    result = unittest.TextTestRunner(verbosity=2, failfast=True).run(unittest.TestSuite(DaemonCards(name) for name in names))
    record = {'status': 'PASS' if result.wasSuccessful() else 'INCOMPLETE', 'command': sys.argv,
              'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'failure_text': [text for _, text in result.failures], 'error_text': [text for _, text in result.errors],
              'commands': previous.COMMANDS, 'artifacts': previous.ARTIFACTS}
    (args.output / 'run.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with tarfile.open(args.output / 'artifacts.tar.gz', 'w:gz') as archive:
        archive.add(previous.ARTIFACT_ROOT, arcname=previous.ARTIFACT_ROOT.name)
    print(json.dumps({k: record[k] for k in ('status', 'tests_run', 'failures', 'errors')}))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
