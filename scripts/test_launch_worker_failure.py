#!/usr/bin/env python3
"""T-094 命令入口边界测试；Herdr/Codex 是显式夹具，不连接 socket 或模型。"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid

REPO = Path(__file__).resolve().parents[1]
LAUNCHER = REPO / "scripts/launch-worker"
REPORTS = []


class LaunchFailure(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="t094-contract-", dir="/tmp")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pane = "owned:" + uuid.uuid4().hex[:12]
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("A2A_", "GIT_CONFIG_"))}
        self.env.update(HERDR_ENV="1", PYTHONDONTWRITEBYTECODE="1",
                        PYTHONPATH=str(REPO / "scripts"),
                        GIT_AUTHOR_NAME="fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
                        GIT_COMMITTER_NAME="fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid")
        role = self.root / ".project-map/roles/worker.md"
        role.parent.mkdir(parents=True)
        role.write_text("测试角色\n", encoding="utf-8")
        for args in (["init", "-q"], ["add", ".project-map"], ["commit", "-qm", "fixture"]):
            subprocess.run(["git", *args], cwd=self.root, env=self.env, check=True)
        fakebin = self.root / "explicit-fake-bin"
        fakebin.mkdir()
        for tool, source in {"codex": "print('codex-cli fixture')\n", "herdr": '''
import json, os, sys
from pathlib import Path
a = sys.argv[1:]
pane = os.environ['T094_PANE']
with Path(os.environ['T094_CALLS']).open('a') as f:
 f.write(json.dumps(a) + '\\n')
scenario = os.environ['T094_SCENARIO']
def error(code, message):
 print(json.dumps({'error': {'code': code, 'message': message}}), file=sys.stderr)
 sys.exit(1)
if a[:2] == ['pane', 'split']:
 print(json.dumps({'result': {'pane': {'pane_id': pane}}}))
elif a[:2] == ['pane', 'process-info']:
 started = Path(os.environ['T094_STARTED']).exists()
 processes = [{'pid': 70, 'name': 'codex', 'argv': ['codex', '--no-daemon']}] if started and scenario in ('unregistered', 'blocked', 'diagnostic-error', 'unregistered-null-name') else [{'pid': 60, 'name': 'zsh'}]
 if started and scenario == 'busy-git':
  processes = [{'pid': 60, 'name': 'zsh', 'argv': ['-zsh']},
               {'pid': 71, 'name': 'git', 'argv': json.loads(os.environ['T094_BUSY_ARGV'])}]
 print(json.dumps({'result': {'process_info': {'pane_id': pane, 'shell_pid': 60,
       'foreground_process_group_id': 70 if processes[0]['pid'] == 70 else 60,
       'foreground_processes': processes}}}))
elif a[:2] == ['agent', 'start']:
 Path(os.environ['T094_STARTED']).touch()
 if scenario == 'success':
  print(json.dumps({'result': {'agent': {'name': a[2], 'agent': 'codex', 'pane_id': pane}}}))
 elif scenario == 'blocked':
  error('agent_not_ready', 'fixture startup approval')
 else:
  print('fixture stdout before failure')
  error('agent_name_not_found' if scenario == 'unregistered' else 'agent_pane_busy', 'fixture readable cause')
elif a[:2] == ['agent', 'get']:
 if scenario == 'diagnostic-error':
  error('transport_error', 'fixture registration unknown')
 if scenario == 'unregistered-null-name':
  print(json.dumps({'result': {'agent': {'name': None, 'agent': 'codex', 'pane_id': pane}}}))
  sys.exit(0)
 if scenario == 'blocked':
  print(json.dumps({'result': {'agent': {'name': 'fixture-worker', 'agent': 'codex', 'pane_id': pane, 'agent_status': 'blocked'}}}))
 else:
  error('agent_not_found', 'fixture has no registered agent')
else:
 error('fixture_unknown_command', str(a))
'''}.items():
            path = fakebin / tool
            path.write_text("#!" + sys.executable + "\n" + source, encoding="utf-8")
            path.chmod(0o755)
        self.env.update(PATH=str(fakebin) + os.pathsep + self.env["PATH"],
                        T094_CALLS=str(self.root / "calls.jsonl"),
                        T094_STARTED=str(self.root / "start-called"), T094_PANE=self.pane)

    def launch(self, scenario):
        r = subprocess.run([sys.executable, str(LAUNCHER), "--root", str(self.root), "--cwd", str(self.root),
             "--agent", "fixture-worker", "--project", "fixture", "--task", "T-094", "--attempt", "a1",
             "--session", "fixture-session"], env=dict(self.env, T094_SCENARIO=scenario),
             capture_output=True, text=True, timeout=10)
        rows = [json.loads(s) for s in (self.root / "records/launches.jsonl").read_text().splitlines()]
        calls = [json.loads(s) for s in (self.root / "calls.jsonl").read_text().splitlines()]
        REPORTS.append(dict(scenario=scenario, command=r.args, exit_code=r.returncode,
                            stdout=r.stdout, stderr=r.stderr, rows=rows, herdr_calls=calls))
        self.assertEqual(sum(c[:2] == ['agent', 'start'] for c in calls), 1, calls)
        self.assertFalse(any(c[:2] == ['pane', 'close'] for c in calls), calls)
        self.assertEqual([r['phase'] for r in rows], ['prepared', 'started' if scenario == 'success' else 'failed'])
        self.assertEqual(rows[-1]['pane'], self.pane)
        return r, rows[-1], calls

    def test_error_keeps_stderr_stdout_and_retains_pane(self):
        r, row, calls = self.launch('busy')
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(row['error_code'], 'agent_pane_busy')
        self.assertIn('fixture readable cause', row['herdr_stderr'])
        self.assertIn('fixture stdout before failure', row['herdr_stdout'])
        self.assertEqual(row['outcome'], 'not_started')
        self.assertEqual(row['pane_disposition'], 'retained_for_controller')

    def test_busy_foreground_argv_is_in_error_identity(self):
        busy_argv = ['git', 'status', '--porcelain=v1', '--', '独立输入 ' + uuid.uuid4().hex[:12]]
        self.env['T094_BUSY_ARGV'] = json.dumps(busy_argv)
        r, row, calls = self.launch('busy-git')
        self.assertEqual(r.returncode, 1)
        self.assertEqual(row['error_code'], 'agent_pane_busy')
        self.assertEqual(row['busy_foreground']['foreground_process_group_id'], 60)
        self.assertEqual(row['busy_foreground']['processes'], [
            {'pid': 60, 'name': 'zsh', 'argv': ['-zsh']},
            {'pid': 71, 'name': 'git', 'argv': busy_argv}])
        for text in (row['error'], r.stderr):
            self.assertIn(json.dumps(busy_argv, ensure_ascii=False), text)
        after_start = calls[next(i for i, c in enumerate(calls) if c[:2] == ['agent', 'start']) + 1:]
        self.assertEqual(after_start, [['pane', 'process-info', '--pane', self.pane],
                                       ['agent', 'get', self.pane]])
        self.assertEqual(row['pane_disposition'], 'retained_for_controller')

    def test_process_started_without_registration_is_distinct(self):
        r, row, calls = self.launch('unregistered')
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(row['outcome'], 'started_unregistered')
        self.assertEqual(row['error_code'], 'agent_name_not_found')
        self.assertEqual(row['pane_disposition'], 'retained_for_controller')

    def test_registered_but_blocked_is_not_unregistered_or_success(self):
        r, row, _ = self.launch('blocked')
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(row['outcome'], 'started_not_ready')
        self.assertEqual(row['error_code'], 'agent_not_ready')
        self.assertEqual(row['pane_disposition'], 'retained_for_controller')

    def test_failed_registration_query_does_not_claim_unregistered(self):
        r, row, _ = self.launch('diagnostic-error')
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(row['outcome'], 'unknown')
        self.assertEqual(row['pane_disposition'], 'retained_for_controller')
        self.assertIn('fixture registration unknown', json.dumps(row['observations']))

    def test_live_process_and_null_name_is_unregistered(self):
        r, row, _ = self.launch('unregistered-null-name')
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(row['outcome'], 'started_unregistered')
        self.assertEqual(row['pane_disposition'], 'retained_for_controller')

    def test_success_keeps_the_pane(self):
        r, row, calls = self.launch('success')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(row['agent'], 'fixture-worker')
        self.assertFalse(any(c[:2] == ['pane', 'close'] for c in calls))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--launcher', type=Path, default=LAUNCHER)
    p.add_argument('--report', type=Path)
    args, other = p.parse_known_args()
    LAUNCHER = args.launcher.resolve()
    result = unittest.main(argv=[sys.argv[0], *other], exit=False).result
    if args.report:
        with args.report.open('x', encoding='utf-8') as f:
            json.dump(dict(launcher=str(LAUNCHER), tests=result.testsRun,
                           failures=len(result.failures), errors=len(result.errors), scenarios=REPORTS),
                      f, ensure_ascii=False, indent=2)
            f.write('\n')
    sys.exit(0 if result.wasSuccessful() else 1)
