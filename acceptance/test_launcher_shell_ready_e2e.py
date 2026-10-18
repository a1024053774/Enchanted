#!/usr/bin/env python3
"""T-079 public launcher/Git contract with an explicit Herdr boundary fixture.

No socket or model calls. Real Herdr timing evidence is supplied separately by
outside-sandbox.sh. Reuses the T-073 fixture and its independent trailer oracle.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import unittest
import uuid

import test_herdr_traceability_e2e as traceability

LAUNCHER = traceability.SCRIPTS / "launch-worker"


class LauncherContract(traceability.Contract):
    def setUp(self):
        super().setUp()
        self.home = self.root / "codex home 中文"
        self.home.mkdir()
        self.env["FAKE_SHELL_READS"] = str(self.root / "shell-reads.txt")
        self.env["FAKE_SHELL_EVENTS"] = str(self.root / "shell-events.jsonl")
        self.child_argv = ["conda", "shell.zsh", "hook", "独立参数-" + uuid.uuid4().hex[:12]]
        self.env["FAKE_CHILD_ARGV"] = json.dumps(self.child_argv)
        codex = self.fakebin / "codex"
        codex.write_text("#!" + sys.executable + "\nimport json, os, sys\nfrom pathlib import Path\n"
                         "if sys.argv[1:] != ['--version']: sys.exit(2)\n"
                         "with Path(os.environ['FAKE_VERSION_RECEIPTS']).open('a', encoding='utf-8') as f:\n"
                         " f.write(json.dumps(dict(argv=sys.argv[1:], returncode=0, stdout='codex-cli 0.162.1\\n')) + '\\n')\n"
                         "print('codex-cli 0.162.1')\n", encoding="utf-8")
        codex.chmod(0o755)
        (self.fakebin / "herdr").write_text("#!" + sys.executable + "\n" + '''
import json, os, shlex, sys, time
from pathlib import Path
args = sys.argv[1:]
with Path(os.environ['FAKE_CALLS']).open('a') as f:
 f.write(json.dumps(args) + '\\n')
counter = Path(os.environ['FAKE_SHELL_READS'])
reads = int(counter.read_text()) if counter.exists() else 0
def observe(kind, sample=None):
 with Path(os.environ['FAKE_SHELL_EVENTS']).open('a', encoding='utf-8') as f:
  f.write(json.dumps(dict(kind=kind, observed_ns=time.time_ns(), sample=sample)) + '\\n')
if args[:2] == ['pane', 'split']:
 values = dict(args[i+1].split('=',1) for i,v in enumerate(args) if v == '--env')
 Path(os.environ['FAKE_ENV']).write_text(json.dumps(values), encoding='utf-8')
 print(json.dumps({'result': {'pane': {'pane_id': 'fake:pane'}}}))
elif args[:2] == ['pane', 'run']:
 # Supports the known-bad baseline, without making its premature start pass.
 values = dict(v.split('=',1) for v in shlex.split(args[3])[1:])
 Path(os.environ['FAKE_ENV']).write_text(json.dumps(values), encoding='utf-8')
elif args[:2] == ['pane', 'process-info']:
 if os.environ.get('FAKE_PROCESS_HANG'):
  time.sleep(60)
 if os.environ.get('FAKE_PROCESS_ERROR'):
  print(json.dumps({'error': {'code': 'pane_not_found', 'message': 'fixture error'}}), file=sys.stderr)
  sys.exit(7)
 reads += 1
 counter.write_text(str(reads))
 shell = {'pid': 842, 'name': '-zsh'}
 sample = {'pane_id': 'fake:pane'}
 if os.environ.get('FAKE_CHILD_ALWAYS'):
  sample.update(shell_pid=842, foreground_process_group_id=842,
                foreground_processes=[shell, {'pid': 913, 'name': 'conda', 'argv': json.loads(os.environ['FAKE_CHILD_ARGV'])}])
 elif not os.environ.get('FAKE_NEVER_READY'):
  if reads == 2:
   sample.update(shell_pid=842, foreground_process_group_id=842,
                 foreground_processes=[shell, {'pid': 913, 'name': 'kiro-cli'}])
  elif reads == 3:
   sample.update(shell_pid=842, foreground_process_group_id=913,
                 foreground_processes=[shell])
  elif reads == 4:
   sample.update(shell_pid=842, foreground_process_group_id=842,
                 foreground_processes=[{'pid': 842, 'name': 'vim'}])
  elif reads >= 5:
   sample.update(shell_pid=842, foreground_process_group_id=842, foreground_processes=[shell])
 if os.environ.get('FAKE_WRONG_PANE'):
  sample['pane_id'] = 'another:pane'
 observe('process_info', sample)
 print(json.dumps({'result': {'process_info': sample}}))
elif args[:2] == ['agent', 'start']:
 observe('agent_start')
 if reads < 5:
  print(json.dumps({'error': {'code': 'agent_pane_busy', 'message': 'shell is still initializing'}}), file=sys.stderr)
  sys.exit(1)
 if os.environ.get('FAKE_FAIL_START'):
  print('explicit fake startup failure', file=sys.stderr)
  sys.exit(12)
 print(json.dumps({'result': {'type': 'agent_started', 'argv': ['codex', *args[args.index('--')+1:]]}}))
else:
 sys.exit(2)
''', encoding="utf-8")

    def run_command(self, argv, env=None, expected=0):
        result = subprocess.run(argv, cwd=self.root, env=env or self.env, text=True,
                                capture_output=True, timeout=40)
        traceability.COMMANDS.append(dict(case=self._testMethodName, argv=[str(v) for v in argv],
                                         cwd=str(self.root), exit_code=result.returncode,
                                         stdout=result.stdout, stderr=result.stderr))
        if expected is None:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def launch(self, attempt=None, env=None, expected=0):
        before = len(self.version_events())
        result = self.run_command([str(LAUNCHER), "--root", str(self.root), "--cwd", str(self.root),
                                  "--agent", "fixture-worker", "--project", "sentinel-project",
                                  "--task", self.task, "--attempt", attempt or self.attempt,
                                  "--session", self.session, "--codex-home", str(self.home)],
                                 env=env, expected=expected)
        if expected:
            return result
        launch = json.loads(result.stdout)["launch_id"]
        self.assert_start_version(launch, before)
        return launch

    def calls(self):
        return [json.loads(line) for line in (self.root / "fake-calls.jsonl").read_text().splitlines()]

    def test_delayed_shell_then_commit(self):
        # Contract inputs include unknown status, shell rc helper, a different
        # foreground group, and an exec-replaced shell PID before availability.
        launch = self.launch()
        calls = self.calls()
        self.assertEqual(calls[0][:2], ["pane", "split"])
        self.assertTrue(all(v[:2] == ["pane", "process-info"] for v in calls[1:-1]))
        self.assertEqual(calls[-1][:2], ["agent", "start"])
        events = [json.loads(line) for line in (self.root / "shell-events.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(sum(e["kind"] == "agent_start" for e in events), 1)
        stable_since = None
        saw_child = False
        for event in events:
            if event["kind"] == "agent_start":
                self.assertIsNotNone(stable_since, "前台仍有子进程或不是 shell 时不得启动")
                self.assertGreaterEqual(event["observed_ns"] - stable_since, 1500000000)
                break
            info = event["sample"]
            processes = info.get("foreground_processes", [])
            saw_child = saw_child or len(processes) > 1
            if (info.get("shell_pid") == 842 and info.get("foreground_process_group_id") == 842
                    and len(processes) == 1 and processes[0]["pid"] == 842 and processes[0]["name"] == "-zsh"):
                if stable_since is None:
                    stable_since = event["observed_ns"]
            else:
                stable_since = None
        self.assertTrue(saw_child, "夹具必须覆盖前台初始化子进程")
        env = self.managed_env()
        self.assertEqual(env["CODEX_HOME"], str(self.home))
        self.assertEqual(env["A2A_PROJECT"], "sentinel-project")
        self.assertEqual(env["A2A_TASK"], self.task)
        self.assertEqual(env["A2A_ATTEMPT"], self.attempt)
        self.assertEqual(env["A2A_SESSION"], self.session)
        self.assertEqual(env["A2A_ROLE"], "worker")
        self.assertEqual(env["A2A_LAUNCH"], launch)
        self.assertEqual(env["A2A_LAUNCHES"], str(self.root / "records/launches.jsonl"))
        self.assertEqual(env["GIT_CONFIG_COUNT"], "1")
        self.assertEqual(env["GIT_CONFIG_KEY_0"], "core.hooksPath")
        self.assertEqual(env["GIT_CONFIG_VALUE_0"], str(LAUNCHER.parent / "git-hooks"))
        rows = self.rows("launches.jsonl")
        self.assertEqual([row["phase"] for row in rows], ["prepared", "started"])
        fields = ("launch_id", "created_at", "project", "task", "attempt", "session", "role",
                  "cli", "cli_version", "model", "effort", "service_tier_requested", "cwd",
                  "project_commit", "launcher_commit", "role_card", "role_card_version", "argv")
        for key in fields:
            self.assertTrue(rows[0][key], key)
            self.assertEqual(rows[0][key], rows[1][key], key)
        self.assertEqual(rows[1]["native_session"], "unknown")
        self.git("commit", "--allow-empty", "-m", "T-079 fixture worker submission", env=env)
        self.assert_trailers(env, launch)

    def assert_wait_failure(self, flag, expected=1):
        self.launch(env=dict(self.env, **{flag: "1"}), expected=expected)
        rows = self.rows("launches.jsonl")
        self.assertEqual([row["phase"] for row in rows], ["prepared", "failed"])
        self.assertEqual(rows[-1]["pane"], "fake:pane")
        self.assertFalse(any(v[:2] == ["agent", "start"] for v in self.calls()))
        self.assertFalse(any(v[:2] == ["pane", "close"] for v in self.calls()))

    def test_unknown_shell_times_out(self):
        self.assert_wait_failure("FAKE_NEVER_READY")
        self.assertIn("30", self.rows("launches.jsonl")[-1]["error"])

    def test_child_foreground_times_out_with_argv(self):
        self.assert_wait_failure("FAKE_CHILD_ALWAYS")
        row = self.rows("launches.jsonl")[-1]
        self.assertEqual(row["shell_foreground"]["foreground_processes"][1]["argv"], self.child_argv)
        self.assertIn(json.dumps(self.child_argv, ensure_ascii=False), row["error"])
        self.assertIn(json.dumps(self.child_argv, ensure_ascii=False), traceability.COMMANDS[-1]["stderr"])

    def test_hung_status_query_times_out(self):
        self.assert_wait_failure("FAKE_PROCESS_HANG")
        self.assertEqual(len(self.calls()), 2)

    def test_status_error_is_not_retried(self):
        self.assert_wait_failure("FAKE_PROCESS_ERROR", expected=7)
        self.assertEqual(len(self.calls()), 2)

    def test_wrong_pane_is_rejected(self):
        self.assert_wait_failure("FAKE_WRONG_PANE")
        self.assertEqual(len(self.calls()), 2)

    def test_agent_start_failure_is_not_retried(self):
        self.launch(env=dict(self.env, FAKE_FAIL_START="1"), expected=12)
        self.assertEqual(self.rows("launches.jsonl")[-1]["phase"], "failed")
        self.assertEqual(sum(v[:2] == ["agent", "start"] for v in self.calls()), 1)
        self.assertFalse(any(v[:2] == ["pane", "close"] for v in self.calls()))


CASES = ("test_delayed_shell_then_commit", "test_child_foreground_times_out_with_argv", "test_unknown_shell_times_out", "test_hung_status_query_times_out",
         "test_status_error_is_not_retried", "test_wrong_pane_is_rejected", "test_agent_start_failure_is_not_retried")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--launcher", type=Path, default=LAUNCHER)
    parser.add_argument("--case", choices=CASES)
    args = parser.parse_args()
    LAUNCHER = args.launcher.resolve()
    traceability.ARTIFACTS = args.artifacts.resolve()
    traceability.ARTIFACTS.mkdir()
    suite = unittest.TestSuite(LauncherContract(name) for name in ([args.case] if args.case else CASES))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    (traceability.ARTIFACTS / "commands.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False)+"\n" for row in traceability.COMMANDS), encoding="utf-8")
    (traceability.ARTIFACTS / "summary.json").write_text(json.dumps(dict(tests=result.testsRun,
        failures=len(result.failures), errors=len(result.errors), launcher=str(LAUNCHER)), indent=2)+"\n", encoding="utf-8")
    sys.exit(0 if result.wasSuccessful() else 1)
