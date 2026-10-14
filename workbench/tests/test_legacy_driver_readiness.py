"""Fixture-client readiness checks, not product acceptance.

The real failed S3 run observed reviewing/null before review_requested. The
client must wait for the record within its existing deadline, while refusing
changed attempt/C/review identity, unknown states, and missing runtime facts.
Only the fixture client's status inputs and actor command recording are local.
"""
import argparse
import copy
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from legacy_quality_driver import QualityDriver

C = 'a' * 40
A = {'attempt_id': 'owned-attempt'}


def status(state='reviewing', review=None):
    return {'state': state, 'candidate_commit': C, 'current_attempt': copy.deepcopy(A), 'review': review, 'repair': None}


def review(state='running'):
    return {'review_id': 'owned-review', 'candidate_commit': C, 'attempt': copy.deepcopy(A), 'state': state,
            'launch_id': 'review-launch' if state == 'running' else None,
            'runtime_identity': {'native_session': 'review-native'} if state == 'running' else None}


class InputDriver(QualityDriver):
    def __init__(self, states):
        self.states = copy.deepcopy(states)
        self.calls = []; self.reviews = []

    def command(self, command, *args, **kwargs):
        self.calls.append((command, args))
        if command == 'status':
            if not self.states: raise AssertionError('Unexpected extra readiness read')
            return {'task': self.states.pop(0)}
        if command != 'integrate': raise AssertionError('Unexpected external actor action')
        return {}

    def complete_review(self, task, attempt, candidate):
        self.reviews.append((task, attempt['attempt_id'], candidate))

    def score_file(self, attempt):
        return '/fixture/' + attempt['attempt_id'] + '.score.json'


class Readiness(unittest.TestCase):
    def test_transient_missing_record(self):
        driver = InputDriver([status('verifying'), status(), status(review=review('requested')), status(review=review())])
        outcome = None
        try:
            with patch('legacy_quality_driver.time.sleep'):
                driver.finalize_run('task', A, C)
            outcome = 'completed'
        except RuntimeError as error:
            outcome = str(error)
        self.assertEqual(outcome, 'completed', 'An absent, not-yet-created review is not a different binding')
        self.assertEqual(driver.reviews, [('task', A['attempt_id'], C)])
        self.assertEqual([command for command, _ in driver.calls], ['status'] * 4 + ['integrate'])

    def refused(self, states, expected):
        driver = InputDriver(states)
        with patch('legacy_quality_driver.time.sleep'):
            with self.assertRaises(RuntimeError) as raised:
                driver.finalize_run('task', A, C)
        self.assertEqual(str(raised.exception), expected)
        self.assertEqual(driver.reviews, [])
        self.assertFalse(any(command == 'integrate' for command, _ in driver.calls))

    def test_changed_bindings_are_not_readiness(self):
        changed_attempt = status(); changed_attempt['current_attempt']['attempt_id'] = 'other-attempt'
        changed_c = status(); changed_c['candidate_commit'] = 'b' * 40
        changed_review_c = review(); changed_review_c['candidate_commit'] = 'b' * 40
        changed_review_attempt = review(); changed_review_attempt['attempt']['attempt_id'] = 'other-attempt'
        rows = [([changed_attempt], 'Executor driver cannot adopt replacement attempt.'),
                ([changed_c], 'Executor driver candidate changed.'),
                ([status(review=changed_review_c)], 'Run review binding differs from the submitted candidate.'),
                ([status(review=changed_review_attempt)], 'Run review binding differs from the submitted candidate.')]
        for states, expected in rows:
            with self.subTest(expected=expected, states=states): self.refused(states, expected)

    def test_changed_review_identity_is_refused(self):
        other = review('requested'); other['review_id'] = 'other-review'
        self.refused([status(review=review('requested')), status(review=other)], 'Run reviewer changed while waiting for readiness.')

    def test_unknown_review_and_missing_facts_are_refused(self):
        no_launch = review(); no_launch['launch_id'] = None
        no_native = review(); no_native['runtime_identity'] = None
        for item, expected in [(review('unknown'), 'Run reviewer failed or has an unknown outcome.'),
                               (no_launch, 'Running reviewer is missing its launch identity.'),
                               (no_native, 'Running reviewer is missing its launch identity.')]:
            with self.subTest(review=item): self.refused([status(review=item)], expected)

    def test_missing_record_still_has_original_deadline(self):
        driver = InputDriver([status()])
        with patch('legacy_quality_driver.time.monotonic', side_effect=[0, 0, 0, 20]), patch('legacy_quality_driver.time.sleep'):
            with self.assertRaises(RuntimeError) as raised:
                driver.finalize_run('task', A, C)
        self.assertEqual(str(raised.exception), 'Run review readiness deadline exceeded.')
        self.assertEqual(driver.reviews, [])
        self.assertEqual([command for command, _ in driver.calls], ['status'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', choices=['transient', 'all'], default='all')
    parser.add_argument('--expect-red', action='store_true')
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    suite = unittest.TestSuite([Readiness('test_transient_missing_record')]) if args.case == 'transient' else unittest.defaultTestLoader.loadTestsFromTestCase(Readiness)
    stream = io.StringIO(); result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (args.output / 'unittest.txt').write_text(stream.getvalue(), encoding='utf-8')
    red = result.testsRun == 1 and len(result.failures) == 1 and not result.errors
    passed = red if args.expect_red else result.wasSuccessful()
    report = {'status': 'PASS' if passed else 'INCOMPLETE', 'scope': 'fixture client only; no product result is supplied',
        'red_confirmed': red if args.expect_red else None, 'tests_run': result.testsRun,
        'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped), 'real_codex_turns': 0}
    with (args.output / 'run.json').open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2); handle.write('\n')
    print(json.dumps(report))
    return 0 if passed else 1


if __name__ == '__main__': raise SystemExit(main())
