"""T-265 驱动的故障注入检查；所有 PTY、Popen、进程查询与信号都是 mock。

独立约束来自主控 #128：非正 PID 不得发信号，已退出子进程先回收；诊断先落盘；
清理异常不能盖掉原异常。没有真实 CLI、模型、ps 或 OS 信号。
"""
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
SOURCE = Path(os.environ.get('T265_DRIVER_SOURCE', ROOT / 'workbench/tests/test_t265_review_cli_e2e.py'))
spec = importlib.util.spec_from_file_location('t265_driver', SOURCE)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


class Diagnostics(unittest.TestCase):
    def drive(self, mode):
        root = Path(tempfile.mkdtemp(prefix='t265-driver-mock-', dir=os.environ['A2A_REQUEST_DIR']))
        self.addCleanup(lambda: driver.shutil.rmtree(root))
        home = root / 'home'; home.mkdir()
        evidence = root / 'evidence'; evidence.mkdir()
        diagnostic, calls = {}, []

        class Child:
            pid = -1 if mode == 'invalid' else 440265
            returncode = 23 if mode == 'exited' else None

            def poll(self):
                calls.append('poll')
                return self.returncode

            def wait(self, timeout=None):
                calls.append('wait')
                self.returncode = 23 if mode == 'exited' else 0
                return self.returncode

        child = Child()

        def signal(group, sig):
            calls.append(('signal', group, int(sig)))
            if mode == 'permission':
                raise PermissionError(1, 'synthetic cleanup EPERM')
            # Native output and process stage must already exist before any signal.
            if 'evidence' in inspect.signature(driver.interact).parameters:
                self.assertIn(b'original terminal bytes', (evidence / 'parent-terminal.txt').read_bytes())
                self.assertTrue((evidence / 'parent-before-cleanup-native-events.json').exists())
                self.assertTrue((evidence / 'parent-process.jsonl').exists())

        def close(descriptor):
            calls.append(f'close-{descriptor}')
            if descriptor == 10:
                if ((evidence / 'parent-before-cleanup-native-events.json').exists() and
                        b'original terminal bytes' in (evidence / 'parent-terminal.txt').read_bytes()):
                    calls.append('diagnostics-persisted-at-master-close')
                if mode == 'close-error':
                    raise OSError(5, 'synthetic master close failure')

        reads = iter([b'original terminal bytes', b''])
        clock = [0.0]
        real_monotonic = driver.time.monotonic
        onboarding = [(0.1, 'original terminal bytes\nFolder access\n\x1b[1m› 1. Open restricted\x1b[0m\n'.encode()),
                      (0.3, '\x1b[1m›  1. Open restricted\x1b[0m\n'.encode()),
                      (1.6, b'Ask Codex to do anything\x1b]7501;state=idle:app=codex\x1b\\'),
                      (3.0, b'Message exceeds the maximum length of 1048576 characters')]
        selects = 0

        def select(*args):
            nonlocal selects
            selects += 1
            if mode == 'onboarding':
                clock[0] = round(clock[0] + .1, 1)
                return ([10] if onboarding and clock[0] >= onboarding[0][0] else [], args[1], [])
            if mode == 'timeout':
                clock[0] += .6
                return ([10] if selects == 1 else [], [], [])
            if mode == 'permission' and selects == 2:
                raise ValueError('original interaction failure')
            return ([10], [], [])

        error = None
        with patch.object(driver.pty, 'fork', return_value=(child.pid, 10)), \
                patch.object(driver.pty, 'openpty', return_value=(10, 11)), \
                patch.object(driver.subprocess, 'Popen', return_value=child,
                             side_effect=PermissionError(1, 'synthetic spawn denied') if mode == 'spawn-failed' else None), \
                patch.object(driver.os, 'close', side_effect=close), patch.object(driver.os, 'set_blocking'), \
                patch.object(driver.fcntl, 'ioctl'), patch.object(driver.select, 'select', side_effect=select), \
                patch.object(driver.time, 'monotonic', side_effect=lambda: clock[0] if mode in ('onboarding', 'timeout') else real_monotonic()), \
                patch.object(driver.os, 'read', side_effect=lambda *_: onboarding.pop(0)[1] if mode == 'onboarding' else next(reads)), \
                patch.object(driver.os, 'write', side_effect=lambda fd, data: (calls.append(('write', clock[0], data)), len(data))[1]), \
                patch.object(driver.os, 'getpgid', return_value=999999 if mode == 'foreign-group' else child.pid), \
                patch.object(driver.os, 'killpg', side_effect=signal), \
                patch.object(driver.os, 'waitpid', return_value=(child.pid, 23 << 8)):
            try:
                kw = dict(evidence=evidence, name='parent', diagnostic=diagnostic) if 'evidence' in inspect.signature(driver.interact).parameters else {}
                driver.interact(['/fixture/codex'], {}, 'input', home, 4 if mode == 'onboarding' else 1, True, **kw)
            except Exception as observed:
                error = observed
        return root, diagnostic, calls, error

    def test_nonpositive_pid_is_never_signalled(self):
        _, diagnostic, calls, _ = self.drive('invalid')
        self.assertFalse([c for c in calls if isinstance(c, tuple)], 'invalid child PID must never be signalled')
        self.assertFalse(diagnostic.get('cleanup', {}).get('complete', True))

    def test_restricted_choice_waits_for_quiet_and_ready_before_actual_delivery(self):
        root, diagnostic, calls, error = self.drive('onboarding')
        self.assertIsNone(error)
        writes = [c for c in calls if isinstance(c, tuple) and c[0] == 'write']
        self.assertEqual(writes[0][2], b'\r', 'selected Open restricted receives only CR, never a numeric choice')
        self.assertGreaterEqual(writes[0][1], 1.1, 'wait 800ms after the final redraw at t=0.3')
        self.assertEqual([c[2] for c in writes], [b'\r', b'\x1b[200~input\x1b[201~', b'\r'])
        self.assertGreaterEqual(writes[1][1], 1.6, 'no task paste before native ready')
        stages = [json.loads(line)['stage'] for line in (root / 'evidence/parent-process.jsonl').read_text(encoding='utf-8').splitlines()]
        expected = ['restricted-choice-observed', 'restricted-key-written', 'native-ready-observed',
                    'entry-paste-written', 'task-submitted']
        self.assertEqual([stage for stage in stages if stage in expected], expected)
        self.assertTrue(diagnostic['restricted_key_written'])
        self.assertTrue(diagnostic['native_ready_observed'])
        self.assertTrue(diagnostic['sent'])

    def test_exited_child_is_reaped_without_signal(self):
        root, diagnostic, calls, error = self.drive('exited')
        self.assertFalse([c for c in calls if isinstance(c, tuple)], 'exited child must be polled/reaped before signalling')
        self.assertIsNone(error)
        self.assertEqual(diagnostic['cleanup']['exit_code'], 23)
        self.assertIn(b'original terminal bytes', (root / 'evidence/parent-terminal.txt').read_bytes())

    def test_cleanup_error_preserves_primary_and_evidence(self):
        root, diagnostic, calls, error = self.drive('permission')
        self.assertIsInstance(error, ValueError, 'cleanup error must not replace the original interaction failure')
        self.assertEqual(str(error), 'original interaction failure')
        self.assertEqual(diagnostic['cleanup']['error']['errno'], 1)
        self.assertFalse(diagnostic['cleanup']['complete'])
        self.assertEqual(len([c for c in calls if isinstance(c, tuple)]), 1, 'no signal retry after EPERM')
        self.assertIn(b'original terminal bytes', (root / 'evidence/parent-terminal.txt').read_bytes())
        final = json.loads((root / 'evidence/parent-process.json').read_text(encoding='utf-8'))
        self.assertEqual(final['error']['message'], 'original interaction failure')

    def test_live_owned_group_is_checked_and_reaped(self):
        _, diagnostic, calls, error = self.drive('live')
        self.assertIsNone(error)
        self.assertEqual([c[1] for c in calls if isinstance(c, tuple)], [440265])
        self.assertEqual(calls[0], 'poll')
        self.assertTrue(diagnostic['cleanup']['complete'])
        self.assertEqual(diagnostic['cleanup']['exit_code'], 0)

    def test_owned_master_closes_once_after_diagnostics_before_reaping(self):
        # native-05 feedback / process-wait-probe-02: a held master can prevent
        # this same Popen.wait from completing. Test ordering, not ESRCH guessing.
        for mode in ('live', 'timeout', 'permission', 'close-error'):
            with self.subTest(mode=mode):
                root, diagnostic, calls, error = self.drive(mode)
                self.assertEqual(calls.count('close-10'), 1, 'own master closes once, including close errors')
                self.assertEqual(calls.count('close-11'), 1, 'own slave closes once')
                self.assertIn('diagnostics-persisted-at-master-close', calls)
                cleanup = [i for i, call in enumerate(calls) if call == 'wait' or
                           isinstance(call, tuple) and call[0] == 'signal']
                self.assertTrue(cleanup, 'must still confirm exit with the original cleanup path')
                self.assertLess(calls.index('close-10'), min(cleanup), 'release owned master before stop_owned can signal/wait')
                if mode == 'permission':
                    self.assertIsInstance(error, ValueError, 'cleanup must preserve the original interaction error')
                    self.assertFalse(diagnostic['cleanup']['complete'])
                elif mode == 'close-error':
                    self.assertIsInstance(error, RuntimeError, 'failed master close cannot report complete interaction')
                    saved = json.loads((root / 'evidence/parent-process.json').read_text(encoding='utf-8'))
                    self.assertEqual(saved['diagnostic_errors'][0]['message'], '[Errno 5] synthetic master close failure')
                else:
                    self.assertIsNone(error)
                    self.assertTrue(diagnostic['cleanup']['complete'])
                if mode == 'timeout':
                    self.assertTrue(diagnostic['deadline_reached'])

    def test_foreign_group_is_never_signalled(self):
        _, diagnostic, calls, _ = self.drive('foreign-group')
        self.assertFalse([c for c in calls if isinstance(c, tuple)], 'unverified process group must never be signalled')
        self.assertFalse(diagnostic['cleanup']['complete'])

    def test_spawn_failure_is_saved_without_signal(self):
        root, diagnostic, calls, error = self.drive('spawn-failed')
        self.assertIsInstance(error, PermissionError)
        self.assertEqual(str(error), '[Errno 1] synthetic spawn denied')
        self.assertFalse(diagnostic['created'])
        self.assertIsNone(diagnostic['pid'])
        self.assertFalse([c for c in calls if isinstance(c, tuple)])
        final = json.loads((root / 'evidence/parent-process.json').read_text(encoding='utf-8'))
        self.assertEqual(final['error_stage'], 'creating-child')

    def test_owned_exit_orderings_require_wait_evidence(self):
        timeout = subprocess.TimeoutExpired('owned child', 3)
        missing = ProcessLookupError(3, 'synthetic ESRCH')
        denied = PermissionError(1, 'synthetic EPERM')
        # poll results, getpgid results, killpg results, wait results,
        # expected signal attempts, expected error. No real process is touched.
        rows = [
            ('already-exited', [-15], [], [], [-15], [], None),
            ('exit-before-term-lookup', [None], [missing], [], [-15], [], None),
            ('exit-before-term-signal', [None], [440265], [missing], [-15], [15], None),
            ('term-timeout-then-poll-exited', [None, -15], [440265], [None], [timeout, -15], [15], None),
            ('native03-term-timeout-esrch-wait', [None, None], [440265, missing], [None], [timeout, -15], [15], None),
            ('exit-before-kill-signal', [None, None], [440265, 440265], [None, missing], [timeout, -15], [15, 9], None),
            ('esrch-without-wait-proof', [None], [missing], [], [timeout], [], subprocess.TimeoutExpired),
            ('identity-changed', [None], [999999], [], [], [], RuntimeError),
            ('eperm-not-esrch', [None], [440265], [denied], [], [15], PermissionError),
        ]
        for name, polls, groups, sends, waits, expected, error_type in rows:
            with self.subTest(name=name):
                from unittest.mock import Mock
                child = Mock(pid=440265)
                child.poll.side_effect = polls
                child.wait.side_effect = waits
                diagnostic = {'pid': 440265, 'pgid': 440265}
                with patch.object(driver.os, 'getpgid', side_effect=groups), \
                        patch.object(driver.os, 'killpg', side_effect=sends) as signal_call:
                    caught = result = None
                    try:
                        result = driver.stop_owned(child, diagnostic)
                    except Exception as error:
                        caught = error
                    if error_type:
                        self.assertIsInstance(caught, error_type, 'unconfirmed exit must remain an explicit failure')
                    else:
                        self.assertIsNone(caught, 'owned wait must establish exit after this ordering')
                        self.assertTrue(result['complete'])
                        self.assertTrue(result['reaped'])
                        self.assertEqual(result['exit_code'], -15)
                    self.assertEqual([int(call.args[1]) for call in signal_call.call_args_list], expected)
                    self.assertEqual(child.poll.call_count, len(polls), 'poll before every signal round')
                    self.assertEqual(child.wait.call_count, len(waits), 'only owned wait proves exit')

    def test_main_keeps_failed_case_and_unconfirmed_fixture(self):
        root = Path(tempfile.mkdtemp(prefix='t265-driver-main-', dir=os.environ['A2A_REQUEST_DIR']))
        self.addCleanup(lambda: driver.shutil.rmtree(root))
        fixture = root / 'fixture'; fixture.mkdir()
        home = fixture / 'parent/codex-home'; home.mkdir(parents=True)
        (home / 'auth.json').write_text('synthetic-not-a-credential', encoding='utf-8')
        summary = root / 'summary.json'

        def failed_case(*args):
            if len(args) == 5:
                args[-1]['process'] = {'pid': 440265, 'created': True, 'cleanup': {'complete': False}}
            raise ValueError('original native boundary failure')

        with patch.object(sys, 'argv', ['driver', '--summary', str(summary), '--codex', '/usr/bin/true']), \
                patch.object(driver.tempfile, 'mkdtemp', return_value=str(fixture)), \
                patch.object(driver.subprocess, 'check_output', return_value='synthetic-version'), \
                patch.object(driver, 'case', side_effect=failed_case):
            self.assertEqual(driver.main(), 1)
        saved = json.loads(summary.read_text(encoding='utf-8'))
        self.assertTrue(fixture.exists(), 'unconfirmed native child must retain its fixture')
        self.assertTrue((home / 'auth.json').exists(), 'do not delete an unconfirmed live child home')
        self.assertEqual(saved['status'], 'INCOMPLETE')
        self.assertEqual(saved['error'], 'original native boundary failure')
        self.assertEqual(saved['cases'][0]['name'], 'parent', 'failed case must remain in report')
        self.assertFalse(saved['cleanup']['removed'])

    def test_failed_fixture_deletion_cannot_report_success(self):
        root = Path(tempfile.mkdtemp(prefix='t265-driver-delete-', dir=os.environ['A2A_REQUEST_DIR']))
        self.addCleanup(lambda: driver.shutil.rmtree(root))
        fixture = root / 'fixture'; fixture.mkdir()
        summary = root / 'summary.json'

        def passed_case(*args):
            if len(args) == 5:
                args[-1].update(status='PASS', process={'cleanup': {'complete': True}})
            return {'status': 'PASS'}

        with patch.object(sys, 'argv', ['driver', '--summary', str(summary), '--codex', '/usr/bin/true']), \
                patch.object(driver.tempfile, 'mkdtemp', return_value=str(fixture)), \
                patch.object(driver.subprocess, 'check_output', return_value='synthetic-version'), \
                patch.object(driver, 'case', side_effect=passed_case), \
                patch.object(driver.shutil, 'rmtree', side_effect=PermissionError(1, 'synthetic deletion denied')):
            try:
                driver.main()
            except PermissionError:
                pass
        saved = json.loads(summary.read_text(encoding='utf-8'))
        self.assertEqual(saved['status'], 'INCOMPLETE', 'failed deletion cannot leave a PASS summary')
        self.assertFalse(saved['cleanup']['removed'])
        self.assertEqual(saved['cleanup']['error']['errno'], 1)


if __name__ == '__main__':
    unittest.main()
