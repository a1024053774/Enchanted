"""Exercise the real probe's release workflow without a provider or socket.

Failure modes: the first input waits for a log that only that input creates;
missing leader, replaced leader, or a known native session bypasses the check.
"""
import argparse
import contextlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

PROBE = None
OUT = None
OBSERVATIONS = []


class InitialRelease(unittest.TestCase):
    def invoke(self, initial):
        current = dict(initial)
        calls, saved, known = [], {}, set()
        clock = [0]

        def call(command, *values):
            calls.append({'command': command, 'values': list(values), 'native_session': current['native_session']})
            if command == 'pane_process_info':
                return dict(current)
            self.assertEqual(command, 'pane_release')
            # This is the first point at which the scripted CLI gets input.
            current['native_session'] = 'fixture-native'
            return {'ok': True, 'state': 'busy'}

        def sleep(_duration):
            clock[0] += 1

        artifact = {'test': self.id(), 'initial': initial, 'calls': calls, 'saved': saved}
        OBSERVATIONS.append(artifact)
        try:
            value = PROBE.release_initial_worker(call, 'fixture-thread', known, saved.__setitem__,
                monotonic=lambda: clock[0], sleep=sleep)
            artifact.update(outcome='released', before=value, after=current, known_pids=sorted(known))
            return value, current, calls
        except RuntimeError as error:
            artifact.update(outcome='refused', error=str(error), known_pids=sorted(known))
            raise

    @staticmethod
    def info(**changes):
        return {'ok': True, 'shell_pid': 11001, 'leader': 11002, 'native_session': None,
                'failed': None, 'processes': [{'pid': 11001}, {'pid': 11002}], **changes}

    def test_first_input_precedes_native_log(self):
        try:
            before, after, calls = self.invoke(self.info())
        except RuntimeError as error:
            self.fail('The confirmed initial leader must receive the first input before its native log exists: ' + str(error))
        self.assertIsNone(before['native_session'])
        self.assertEqual(after['native_session'], 'fixture-native')
        self.assertEqual([row['command'] for row in calls], ['pane_process_info', 'pane_release'])

    def test_no_leader_is_refused(self):
        with self.assertRaises(RuntimeError):
            self.invoke(self.info(leader=None))
        self.assertFalse(any(row['command'] == 'pane_release' for row in OBSERVATIONS[-1]['calls']))

    def test_replaced_leader_is_refused(self):
        with self.assertRaises(RuntimeError):
            self.invoke(self.info(native_session='fixture-native', failed='codex_leader_replaced_or_exited'))
        self.assertFalse(any(row['command'] == 'pane_release' for row in OBSERVATIONS[-1]['calls']))

    def test_existing_native_session_is_preserved(self):
        before, after, calls = self.invoke(self.info(native_session='fixture-native'))
        self.assertEqual(before['native_session'], after['native_session'])
        self.assertEqual([row['command'] for row in calls], ['pane_process_info', 'pane_release'])


def main():
    global PROBE, OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve(); OUT = args.output.resolve(); OUT.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location('t076_release_probe', source / 'workbench/tests/run_t076_real.py')
    PROBE = importlib.util.module_from_spec(spec); spec.loader.exec_module(PROBE)
    with (OUT / 'stdout.txt').open('x', encoding='utf-8') as stdout, (OUT / 'stderr.txt').open('x', encoding='utf-8') as stderr:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(InitialRelease))
    record = {'status': 'PASS' if result.wasSuccessful() else 'INCOMPLETE', 'argv': sys.argv,
              'source': str(source), 'real_codex_turns': 0, 'tests_run': result.testsRun,
              'failures': [{'test': test.id(), 'text': value} for test, value in result.failures],
              'errors': [{'test': test.id(), 'text': value} for test, value in result.errors],
              'skipped': result.skipped, 'observations': OBSERVATIONS,
              'evidence_layer': 'actual real-probe release function; scripted calls and clock'}
    with (OUT / 'run.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print(json.dumps({'status': record['status'], 'tests_run': result.testsRun,
                      'failures': len(result.failures), 'errors': len(result.errors)}))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
