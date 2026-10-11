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

import test_herdr_traceability_e2e as traceability

LAUNCHER = traceability.SCRIPTS / "launch-worker"


class LauncherContract(traceability.Contract):
    def setUp(self):
        super().setUp()
        self.home = self.root / "codex home 中文"
        self.home.mkdir()
        self.env["FAKE_SHELL_READS"] = str(self.root / "shell-reads.txt")
        codex = self.fakebin / "codex"
        codex.write_text("#!" + sys.executable + "\nimport sys\n"
                         "if sys.argv[1:] != ['--version']: sys.exit(2)\n"
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
if args[:2] == ['pane', 'split']:
 values = [args[i+1] for i,v in enumerate(args) if v == '--env']
 Path(os.environ['FAKE_EXPORT']).write_text('export ' + ' '.join(shlex.quote(v) for v in values))
 print(json.dumps({'result': {'pane': {'pane_id': 'fake:pane'}}}))
elif args[:2] == ['pane', 'run']:
 # Supports the known-bad baseline, without making its premature start pass.
 Path(os.environ['FAKE_EXPORT']).write_text(args[3])
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
 if not os.environ.get('FAKE_NEVER_READY'):
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
 print(json.dumps({'result': {'process_info': sample}}))
elif args[:2] == ['agent', 'start']:
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
        result = self.run_command([str(LAUNCHER), "--root", str(self.root), "--cwd", str(self.root),
                                  "--agent", "fixture-worker", "--project", "sentinel-project",
                                  "--task", self.task, "--attempt", attempt or self.attempt,
                                  "--session", self.session, "--codex-home", str(self.home)],
                                 env=env, expected=expected)
        return result if expected else json.loads(result.stdout)["launch_id"]

    def calls(self):
        return [json.loads(line) for line in (self.root / "fake-calls.jsonl").read_text().splitlines()]

    def test_delayed_shell_then_commit(self):
        # Contract inputs include unknown status, shell rc helper, a different
        # foreground group, and an exec-replaced shell PID before availability.
        launch = self.launch()
        calls = self.calls()
        self.assertEqual([v[:2] for v in calls], [["pane", "split"],
                         *([["pane", "process-info"]] * 5), ["agent", "start"]])
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


CASES = ("test_delayed_shell_then_commit", "test_unknown_shell_times_out", "test_hung_status_query_times_out",
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
