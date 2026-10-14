#!/usr/bin/env python3
"""Local classifier counterexamples; no daemon, Git mutation or provider."""
import argparse
import ast
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[3]
E = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'workbench/tests'))
import test_worktree_lifecycle_e2e as subject

CASES = ['test_conflict_active_worker_reworks_and_integrates', 'test_conflict_ended_session_gets_new_attempt',
         'test_conflict_unknown_session_preserves_scene_and_reports', 'test_conflict_unknown_delivery_does_not_resend',
         'test_merge_command_error_is_not_text_conflict', 'test_conflict_rework_still_rejects_forbidden_path',
         'test_conflict_rework_still_rejects_foreign_trailer']
TARGETS = ['CONFLICT-ACTIVE-WRITEBACK', 'CONFLICT-ENDED-NEW-ATTEMPT', 'CONFLICT-UNKNOWN-SESSION-REPORT',
           'CONFLICT-UNKNOWN-DELIVERY-ONCE', 'CONFLICT-GIT-ERROR-CLASSIFICATION',
           'CONFLICT-REWORK-FORBIDDEN-PATH', 'CONFLICT-REWORK-FOREIGN-TRAILER']
# Independent expected prerequisites from controller #123, including the
# common scenario facts. The classifier's own table is not the answer key.
FACTS = [
    ('scenario_prepared', 'worker_session_input_available', 'text_conflict_observed', 'conflict_handling_entered'),
    ('scenario_prepared', 'ended_session_input_configured', 'text_conflict_observed', 'conflict_handling_entered'),
    ('scenario_prepared', 'unknown_session_input_configured', 'text_conflict_observed', 'conflict_handling_entered'),
    ('scenario_prepared', 'delivery_unknown_input_configured', 'text_conflict_observed', 'conflict_handling_entered'),
    ('scenario_prepared', 'git_io_failure_observed', 'target_verify_executed'),
    ('scenario_prepared', 'text_conflict_observed', 'conflict_handling_entered',
     'conflict_delivered', 'explicit_resubmitted', 'target_verify_executed'),
    ('scenario_prepared', 'text_conflict_observed', 'conflict_handling_entered',
     'conflict_delivered', 'explicit_resubmitted', 'target_verify_executed'),
]
CLASSIFY = subject.classify_conflict_red


def inputs(index=0, passed=False):
    return {'case': CASES[index], 'contracts': [{'assertion_id': TARGETS[index], 'pass': passed}],
            'evidence': {'steps': [{'kind': 'precondition', 'id': name, 'passed': True,
                                   'details': {'independent_fixture_fact': name}} for name in FACTS[index]]
                         + [{'kind': 'target', 'id': TARGETS[index], 'passed': passed}], 'cleanup_failures': []},
            'tests_run': 1, 'failures': 0 if passed else 1, 'errors': 0, 'skipped': 0}


