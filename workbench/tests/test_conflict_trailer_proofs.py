#!/usr/bin/env python3
"""C2 with extra trailers is refused; the same C2 code with hook trailers integrates.

Public CLI/socket/daemon/gates/Git/production hook are real. Only PTY callbacks
and process facts are supplied by the existing isolated-runtime fixture pattern.
Two independent scenes keep candidates immutable: each reproduces the ended
conflict worker and fence-2 attempt, using identical r3 C2 source bytes.
"""
import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
import test_task_cards_e2e as cards
import test_relay_conflict_e2e as relay
from command_evidence import CommandLog

ROOT = Path(__file__).resolve().parents[2]
SOURCE = OUT = INPUT = None
CONTRACTS = []
KEYS = ('Task', 'Attempt', 'Session', 'Role', 'Tool', 'Model', 'Effort', 'Native-Session', 'Launch')
ORACLE = '''import importlib.util,pathlib
root=pathlib.Path.cwd()
spec=importlib.util.spec_from_file_location("independent_summary",root/"src/summary.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
for values,expected in [([], {"count":0,"total_ms":0,"mean_ms":None,"unit":"ms"}),
                       ([2,5,8], {"count":3,"total_ms":15,"mean_ms":5.0,"unit":"ms"}),
                       ([-4,1], {"count":2,"total_ms":-3,"mean_ms":-1.5,"unit":"ms"}),
                       ([0], {"count":1,"total_ms":0,"mean_ms":0.0,"unit":"ms"})]:
    assert module.summarize(values)==expected,(values,expected,module.summarize(values))
assert (root/"host-policy.txt").read_bytes()==b"unit=ms; source=host\\n"
'''


