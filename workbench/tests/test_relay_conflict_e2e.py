#!/usr/bin/env python3
"""Two explicit deliveries across an ended conflict worker, with one ID.

Real CLI/socket/daemon/Panes/relay/gates/Git/SQLite; scripted PTY and process
facts, no provider. Independent oracles: submitted C2, current native binding,
one gate effect per launch despite file replay, preserved old log, integrated
combined content. The old relay must fail at the second submitted candidate.
"""
import argparse
from contextlib import closing
import io
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
import test_task_cards_e2e as cards

ROOT = Path(__file__).resolve().parents[2]
SOURCE = OUT = None
CONTRACTS = []


class RelayConflict(cards.TaskCardsCLI):
    def setUp(self):
        super().setUp()
        self.control = self.root / 'control'; self.control.mkdir()
        self.host = None; self.host_streams = []
        self.addCleanup(self.cleanup_host)
        self.env = {k: v for k, v in self.env.items() if not k.startswith('CODEX_')}
        self.card['completion_conditions'][0]['argv'][-1] = (
            "from pathlib import Path; assert Path('src/value.txt').read_text() == 'worker+host\\n'")
        ready = self.control / 'ready.json'
        self.host_streams = [(self.root / name).open('xb') for name in ('host.stdout.txt', 'host.stderr.txt')]
        argv = ['node', ROOT / 'workbench/tests/relay_conflict_host.ts', SOURCE, self.state, self.control, ready]
        self.host = subprocess.Popen(list(map(str, argv)), cwd=ROOT, env=self.env,
            stdout=self.host_streams[0], stderr=self.host_streams[1], start_new_session=True)
        self.save('host-launch.json', {'argv': list(map(str, argv)), 'pid': self.host.pid})
        self.wait(lambda: ready.exists(), 'Host did not reach ready')
        self.save_card()
        self.cli('create', '--repo', self.repo, '--branch', 'refs/heads/main', '--card-version', '1', '--project', 'fixture')

    def save(self, name, value):
        with (self.root / name).open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')

    def wait(self, predicate, message):
        deadline = time.monotonic() + 10
        while not predicate():
            if self.host.poll() is not None or time.monotonic() >= deadline:
                raise RuntimeError(message)
            time.sleep(0.02)

    def runtime(self, launch):
        return json.loads((self.control / (launch + '.runtime.json')).read_text(encoding='utf-8'))

    def pane_cli(self, command, *args):
        # pane_* commands take a thread, not a task. The inherited helper is
        # for gate commands and always adds --task, which this CLI rejects.
        p = self.process(['node', cards.GATE, '--state', self.state, command, *args])
        self.assertEqual(p.returncode, 0, cards.COMMANDS[-1])
        value = json.loads(p.stdout)
        self.assertEqual(value['ok'], True, value)
        return value

    def launch(self, attempt):
        launch = self.cli('status')['task']['current_attempt']['runtime_identity']['launch']
        self.pane_cli('pane_release', '--thread', attempt['thread_id'], '--reason', 'controlled foreground process, no provider')
        self.wait(lambda: self.runtime(launch)['turn'] == 1, 'Initial input not written')
        self.assertIsNone(self.cli('status')['task']['current_attempt']['runtime_identity']['native_session'])
        return launch

    def worker_call(self, launch, command, *args, hook=None):
        env = json.loads((self.control / (launch + '.env.json')).read_text(encoding='utf-8'))
        env['CODEX_THREAD_ID'] = self.runtime(launch)['native']
        argv = list(map(str, ['node', cards.GATE, '--state', self.state, command, *args]))
        p = subprocess.run(argv, cwd=self.root, env=env, input=json.dumps(hook) if hook else None,
            capture_output=True, text=True, timeout=20)
        record = {'test': self.id(), 'argv': argv, 'hook': hook, 'cwd': str(self.root),
                  'exit': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
        cards.COMMANDS.append(record)
        self.assertEqual(p.returncode, 0, record)
        return json.loads(p.stdout)

    def stop_turn(self, launch, turn):
        reply = self.worker_call(launch, 'signal', '--launch', launch,
            hook={'hook_event_name': 'Stop', 'session_id': self.runtime(launch)['native'], 'turn_id': 'turn-' + str(turn)})
        self.assertEqual(reply, {})

    def deliver(self, attempt, launch, commit):
        reply = self.worker_call(launch, 'submit', '--task', self.task, '--attempt', attempt['attempt_id'],
            '--session', attempt['session_id'], '--fence', attempt['fence'], '--spec-rev', attempt['spec_rev'],
            '--commit', commit, '--request-id', 'delivery')
        self.assertTrue(reply['queued']); self.assertFalse(reply['delivered'])
        env = json.loads((self.control / (launch + '.env.json')).read_text(encoding='utf-8'))
        requests = Path(env['A2A_REQUEST_DIR'])
        # Two files with the same request while the original turn is active.
        # This exercises replay protection independently of gate turn fencing.
        shutil.copyfile(requests / 'delivery.json', requests / 'copy.json')
        self.stop_turn(launch, 1)
        self.wait(lambda: self.runtime(launch)['turn'] == 2, 'Receipt input not written')
        self.stop_turn(launch, 2)
        self.assertEqual(self.pane_cli('pane_status', '--thread', attempt['thread_id'])['state'], 'idle')
        return self.cli('status')['task']

    def test_new_attempt_same_request_id_delivers_once(self):
        first = self.cli('dispatch', '--runtime-mode', 'workspace-write')['attempt']
        launch1 = self.launch(first)
        c1 = self.commit(first)
        submitted1 = self.deliver(first, launch1, c1)
        self.assertEqual(submitted1['state'], 'submitted')
        self.assertEqual(submitted1['candidate_commit'], c1)
        old_log = Path(self.runtime(launch1)['file']); old_bytes = old_log.read_bytes()
        (self.repo / 'src/value.txt').write_text('host\n', encoding='utf-8')
        self.git('add', 'src/value.txt'); self.git('commit', '-m', 'Independent integration head conflict')
        g = self.oid()
        (self.control / (launch1 + '.exit')).write_text('synthetic PTY has ended\n', encoding='utf-8')
        self.pane_cli('pane_process_info', '--thread', first['thread_id'])
        self.cli('verify', ok=False, error='merge_conflict')
        task = self.cli('status')['task']; second = task['current_attempt']
        self.assertNotEqual(second['attempt_id'], first['attempt_id'])
        self.assertEqual(second['fence'], 2); self.assertEqual(second['base_commit'], g)
        self.assertTrue(second['conflict_source'])
        launch2 = self.launch(second)
        self.assertNotEqual(launch1, launch2)
        self.assertNotEqual(self.runtime(launch1)['native'], self.runtime(launch2)['native'])
        c2 = self.commit(second, {'src/value.txt': 'worker+host\n'})
        submitted2 = self.deliver(second, launch2, c2)
        self.save('second-delivery.json', {'first': first, 'second': second, 'C1': c1, 'G': g, 'C2': c2, 'task': submitted2})
        contract = {'name': 'new_attempt_delivery', 'expected': 'submitted', 'actual': submitted2['state'],
                    'pass': submitted2['state'] == 'submitted'}
        CONTRACTS.append(contract)
        self.assertTrue(contract['pass'], 'A new attempt must accept its own delivery ID: ' + repr(contract))
        self.assertEqual(submitted2['candidate_commit'], c2)
        self.assertEqual(submitted2['current_attempt']['runtime_identity']['native_session'], self.runtime(launch2)['native'])
        self.assertEqual(old_log.read_bytes(), old_bytes, 'The earlier root rollout is immutable')
        with closing(sqlite3.connect(self.state.resolve().joinpath('state.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
            intents = db.execute('SELECT launch,request_id FROM relay_requests ORDER BY created_at').fetchall()
            outcomes = db.execute('SELECT count(*) FROM relay_results').fetchone()[0]
        self.assertEqual(intents, [(launch1, 'delivery'), (launch2, 'delivery')]); self.assertEqual(outcomes, 2)
        submitted = [event for event in self.events() if event['type'] == 'submitted']
        self.assertEqual(len(submitted), 2, 'Duplicate files and Stops cannot invoke submit again')
        self.cli('verify'); self.cli('integrate'); self.cli('reclaim')
        self.assertEqual(self.oid(), c2)
        self.assertEqual((self.repo / 'src/value.txt').read_text(encoding='utf-8'), 'worker+host\n')
        self.assertEqual(self.git('status', '--porcelain'), '')
        self.assertEqual(self.oid(ref='refs/a2a/attempts/' + self.task + '/a1'), c1)
        self.assertEqual(self.oid(ref='refs/a2a/attempts/' + self.task + '/a2'), c2)
        self.save('accepted-readback.json', {'task': self.cli('status')['task'], 'events': self.events(),
            'intents': intents, 'outcomes': outcomes, 'old_rollout_preserved': True, 'head': self.oid()})

    def cleanup_host(self):
        if self.host is not None:
            if self.host.poll() is None:
                self.process(['node', cards.GATE, '--state', self.state, 'daemon_stop'])
                try:
                    self.host.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.host.terminate(); self.host.wait(timeout=10)
                    raise RuntimeError('Owned fixture host needed termination; not a passing cleanup')
            self.assertEqual(self.host.returncode, 0, 'Owned fixture host exited with an error')
        for stream in self.host_streams:
            stream.close()
        for file in self.control.glob('*.env.json'):
            env = json.loads(file.read_text(encoding='utf-8'))
            shutil.copytree(env['A2A_REQUEST_DIR'], self.root / ('requests-' + env['A2A_LAUNCH']))


def main():
    global SOURCE, OUT
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expect-red', action='store_true')
    args = parser.parse_args(); SOURCE = args.source.resolve(); OUT = args.output.resolve()
    OUT.mkdir(parents=True, exist_ok=False)
    cards.GATE = SOURCE / 'workbench/src/gates/cli.ts'
    cards.ARTIFACT_ROOT = Path(tempfile.mkdtemp(prefix='r77-', dir='/tmp'))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
        unittest.TestSuite([RelayConflict('test_new_attempt_same_request_id_delivers_once')]))
    (OUT / 'unittest.txt').write_text(stream.getvalue(), encoding='utf-8')
    (OUT / 'commands.json').write_text(json.dumps(cards.COMMANDS, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    red = (len(result.failures) == 1 and not result.errors and not result.skipped and
           len(CONTRACTS) == 1 and not CONTRACTS[0]['pass'])
    with tarfile.open(OUT / 'fixtures.tar.gz', 'x:gz') as archive:
        archive.add(cards.ARTIFACT_ROOT, arcname=cards.ARTIFACT_ROOT.name)
    with tarfile.open(OUT / 'sources.tar.gz', 'x:gz') as archive:
        for folder in ('workbench/src', 'workbench/hooks'):
            archive.add(SOURCE / folder, arcname=folder)
        for name in ('test_relay_conflict_e2e.py', 'relay_conflict_host.ts', 'test_task_cards_e2e.py'):
            archive.add(ROOT / 'workbench/tests' / name, arcname='workbench/tests/' + name)
    report = {'status': 'PASS' if not args.expect_red and result.wasSuccessful() else 'INCOMPLETE',
        'red_confirmed': red if args.expect_red else None, 'argv': sys.argv, 'source': str(SOURCE),
        'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
        'contracts': CONTRACTS,
        'real_codex_turns': 0, 'scope': 'CLI/Panes/relay/gates/Git; controlled PTY/process boundary', 'artifacts': cards.ARTIFACTS}
    (OUT / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if (red if args.expect_red else result.wasSuccessful()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