class ClassifierChecks(unittest.TestCase):
    def test_exact_target_and_all_prior_receipts_are_red(self):
        for index in range(7):
            with self.subTest(case=CASES[index]):
                value = CLASSIFY(**inputs(index))
                self.assertTrue(value['business_red']); self.assertEqual(value['target_assertion_id'], TARGETS[index])
                self.assertEqual(value['required_preconditions'], list(FACTS[index]))

    def test_original_06_07_precondition_failures_are_not_covered(self):
        for index in (5, 6):
            with self.subTest(case=CASES[index]):
                path = E / 'outside-rebase-final-05' / ('conflict-red-%02d' % (index + 1)) / ('01-' + CASES[index]) / 'result.json'
                old = json.loads(path.read_text(encoding='utf-8'))
                args = inputs(index)
                args.update(contracts=[{**row, 'assertion_id': None} for row in old['contracts']],
                            evidence={'steps': [], 'cleanup_failures': []},
                            failures=old['failures'], errors=old['errors'], skipped=old['skipped'])
                value = CLASSIFY(**args)
                self.assertFalse(value['business_red']); self.assertEqual(value['target_coverage'], 'NOT_COVERED')

    def test_each_missing_false_or_late_prerequisite_blocks_red(self):
        for case_index, facts in enumerate(FACTS):
            for index, fact in enumerate(facts):
                for kind in ('missing', 'false', 'late'):
                    with self.subTest(case=CASES[case_index], fact=fact, kind=kind):
                        args = inputs(case_index); step = args['evidence']['steps'][index]
                        if kind == 'missing': del args['evidence']['steps'][index]
                        elif kind == 'false': step['passed'] = False
                        else: args['evidence']['steps'].append(args['evidence']['steps'].pop(index))
                        value = CLASSIFY(**args)
                        self.assertFalse(value['business_red']); self.assertIn(fact, value['missing_preconditions'])

    def test_other_assertion_failure_is_not_the_target(self):
        args = inputs(passed=True); args['failures'] = 1
        args['contracts'].append({'assertion_id': None, 'pass': False})
        self.assertFalse(CLASSIFY(**args)['business_red'])

    def test_errors_skips_and_cleanup_failures_block_red(self):
        for key in ('errors', 'skipped', 'cleanup_failures'):
            with self.subTest(key=key):
                args = inputs()
                if key == 'cleanup_failures': args['evidence'][key] = [{'error': 'cleanup failed'}]
                else: args[key] = 1
                self.assertFalse(CLASSIFY(**args)['business_red'])

    def test_cleanup_assertion_is_recorded_separately(self):
        class CleanupProbe(subject.ConflictContracts):
            def setUp(self):
                self.conflict_evidence = {'steps': [], 'cleanup_failures': []}
                self.addCleanup(self.fail, 'Intentional cleanup assertion')
            def runTest(self): pass
            def tearDown(self): pass

        probe = CleanupProbe(); result = unittest.TestResult(); probe.run(result)
        self.assertEqual((len(result.failures), len(result.errors)), (1, 0))
        self.assertEqual(len(probe.conflict_evidence['cleanup_failures']), 1)
        args = inputs(); args['evidence']['cleanup_failures'] = probe.conflict_evidence['cleanup_failures']
        self.assertFalse(CLASSIFY(**args)['business_red'])

    def test_duplicate_target_and_empty_receipt_block_red(self):
        for kind in ('duplicate', 'empty'):
            with self.subTest(kind=kind):
                args = inputs()
                if kind == 'duplicate': args['evidence']['steps'].append(copy.deepcopy(args['evidence']['steps'][-1]))
                else: args['evidence']['steps'][0]['details'] = {}
                self.assertFalse(CLASSIFY(**args)['business_red'])

    def test_unreported_failure_and_wrong_test_count_block_red(self):
        for key, value in [('failures', 0), ('tests_run', 0), ('tests_run', 2)]:
            with self.subTest(key=key, value=value):
                args = inputs(); args[key] = value
                self.assertFalse(CLASSIFY(**args)['business_red'])

    def test_success_is_not_a_counterfactual_failure(self):
        value = CLASSIFY(**inputs(passed=True))
        self.assertFalse(value['business_red']); self.assertTrue(value['target_passed'])


def main():
    global CLASSIFY
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--old-rule-mutant', action='store_true')
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    mutation = None
    if args.old_rule_mutant:
        original = subprocess.check_output(['git', 'show', '6779d48e85b4724b0b0a6411305e519b9fece392:workbench/tests/test_worktree_lifecycle_e2e.py'], cwd=ROOT, text=True)
        expressions = [value for node in ast.walk(ast.parse(original)) if isinstance(node, ast.Dict)
                       for key, value in zip(node.keys, node.values) if isinstance(key, ast.Constant) and key.value == 'business_red'
                       and isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == 'bool']
        assert len(expressions) == 1
        expression = ast.Expression(body=expressions[0]); ast.fix_missing_locations(expression)
        code = compile(expression, '<recorded-old-business-red-expression>', 'eval')

        def old_rule(**values):
            record = subject.classify_conflict_red(**values)
            result = SimpleNamespace(failures=[None] * values['failures'], errors=[None] * values['errors'])
            record['business_red'] = eval(code, {'result': result, 'contracts': values['contracts']})
            return record

        CLASSIFY = old_rule
        mutation = {'scope': 'in-memory fixture classifier only', 'source_revision': '6779d48e85b4724b0b0a6411305e519b9fece392',
                    'old_expression': ast.unparse(expressions[0]), 'product_changed': False}
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ClassifierChecks))
    (args.output / 'unittest.txt').write_text(stream.getvalue(), encoding='utf-8')
    snapshot = args.output / 'fixture-at-run.py'
    snapshot.write_bytes((ROOT / 'workbench/tests/test_worktree_lifecycle_e2e.py').read_bytes())
    report = {'status': 'PASS' if result.wasSuccessful() else 'INCOMPLETE', 'scope': 'fixture classifier only; not product E2E',
              'argv': sys.argv, 'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
              'skipped': len(result.skipped), 'mutation': mutation, 'real_codex_turns': 0,
              'source_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'expected_case_prerequisites': {case: list(facts) for case, facts in zip(CASES, FACTS)},
              'fixture_source': str(snapshot)}
    with (args.output / 'run.json').open('x', encoding='utf-8') as output:
        json.dump(report, output, ensure_ascii=False, indent=2); output.write('\n')
    print(json.dumps({key: report[key] for key in ('status', 'tests_run', 'failures', 'errors', 'skipped')}))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__': raise SystemExit(main())