class ConflictTrailerProofs(relay.RelayConflict):
    def setUp(self):
        self.case = OUT / self._testMethodName; self.case.mkdir()
        self.command_log = CommandLog(self.case)
        cards.TaskCardsCLI.setUp(self)
        self.control = self.root / 'control'; self.control.mkdir()
        self.host = None; self.host_streams = []
        self.addCleanup(self.cleanup_host)
        self.env = {k: v for k, v in self.env.items() if not k.startswith('CODEX_')}
        (self.repo / 'src/summary.py').write_text(INPUT['sources']['base'], encoding='utf-8')
        (self.repo / 'host-policy.txt').write_text('host baseline\n', encoding='utf-8')
        (self.repo / '.gitignore').write_text('__pycache__/\n*.pyc\n', encoding='utf-8')
        self.git('add', 'src/summary.py', 'host-policy.txt', '.gitignore')
        self.git('commit', '-m', 'Independent r3-shaped baseline')
        self.base = self.oid()
        cards.ARTIFACTS[-1].update(base=self.base, input_refs=INPUT['refs'], case=str(self.case))
        self.card['paths'] = {'allow': ['src/summary.py'], 'deny': []}
        self.card['goal'] = '核对 r3 同一份 C2 代码的尾注拒收与验收集成；不调用模型'
        self.card['executor'] = {'cli': 'Codex', 'model': 'gpt-6.1-sol', 'effort': 'xhigh'}
        self.card['completion_conditions'] = [{'argv': [sys.executable, '-I', '-B', '-c', ORACLE]}]
        ready = self.control / 'ready.json'
        self.host_streams = [(self.case / name).open('xb') for name in ('host.stdout.txt', 'host.stderr.txt')]
        argv = ['node', ROOT / 'workbench/tests/trailer_conflict_host.ts', SOURCE, self.state, self.control, ready]
        self.host = subprocess.Popen(list(map(str, argv)), cwd=ROOT, env=self.env,
            stdout=self.host_streams[0], stderr=self.host_streams[1], start_new_session=True)
        self.save('host-launch.json', {'argv': list(map(str, argv)), 'pid': self.host.pid})
        self.wait(lambda: ready.exists(), 'Controlled host not ready')
        self.save_card()
        self.cli('create', '--repo', self.repo, '--branch', 'refs/heads/main', '--card-version', '1', '--project', 'fixture')

    def save(self, name, value):
        with (self.case / name).open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')

    def process(self, argv, cwd=None):
        result = self.command_log.run(argv, cwd=cwd or self.root, env=self.env, timeout=90)
        cards.COMMANDS.append({'test': self.id(), **result.evidence})
        return result

    def raw_cli(self, command, *args):
        result = self.process(['node', cards.GATE, '--state', self.state, command, '--task', self.task, *args])
        self.assertIn(result.returncode, (0, 1), result.evidence)
        value = json.loads(result.stdout)
        self.assertEqual(value['ok'], result.returncode == 0)
        return result, value

    def commit_by_hook(self, attempt, launch, source, *, extra=False):
        workspace = Path(attempt['workspace'])
        (workspace / 'src/summary.py').write_text(source, encoding='utf-8')
        self.git('add', 'src/summary.py', cwd=workspace)
        supplied = json.loads((self.control / (launch + '.env.json')).read_text(encoding='utf-8'))
        env = {**self.env, **supplied, 'CODEX_THREAD_ID': self.runtime(launch)['native']}
        argv = ['git', 'commit', '-m', 'Controlled summary rework']
        if extra:
            argv += ['--trailer', 'A2A-Fence: ' + str(attempt['fence']), '--trailer', 'A2A-Spec-Rev: 1']
        result = self.command_log.run(argv, cwd=workspace, env=env, timeout=20)
        cards.COMMANDS.append({'test': self.id(), **result.evidence})
        self.assertEqual(result.returncode, 0, result.evidence)
        commit = self.oid(workspace)
        message = self.git('show', '-s', '--format=%B', commit)
        expected = {'Task': self.task, 'Attempt': attempt['attempt_id'], 'Session': attempt['session_id'],
            'Role': 'worker', 'Tool': 'codex-cli 0.162.1', 'Model': 'gpt-6.1-sol', 'Effort': 'xhigh',
            'Native-Session': self.runtime(launch)['native'], 'Launch': launch}
        actual = {}
        for line in message.splitlines():
            if line.startswith('A2A-'):
                key, value = line[4:].split(': ', 1); actual.setdefault(key, []).append(value)
        self.assertEqual({key: actual.get(key) for key in KEYS}, {key: [expected[key]] for key in KEYS})
        extras = {key: value for key, value in actual.items() if key not in KEYS}
        self.assertEqual(extras, {'Fence': ['2'], 'Spec-Rev': ['1']} if extra else {})
        self.assertEqual(sum(map(len, actual.values())), 11 if extra else 9)
        self.save(('bad' if extra else 'hook') + '-a' + str(attempt['fence']) + '-commit.json', {'commit': commit, 'argv': argv,
            'message': message, 'expected': expected, 'actual': actual, 'code': source,
            'hook': env['GIT_CONFIG_VALUE_0'], 'CODEX_HOME': env['CODEX_HOME'], 'CODEX_THREAD_ID': env['CODEX_THREAD_ID']})
        return commit

    def prepare_rework(self, *, extra):
        first = self.cli('dispatch', '--runtime-mode', 'workspace-write')['attempt']
        launch1 = self.launch(first)
        c1 = self.commit_by_hook(first, launch1, INPUT['sources']['C1'])
        submitted = self.deliver(first, launch1, c1)
        self.assertEqual((submitted['state'], submitted['candidate_commit']), ('submitted', c1))
        old_log = Path(self.runtime(launch1)['file']); old_bytes = old_log.read_bytes()
        (self.repo / 'src/summary.py').write_text(INPUT['sources']['G'], encoding='utf-8')
        (self.repo / 'host-policy.txt').write_text(INPUT['host_policy'], encoding='utf-8')
        self.git('add', 'src/summary.py', 'host-policy.txt')
        self.git('commit', '-m', 'Independent concurrent host unit policy')
        g = self.oid()
        (self.control / (launch1 + '.exit')).write_text('controlled CLI has ended\n', encoding='utf-8')
        self.pane_cli('pane_process_info', '--thread', first['thread_id'])
        conflict = self.cli('verify', ok=False, error='merge_conflict')
        self.assertEqual(conflict['details']['state'], 'merge_failed')
        self.assertEqual(conflict['details']['conflict']['files'], ['src/summary.py'])
        second = self.cli('status')['task']['current_attempt']
        self.assertNotEqual(second['attempt_id'], first['attempt_id'])
        self.assertEqual(second['fence'], 2); self.assertEqual(second['base_commit'], g)
        self.assertEqual(second['conflict_source'], conflict['details']['verification_id'])
        launch2 = self.launch(second)
        c2 = self.commit_by_hook(second, launch2, INPUT['sources']['C2'], extra=extra)
        submitted = self.deliver(second, launch2, c2)
        self.assertEqual((submitted['state'], submitted['candidate_commit']), ('submitted', c2))
        self.assertEqual(old_log.read_bytes(), old_bytes)
        self.save('scene.json', {'first': first, 'second': second, 'C1': c1, 'G': g, 'C2': c2,
            'conflict': conflict, 'C2_source': INPUT['sources']['C2'], 'old_rollout_preserved': True})
        return second, c2, g

    def test_extra_trailers_refused(self):
        attempt, c2, g = self.prepare_rework(extra=True)
        result, reply = self.raw_cli('verify')
        contract = {'name': 'verify-refuses-extra-C2-trailers', 'expected': {'exit': 1, 'ok': False, 'error': 'invalid_trailers'},
                    'actual': {'exit': result.returncode, 'ok': reply['ok'], 'error': reply.get('error')}}
        contract['pass'] = contract['actual'] == contract['expected']
        CONTRACTS.append(contract)
        self.save('verify-reply.json', reply)
        self.assertTrue(contract['pass'], 'Spec section 8 closed trailer contract: ' + repr(contract))
        events = self.events()
        check = [e for e in events if e['type'] == 'trailer_check' and e['details']['commit'] == c2]
        self.assertEqual(len(check), 1)
        self.assertFalse(check[0]['details']['passed']); self.assertEqual(check[0]['details']['error'], 'invalid_trailers')
        self.assertEqual(set(check[0]['details']['trailers']), {key.lower() for key in KEYS} | {'fence', 'spec-rev'})
        status = self.cli('status')['task']; v = status['verification']
        self.assertEqual((status['state'], v['state']), ('submitted', 'failed'))
        self.assertTrue(any(e['type'] == 'rejected' and e['details']['error'] == 'invalid_trailers' for e in events))
        self.assertTrue(any(e['type'] == 'completion_check' and e['details']['verification_id'] == v['verification_id'] and e['details']['passed'] for e in events))
        self.cli('integrate', ok=False, error='not_verified')
        self.assertEqual(self.oid(), g)
        self.assertFalse(any(e['type'] == 'integrated' and e['attempt'] == attempt['attempt_id'] for e in self.events()))
        self.save('proof.json', {'status': 'PASS', 'claim': 'Unsupported extra C2 trailers are rejected',
            'C2': c2, 'G': g, 'verify': reply, 'task': status, 'events': self.events()})

    def test_hook_trailers_integrate(self):
        attempt, c2, g = self.prepare_rework(extra=False)
        v = self.cli('verify')['verification']
        self.assertEqual((v['state'], v['C'], v['G'], v['M']), ('passed', c2, g, c2))
        self.cli('integrate'); self.cli('reclaim')
        self.assertEqual(self.oid(), c2)
        self.assertEqual((self.repo / 'src/summary.py').read_text(encoding='utf-8'), INPUT['sources']['C2'])
        self.assertEqual((self.repo / 'host-policy.txt').read_text(encoding='utf-8'), INPUT['host_policy'])
        self.assertEqual(self.git('status', '--porcelain'), '')
        self.assertEqual(self.oid(ref='refs/a2a/attempts/' + self.task + '/a2'), c2)
        events = self.events()
        self.assertEqual(len([e for e in events if e['type'] == 'integrated' and e['attempt'] == attempt['attempt_id']]), 1)
        self.assertTrue(any(e['type'] == 'trailer_check' and e['details']['commit'] == c2 and e['details']['passed'] for e in events))
        self.save('proof.json', {'status': 'PASS', 'claim': 'Same C2 code, nine hook-generated trailers, verified and integrated',
            'C2': c2, 'G': g, 'verification': v, 'head': self.oid(), 'task': self.cli('status')['task'], 'events': events})


