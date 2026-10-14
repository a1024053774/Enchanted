#!/usr/bin/env python3
"""Exercise fixture helper dispatch only, with no Git process or gate verdict."""
import argparse
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'workbench/tests'))
from test_relay_conflict_e2e import RelayConflict
from test_quality_chain_e2e import QualityCase
from test_quality_tracer_e2e import Tracer
from test_quality_widen_e2e import Widen
from test_quality_legacy_e2e import LegacyQuality
import test_task_cards_e2e as cards


class Helpers(unittest.TestCase):
    def subject(self, cls):
        case = cls('runTest' if cls is RelayConflict else 'preflight-only')
        case.root = Path(tempfile.mkdtemp(prefix='t077-helper-', dir='/tmp'))
        case.control = case.root / 'control'; case.control.mkdir()
        case.state = case.root / 'state'; case.task = 'fixture-task'
        case.recorded_git = []
        case.git = lambda *args, **kwargs: case.recorded_git.append((args, kwargs))
        case.oid = lambda *args, **kwargs: 'a' * 40
        return case

    def test_relay_commit_uses_each_attempt_observed_identity(self):
        case = self.subject(RelayConflict)
        for fence in (1, 2):
            launch = 'launch-' + str(fence); native = 'native-' + str(fence)
            workspace = case.root / ('attempt-' + str(fence)); workspace.mkdir()
            rollout = case.root / ('rollout-' + str(fence) + '.jsonl')
            rollout.write_text(json.dumps({'type': 'session_meta', 'payload': {'id': native, 'cwd': str(workspace)}}) + '\n'
                               + json.dumps({'type': 'turn_context', 'payload': {'model': 'gpt-6.1-sol', 'effort': 'xhigh'}}) + '\n', encoding='utf-8')
            (case.control / (launch + '.env.json')).write_text(json.dumps({'A2A_TOOL': 'codex-cli 0.162.1',
                'A2A_MODEL_REQUESTED': 'requested-model-is-not-observed-model', 'A2A_EFFORT_REQUESTED': 'low'}), encoding='utf-8')
            (case.control / (launch + '.runtime.json')).write_text(json.dumps({'native': native, 'file': str(rollout)}), encoding='utf-8')
            attempt = {'attempt_id': 'attempt-' + str(fence), 'session_id': 'session-' + str(fence),
                       'workspace': str(workspace), 'thread_id': 'thread-' + str(fence), 'runtime_identity': {'launch': launch}}
            self.assertEqual(case.commit(attempt), 'a' * 40)
            message = case.recorded_git[-1][0][-1]
            self.assertEqual(message.splitlines()[2:], [
                'A2A-Task: fixture-task', 'A2A-Attempt: attempt-' + str(fence),
                'A2A-Session: session-' + str(fence), 'A2A-Role: worker', 'A2A-Tool: codex-cli 0.162.1',
                'A2A-Model: gpt-6.1-sol', 'A2A-Effort: xhigh', 'A2A-Native-Session: ' + native, 'A2A-Launch: ' + launch])

    def test_quality_parent_commit_is_manual_only(self):
        for cls in (QualityCase, Tracer, Widen, LegacyQuality):
            with self.subTest(cls=cls.__name__):
                case = self.subject(cls)
                case.native = {'native': 'observed-native'}; case.launch = 'quality-launch'
                for thread in (None, 'managed-thread'):
                    workspace = case.root / ('manual' if thread is None else 'managed'); workspace.mkdir()
                    attempt = {'attempt_id': 'attempt', 'session_id': 'session', 'workspace': str(workspace), 'thread_id': thread}
                    self.assertEqual(case.commit(attempt), 'a' * 40)
                    self.assertEqual((workspace / 'src/value.txt').read_text(encoding='utf-8'), 'worker\n')

    def test_relay_cli_forwards_parent_keyword_arguments(self):
        case = self.subject(RelayConflict)

        def process(argv, cwd=None):
            cards.COMMANDS.append({'argv': list(map(str, argv)), 'scope': 'fixture forwarding only'})
            return SimpleNamespace(returncode=1, stdout=json.dumps({'ok': False, 'error': 'merge_conflict'}))

        case.process = process
        self.assertEqual(case.cli('verify', ok=False, error='merge_conflict'), {'ok': False, 'error': 'merge_conflict'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Helpers))
    (args.output / 'unittest.txt').write_text(output.getvalue(), encoding='utf-8')
    record = {'status': 'PASS' if result.wasSuccessful() else 'INCOMPLETE', 'tests': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
              'scope': 'Python helper resolution and construction only; no Git/gate/model', 'argv': sys.argv, 'real_codex_turns': 0}
    with (args.output / 'run.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps(record))
    raise SystemExit(0 if result.wasSuccessful() else 1)
