#!/usr/bin/env python3
"""Local fixture checks only; these do not prove gate acceptance."""
import argparse
import ast
import io
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'workbench/tests'))
import daemon_acceptance_adapter as adapter


class Parent:
    def claim(self, task=None, owner='independent-check', overlap_reason=None):
        self.forwarded = (task, owner, overlap_reason)
        return self.attempt


class Subject(adapter.DaemonLifecycle, Parent):
    def __init__(self, method):
        self._testMethodName = method
        self.task = 'fixture-task'
        self.attempt = {'task_id': self.task, 'attempt_id': 'fixture-attempt'}
        self.commands = []
        self.scores = []

    def cli(self, *args):
        self.commands.append(args)
        return {'attempt': self.attempt}

    def prepare_executor_score(self, attempt):
        self.scores.append(attempt)


class FixtureChecks(unittest.TestCase):
    def test_manual_claim_preserves_reason_and_owner(self):
        subject = Subject('test_reclaim_guard_targets_history_and_rejects_foreign_and_unknown_attempt')
        reason = '  Historical reclaim; keep current worker alive.  '
        self.assertIs(subject.claim(task='explicit-task', owner='current-owner', overlap_reason=reason), subject.attempt)
        self.assertEqual(subject.forwarded, ('explicit-task', 'current-owner', reason))

    def test_managed_claim_sends_reason_to_dispatch_cli(self):
        subject = Subject('test_integrate_expected_attempt_uses_real_git_gate')
        reason = '  Keep both attempts for the integration guard.  '
        self.assertIs(subject.claim(overlap_reason=reason), subject.attempt)
        self.assertEqual(subject.commands, [('dispatch', '--task', 'fixture-task', '--runtime-mode',
                                            'approval-required', '--overlap-reason', reason)])
        self.assertEqual(subject.scores, [subject.attempt])

    def test_absent_reason_remains_absent(self):
        manual = Subject('test_reclaim_guard_targets_history_and_rejects_foreign_and_unknown_attempt')
        manual.claim(owner='current-owner')
        self.assertEqual(manual.forwarded, (None, 'current-owner', None))
        managed = Subject('test_integrate_expected_attempt_uses_real_git_gate')
        managed.claim()
        self.assertEqual(managed.commands, [('dispatch', '--task', 'fixture-task', '--runtime-mode', 'approval-required')])

    def test_runner_continues_after_eleventh_test_error(self):
        tree = ast.parse((ROOT / 'workbench/tests/run_s3_rebased_regression.py').read_text(encoding='utf-8'))
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                 and node.func.value.id == 'unittest' and node.func.attr == 'TextTestRunner']
        self.assertEqual(len(calls), 1)
        expression = ast.Expression(body=calls[0]); ast.fix_missing_locations(expression)
        output = io.StringIO()
        runner = eval(compile(expression, '<actual-runner-constructor>', 'eval'),
                      {'unittest': unittest, 'stream': output, 'result_class': unittest.TextTestResult,
                       'SuiteResult': unittest.TextTestResult})
        observed = []

        class Case(unittest.TestCase):
            def runTest(self):
                observed.append(len(observed) + 1)
                if len(observed) == 11:
                    raise RuntimeError('Intentional runner-only error at test 11')

        result = runner.run(unittest.TestSuite(Case() for _ in range(18)))
        self.assertEqual(observed, list(range(1, 19)))
        self.assertEqual(result.testsRun, 18)
        self.assertEqual((len(result.failures), len(result.errors), len(result.skipped)), (0, 1, 0))
        self.assertFalse(result.wasSuccessful())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(FixtureChecks))
    (args.output / 'unittest.txt').write_text(output.getvalue(), encoding='utf-8')
    record = {'status': 'PASS' if result.wasSuccessful() else 'INCOMPLETE', 'scope': 'fixture_client_and_runner_only',
              'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'skipped': len(result.skipped), 'argv': sys.argv, 'real_codex_turns': 0,
              'real_gate_acceptance': 'NOT RUN: controller final-04 run suite required'}
    with (args.output / 'run.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps(record))
    raise SystemExit(0 if result.wasSuccessful() else 1)
