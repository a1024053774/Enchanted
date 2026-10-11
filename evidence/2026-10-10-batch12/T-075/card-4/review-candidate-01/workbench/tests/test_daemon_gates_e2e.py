#!/usr/bin/env python3
"""Re-run card-2 assertions through the daemon CLI, with only lifecycle adaptation."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tarfile
import tempfile
import time
import unittest
import test_task_cards_e2e as previous


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
        p = self.process(['node', previous.GATE, '--state', self.state, 'daemon_start'])
        self.env['PATH'] = original
        self.assertEqual(p.returncode, 0, previous.COMMANDS[-1])
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

    def cli(self, command, *args, **kwargs):
        if command == 'create' and '--project' not in args:
            args = (*args, '--project', 'fixture')
        return super().cli(command, *args, **kwargs)

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
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(DaemonCards(name) for name in names))
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