def main():
    global SOURCE, OUT, INPUT
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--case', choices=('red', 'green', 'both'), default='both')
    parser.add_argument('--expect-red', action='store_true')
    args = parser.parse_args(); SOURCE = args.source.resolve(); OUT = args.output.resolve()
    if args.expect_red and args.case != 'red': raise ValueError('Counterfactual runs the rejection assertion only')
    OUT.mkdir(parents=True, exist_ok=False)
    INPUT = json.loads(args.input.read_text(encoding='utf-8'))
    cards.GATE = SOURCE / 'workbench/src/gates/cli.ts'; relay.SOURCE = SOURCE
    cards.ARTIFACT_ROOT = Path(tempfile.mkdtemp(prefix='t77p-', dir='/tmp'))
    names = ['test_extra_trailers_refused', 'test_hook_trailers_integrate']
    if args.case != 'both': names = names[:1] if args.case == 'red' else names[1:]
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2, failfast=True).run(unittest.TestSuite(ConflictTrailerProofs(n) for n in names))
    (OUT / 'unittest.txt').write_text(stream.getvalue(), encoding='utf-8')
    (OUT / 'commands.json').write_text(json.dumps(cards.COMMANDS, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    confirmed = len(result.failures) == 1 and not result.errors and not result.skipped and len(CONTRACTS) == 1 and not CONTRACTS[0]['pass']
    with tarfile.open(OUT / 'fixtures.tar.gz', 'x:gz') as archive:
        archive.add(cards.ARTIFACT_ROOT, arcname=cards.ARTIFACT_ROOT.name)
    # Always preserve the original candidate and driver, not the temporary
    # mutant product. The orchestrator records its one-line mutation recipe.
    with tarfile.open(OUT / 'sources.tar.gz', 'x:gz') as archive:
        for folder in ('workbench/src', 'workbench/hooks'): archive.add(ROOT / folder, arcname=folder)
        for name in ('test_conflict_trailer_proofs.py', 'trailer_conflict_host.ts', 'test_relay_conflict_e2e.py', 'test_task_cards_e2e.py'):
            archive.add(ROOT / 'workbench/tests' / name, arcname='workbench/tests/' + name)
        archive.add(args.input, arcname='controlled-trailer-input.json')
    report = {'status': 'PASS' if not args.expect_red and result.wasSuccessful() else 'INCOMPLETE',
        'red_confirmed': confirmed if args.expect_red else None, 'source': str(SOURCE), 'argv': sys.argv,
        'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
        'contracts': CONTRACTS, 'real_codex_turns': 0, 'artifacts': cards.ARTIFACTS,
        'scope': 'Real CLI, gates, Git and hook; controlled native runtime, not model evidence'}
    with (OUT / 'run.json').open('x', encoding='utf-8') as f: json.dump(report, f, ensure_ascii=False, indent=2); f.write('\n')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if (confirmed if args.expect_red else result.wasSuccessful()) else 1


if __name__ == '__main__': raise SystemExit(main())
