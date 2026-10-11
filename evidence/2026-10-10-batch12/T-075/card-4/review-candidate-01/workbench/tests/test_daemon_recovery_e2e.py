"""Recovery through the real daemon CLI; only this fixture's daemon is killed.

The oracle and Git barriers are reused unchanged from the independent acceptance
suite. Gate assertions use CLI, SQLite and Git readback, never product imports.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest

import test_task_cards_e2e as records
from test_daemon_gates_e2e import DaemonCards
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'acceptance'))
from test_recovery_e2e import GIT_BARRIER, ORACLE_BARRIER, REAL_GIT


class DaemonRecovery(DaemonCards):
    def setUp(self):
        super().setUp()
        self.controls = []
        self.handles = []
        self.addCleanup(self.release_owned_commands)

    def release_owned_commands(self):
        for control in self.controls:
            (control / 'release-all').write_text('abort', encoding='utf-8')
        for handle in self.handles:
            self.finish(handle)

    def start(self, command):
        path = self.root / ('async-' + str(len(self.handles)))
        argv = ['node', str(records.GATE), '--state', str(self.state), command, '--task', self.task]
        with path.with_suffix('.stdout').open('xb') as stdout, path.with_suffix('.stderr').open('xb') as stderr:
            process = subprocess.Popen(argv, cwd=self.root, env=self.env, stdout=stdout, stderr=stderr, start_new_session=True)
        handle = {'process': process, 'argv': argv, 'path': path, 'recorded': False}
        self.handles.append(handle)
        path.with_suffix('.launch.json').write_text(json.dumps({'argv': argv, 'pid': process.pid}) + '\n', encoding='utf-8')
        return handle

    def finish(self, handle):
        handle['process'].wait(timeout=15)
        result = {'argv': handle['argv'], 'exit': handle['process'].returncode,
                  'stdout': handle['path'].with_suffix('.stdout').read_text(encoding='utf-8'),
                  'stderr': handle['path'].with_suffix('.stderr').read_text(encoding='utf-8')}
        if not handle['recorded']:
            records.COMMANDS.append(result)
            handle['recorded'] = True
        return result

    def daemon_pid(self):
        result = self.process(['node', records.GATE, '--state', self.state, 'daemon_status'])
        self.assertEqual(result.returncode, 0, records.COMMANDS[-1])
        return json.loads(result.stdout)['pid']

    def barrier(self, control, handle, prior=()):
        deadline = time.monotonic() + 12
        pid = self.daemon_pid()
        while time.monotonic() < deadline:
            for path in sorted(control.glob('*.entry.json')):
                if path in prior:
                    continue
                value = json.loads(path.read_text(encoding='utf-8'))
                if value['ppid'] == pid:
                    self.assertIsNone(handle['process'].poll(), 'Client must still await the live daemon')
                    return path, value
            if handle['process'].poll() is not None:
                self.fail({'barrier_not_reached': self.finish(handle)})
            time.sleep(0.02)
        self.fail('Barrier deadline; this is not recovery evidence')

    def release(self, entry):
        Path(entry[1]['release']).write_text('abort', encoding='utf-8')
        prefix = entry[0].name[:-len('.entry.json')]
        deadline = time.monotonic() + 12
        while not any((entry[0].parent / (prefix + suffix)).exists() for suffix in ('.done', '.done.json')):
            self.assertLess(time.monotonic(), deadline, 'Owned barrier must finish after release')
            time.sleep(0.02)

    def interrupt(self, handle):
        pid = self.daemon_pid()
        observation = self.process(['/bin/ps', '-o', 'pid=,ppid=,command=', '-p', str(pid)])
        self.assertEqual(observation.returncode, 0)
        self.assertIn(str(records.GATE.parent.parent / 'daemon.ts'), observation.stdout)
        self.assertIn(str(self.state), observation.stdout)
        self.assertEqual(int((self.state / 'daemon.pid').read_text()), pid)
        (self.root / 'fault-owner.json').write_text(json.dumps({'pid': pid, 'signal': 'SIGKILL',
                                                              'ps': observation.stdout}) + '\n', encoding='utf-8')
        os.kill(pid, signal.SIGKILL)
        self._daemon_state = None
        result = self.finish(handle)
        self.assertNotEqual(result['exit'], 0, 'Disconnected client must not report success')
        deadline = time.monotonic() + 10
        while True:
            seen = self.process(['/bin/ps', '-o', 'pid=', '-p', str(pid)])
            self.assertIn(seen.returncode, (0, 1))
            if not seen.stdout.strip():
                break
            self.assertLess(time.monotonic(), deadline, 'Owned daemon must exit before endpoint cleanup')
            time.sleep(0.05)
        refused = self.process(['node', records.GATE, '--state', self.state, 'daemon_start'])
        self.assertEqual(refused.returncode, 1, 'Product must refuse the stale socket')
        self.assertTrue((self.state / 'control.sock').exists())
        for name in ('control.sock', 'daemon.pid'):
            (self.state / name).unlink()
        (self.root / 'endpoint-cleanup.json').write_text(json.dumps({'owner': pid, 'confirmed_exited': True,
                                                                   'removed': ['control.sock', 'daemon.pid']}) + '\n', encoding='utf-8')

    def restart(self):
        env_path = self.env['PATH']
        self.env['PATH'] = str(self.root / 'daemon-git') + os.pathsep + env_path
        try:
            result = self.process(['node', records.GATE, '--state', self.state, 'daemon_start'])
            self.assertEqual(result.returncode, 0, records.COMMANDS[-1])
            self._daemon_state = self.state
        finally:
            self.env['PATH'] = env_path

    def snapshot(self, label):
        value = self.cli('status')['task']
        with sqlite3.connect(f'file:{self.state / "state.sqlite3"}?mode=ro', uri=True) as db:
            stored = json.loads(db.execute('SELECT data FROM tasks WHERE id=?', (self.task,)).fetchone()[0])
            verification = [json.loads(row[0]) for row in db.execute('SELECT data FROM verifications')]
        self.assertEqual(value, stored)
        result = {'task': value, 'verifications': verification, 'events': self.events(),
                  'refs': self.git('show-ref'), 'reflog': self.git('reflog', 'show', '--format=%H', 'refs/heads/main')}
        (self.root / (label + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return result

    def verify_fixture(self):
        control = self.root / 'oracle-barrier'
        control.mkdir(); self.controls.append(control)
        source = 'CONTROL = ' + repr(str(control)) + '\nORACLE_SOURCE = ' + repr(
            "from pathlib import Path; assert Path(sys.argv[1], 'src/value.txt').read_text() == 'worker\\n'") + '\n' + ORACLE_BARRIER
        self.card['completion_conditions'] = [{'argv': [sys.executable, '-I', '-B', '-c', source, '{worktree}']}]
        attempt = self.create()
        self.submit(attempt, self.commit(attempt))
        return attempt, control

    def test_daemon_verify_interruption_and_operation_lock(self):
        attempt, control = self.verify_fixture()
        original = self.start('verify')
        old_entry = self.barrier(control, original)
        before = self.snapshot('verify-before-kill')
        for command in ('verify', 'integrate'):
            self.cli(command, ok=False, error='operation_busy')
        self.interrupt(original)
        self.restart()
        restarted = self.snapshot('verify-after-restart')
        self.assertEqual(restarted['task'], before['task'], 'Startup must not complete or restart verification')
        following = self.start('verify')
        new_entry = self.barrier(control, following, [old_entry[0]])
        during = self.snapshot('verify-new-oracle')
        old_id = before['task']['verification']['verification_id']
        old = next(row for row in during['verifications'] if row['verification_id'] == old_id)
        self.assertEqual(old['state'], 'interrupted')
        self.assertIsNone(old['result']['returncode'])
        self.assertIsNone(old['result']['stdout'])
        self.assertEqual(old['command_intent'], before['task']['verification']['command_intent'])
        self.assertNotEqual(during['task']['verification']['verification_id'], old_id)
        self.assertNotEqual(old_entry[1]['candidate_directory'], new_entry[1]['candidate_directory'])
        self.release(old_entry)
        self.assertIsNone(following['process'].poll(), 'Orphan result must not satisfy the new oracle')
        self.release(new_entry)
        self.assertEqual(self.finish(following)['exit'], 0)
        after = self.snapshot('verify-complete')
        self.assertEqual(after['task']['state'], 'verified')
        self.assertEqual(after['task']['current_attempt']['attempt_id'], attempt['attempt_id'])
        self.assertEqual(self.oid(), self.base)
        self.assertEqual(after['events'][:len(before['events'])], before['events'])

    def integration(self, phase, changed=None):
        attempt = self.create()
        self.submit(attempt, self.commit(attempt))
        verified = self.cli('verify')['verification']
        control = self.root / 'git-barrier'; control.mkdir(); self.controls.append(control)
        (control / 'phase').write_text(phase, encoding='utf-8')
        tools = self.root / 'wrapped-git'; tools.mkdir()
        wrapper = tools / 'git'
        wrapper.write_text('#!' + sys.executable + '\nCONTROL = ' + repr(str(control))
                           + '\nREAL_GIT = ' + repr(REAL_GIT) + '\n' + GIT_BARRIER, encoding='utf-8')
        wrapper.chmod(0o755)
        original = self.start('integrate')
        entry = self.barrier(control, original)
        before = self.snapshot('integrate-before-kill')
        if phase == 'after':
            self.assertTrue(entry[1]['executed_real_git'])
            self.assertEqual(entry[1]['exit_code'], 0)
            self.assertEqual(self.oid(), verified['M'])
        else:
            self.assertEqual(self.oid(), self.base)
        for command in ('verify', 'integrate'):
            self.cli(command, ok=False, error='operation_busy')
        self.interrupt(original)
        (control / 'phase').write_text('record-only', encoding='utf-8')
        self.release(entry)
        if changed == 'external':
            self.git('update-ref', 'refs/heads/main', self.base, verified['M'])
            # X must differ from both G and M. A new host commit provides X.
            (self.repo / 'host.txt').write_text('external X\n', encoding='utf-8')
            self.git('add', 'host.txt'); self.git('commit', '-m', 'External X')
        elif changed == 'deleted':
            self.git('update-ref', '-d', 'refs/heads/main', verified['M'])
        self.restart()
        restarted = self.cli('status')['task']
        self.assertEqual(restarted, before['task'], 'Restart must preserve the unresolved intent')
        if changed:
            refs = self.process(['git', '-C', self.repo, 'show-ref']).stdout
            self.cli('integrate', ok=False, error='needs_reconciliation')
            self.assertEqual(self.cli('status')['task']['integration_intent'], before['task']['integration_intent'])
            self.assertEqual(self.process(['git', '-C', self.repo, 'show-ref']).stdout, refs)
            self.assertNotEqual(self.cli('status')['task']['state'], 'accepted')
            return
        log = self.git('reflog', 'show', '--format=%H', 'refs/heads/main')
        self.cli('integrate')
        after = self.snapshot('integrate-complete')
        self.assertEqual(after['task']['state'], 'accepted')
        self.assertEqual(after['task']['integration_intent']['intent_id'], before['task']['integration_intent']['intent_id'])
        self.assertEqual(self.oid(), verified['M'])
        self.assertEqual(len(after['reflog'].splitlines()) - len(log.splitlines()), 1 if phase == 'before' else 0)
        self.cli('integrate')
        self.assertEqual(self.git('reflog', 'show', '--format=%H', 'refs/heads/main'), after['reflog'])
        self.assertEqual(after['events'][:len(before['events'])], before['events'])

    def test_daemon_before_CAS(self): self.integration('before')
    def test_daemon_after_CAS(self): self.integration('after')
    def test_daemon_external_X(self): self.integration('after', 'external')
    def test_daemon_deleted_ref(self): self.integration('after', 'deleted')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    records.ARTIFACT_ROOT = Path(tempfile.mkdtemp(prefix='a4r-', dir='/tmp'))
    names = [name for name in unittest.defaultTestLoader.getTestCaseNames(DaemonRecovery) if name.startswith('test_daemon_')]
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(DaemonRecovery(name) for name in names))
    record = {'status': 'PASS' if result.wasSuccessful() else 'INCOMPLETE', 'argv': sys.argv,
              'tests_run': result.testsRun, 'failures': result.failures, 'errors': result.errors,
              'commands': records.COMMANDS, 'artifacts': records.ARTIFACTS}
    (args.output / 'run.json').write_text(json.dumps(record, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
    with tarfile.open(args.output / 'artifacts.tar.gz', 'x:gz') as archive:
        archive.add(records.ARTIFACT_ROOT, arcname=records.ARTIFACT_ROOT.name)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
