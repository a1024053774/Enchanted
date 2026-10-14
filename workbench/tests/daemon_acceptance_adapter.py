"""Lifecycle adapter for the original acceptance methods; no business overrides.

Original suites exercise delivery, recovery, and controlled thread orchestration.
Product requests always use the daemon-only CLI.
"""
from contextlib import closing
import json
import os
from pathlib import Path
import signal
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch
from legacy_quality_driver import QualityDriver, prepare_review_control

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / "acceptance/entry/a2a_gates.py"
CLI = ROOT / "workbench/src/gates/cli.ts"
DAEMON = ROOT / "workbench/src/daemon.ts"
HOST = ROOT / "workbench/tests/daemon_acceptance_host.ts"
os.environ["COOP_SCRIPT"] = str(ENTRY)
os.environ["COOP_NATIVE_ENTRY"] = str(CLI)
sys.path.insert(0, str(ROOT / "acceptance"))
import test_coop_e2e as delivery
import test_recovery_e2e as recovery
import test_run_e2e as orchestration
import test_cas_race as cas

DEFAULT_RUN_METHODS = frozenset({
    "test_verify_expected_attempt_uses_real_gate",
    "test_integrate_expected_attempt_uses_real_git_gate",
    "test_invalid_wait_values_have_no_worker_or_business_side_effect",
    "test_stale_verify_integrate_guards_preserve_current_and_accepted_state",
    "test_attempt_guards_preserve_existing_live_operation_lock",
})


class DaemonLifecycle:
    def setUp(self):
        self.daemons = []
        self.active_daemon = None
        self.host_processes = {}
        allocate = tempfile.mkdtemp
        artifact_root = Path(os.environ["COOP_E2E_ARTIFACT_ROOT"])

        def short_root(*args, **kwargs):
            if kwargs.get("dir") == str(artifact_root):
                kwargs = dict(kwargs, prefix="t-")
            return allocate(*args, **kwargs)

        # Only the fixture root allocation changes. Test names and state/repo
        # relationships remain those of the inherited acceptance helpers.
        with patch.object(delivery.tempfile, "mkdtemp", short_root):
            super().setUp()
        self.artifact = delivery.ARTIFACTS[-1]
        self.artifact["daemons"] = self.daemons
        self.artifact["lifecycle_log"] = str(self.root / "daemon-lifecycle.jsonl")
        for key in list(self.env):
            if key.startswith("A2A_") and key != "A2A_TEST_THREAD_CONTROL":
                del self.env[key]
        self.controlled = True
        if not hasattr(self, 'boundary'):
            self.boundary = self.root / 'isolated boundary'; self.boundary.mkdir()
            recovery.write_new(self.boundary / 'store.json', dict(threads={}, next=0, scenario='done-no-submit',
                                                                prompts=[], closes=[], archived={}))
        self.review_control = prepare_review_control(self.root)
        self.quality = QualityDriver(CLI, self.state, self.review_control, self.env)
        self.integration_scores = {}
        self.mutant_core = os.environ.get("COOP_E2E_MUTANT_CORE")
        self.artifact['evidence_layer'] = 'real-daemon-Git-gates; controlled-external-worker-and-reviewer'
        self.artifact['quality_driver'] = str(self.review_control / 'driver.jsonl')
        if not isinstance(self, recovery.RecoveryCLI):
            self.addCleanup(self.stop_daemon)
        self.prepare_git_router()
        self.start_daemon()

    def prepare_git_router(self):
        router = self.root / "daemon-git"
        router.mkdir()
        self.git_route = router / "target.json"
        real_git = shutil.which("git", path=self.env["PATH"])
        if not real_git:
            raise recovery.FixtureError("Real Git executable is unavailable for daemon routing")
        recovery.write_new(self.git_route, {"executable": real_git})
        script = ("#!" + sys.executable + "\nimport json,os,pathlib,sys\n"
                  + "control=pathlib.Path(" + repr(str(self.git_route)) + ")\n"
                  + "target=json.loads(control.read_text(encoding='utf-8'))['executable']\n"
                  + "with (control.parent/'invocations.jsonl').open('a',encoding='utf-8') as out:\n"
                  + "    out.write(json.dumps({'pid':os.getpid(),'ppid':os.getppid(),'target':target,'argv':sys.argv})+'\\n')\n"
                  + "os.execv(target,[target]+sys.argv[1:])\n")
        (router / "git").write_text(script, encoding="utf-8")
        (router / "git").chmod(0o755)
        self.daemon_path = str(router) + os.pathsep + self.env["PATH"]

    def install_git_wrapper(self, phase):
        control = super().install_git_wrapper(phase)
        target = self.root / "wrapped tools/git"
        pending = self.git_route.with_suffix(".next.json")
        recovery.write_new(pending, {"executable": str(target)})
        pending.replace(self.git_route)
        self.lifecycle("git_fault_route_selected", phase=phase, wrapper=str(target), control=str(control))
        return control

    def lifecycle(self, event, **value):
        record = {"at": delivery.utc_now(), "test": self.id(), "event": event, **value}
        with (self.root / "daemon-lifecycle.jsonl").open("a", encoding="utf-8") as out:
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def cli_argv(self, command, *args):
        if command == "create" and "--project" not in args:
            args = (*args, "--project", args[args.index("--task") + 1])
        if command == 'integrate' and '--score-file' not in args:
            task = str(args[args.index('--task') + 1]) if '--task' in args else self.task
            prepared = getattr(self, 'integration_scores', {}).get(task)
            if prepared:
                args = (*args, '--score-file', str(prepared['file']))
                self.quality.record('executor-score-argument', task=task, bound_attempt=prepared['attempt'], argv=list(map(str, args)))
        return super().cli_argv(command, *args)

    def process(self, argv, *args, **kwargs):
        result = super().process(argv, *args, **kwargs)
        values = list(map(str, argv))
        if hasattr(self, 'quality') and str(ENTRY) in values and '--state' in values:
            command = values[values.index('--state') + 2]
            if result.returncode == 0:
                reply = json.loads(result.stdout)
                if command in ('claim', 'dispatch'):
                    a = reply['attempt']; self.quality.preparation(a['task_id'], a, '手工 claim' if command == 'claim' else '受控 dispatch')
                if command == 'verify' and reply.get('task', {}).get('state') == 'reviewing':
                    self.quality.complete_review(reply['task']['task_id'], reply['task']['current_attempt'], reply['task']['candidate_commit'])
        return result

    def complete(self, handle, timeout=12):
        result = super().complete(handle, timeout)
        if handle['command'] == 'verify' and result.returncode == 0:
            reply = json.loads(result.stdout)
            if reply.get('task', {}).get('state') == 'reviewing':
                task = reply['task']; attempt = task['current_attempt']; review = task['review']
                binding = {'task': task['task_id'], 'attempt': attempt['attempt_id'], 'session': attempt['session_id'],
                           'fence': attempt['fence'], 'spec_rev': task['spec_rev'], 'card_snapshot_id': attempt['card_snapshot_id'],
                           'candidate': task['candidate_commit'], 'verification': task['verification']['verification_id'],
                           'review': review['review_id']}
                previous = handle.get('quality_review_followup')
                if previous is not None:
                    if previous['binding'] != binding or previous['phase'] != 'completed':
                        raise recovery.FixtureError('Review follow-up changed or remains incomplete; do not repeat it.')
                    self.lifecycle('review_driver_receipt_replayed', binding=binding)
                else:
                    # complete() also runs during cleanup. Its saved reviewing
                    # reply is historical, not a request to drive another turn.
                    handle['quality_review_followup'] = {'binding': binding, 'phase': 'started'}
                    self.lifecycle('review_driver_intent', binding=binding)
                    self.quality.complete_review(task['task_id'], attempt, task['candidate_commit'])
                    handle['quality_review_followup']['phase'] = 'completed'
                    self.lifecycle('review_driver_completed', binding=binding)
        return result

    def dispatch_candidate_attempt(self, task=None):
        task = task or self.task
        a = self.cli('dispatch', '--task', task, '--runtime-mode', 'approval-required')['attempt']
        self.prepare_executor_score(a)
        return a

    def prepare_executor_score(self, attempt):
        path = self.quality.score_file(attempt)
        self.integration_scores[attempt['task_id']] = {'attempt': attempt['attempt_id'], 'file': path}
        return path

    def score_file(self, attempt):
        return self.quality.score_file(attempt)

    def drive_executor_finalize(self, handle, attempt, candidate):
        self.quality.finalize_run(self.task, attempt, candidate)

    def claim(self, task=None, owner='independent-check'):
        method = self._testMethodName
        recovery_managed = {'test_live_integrate_excludes_verify_and_integrate', 'test_before_CAS_recovers_same_intent_once',
                            'test_after_CAS_recovers_bookkeeping_without_Git_write', 'test_after_CAS_external_X_requires_reconciliation',
                            'test_after_CAS_deleted_ref_requires_reconciliation',
                            'test_external_write_between_read_and_cas_is_preserved'}
        run_managed = {'test_integrate_expected_attempt_uses_real_git_gate', 'test_attempt_guards_preserve_existing_live_operation_lock'}
        replacement = method in {'test_interrupted_verify_revoke_reclaim_rejects_old_identity',
                                'test_interrupted_verify_spec_change_rejects_old_candidate'} and owner == 'replacement-after-interruption'
        guarded = method == 'test_stale_verify_integrate_guards_preserve_current_and_accepted_state' and owner == 'current-guard-owner'
        if owner == 'independent-check' and method in recovery_managed | run_managed or replacement or guarded:
            return self.dispatch_candidate_attempt(task)
        return super().claim(task=task, owner=owner)

    def daemon_command(self, command):
        p = self.process([sys.executable, "-B", ENTRY, "--state", self.state, command],
                         label="fixture:" + command)
        if p.returncode != 0:
            raise recovery.FixtureError("Explicit daemon command failed: " +
                                        repr({"command": command, "exit": p.returncode,
                                              "stdout": p.stdout, "stderr": p.stderr}))
        return self.parse_cli(p)

    def start_daemon(self):
        if self.active_daemon is not None:
            raise recovery.FixtureError("Fixture already owns a live daemon")
        endpoint = str(self.state.resolve() / "control.sock")
        if len(endpoint.encode("utf-8")) > 103:
            raise recovery.FixtureError("Fixture socket path exceeds 103 bytes: " + endpoint)
        record = {"generation": len(self.daemons) + 1, "state": str(self.state.resolve()),
                  "controlled_thread_service": self.controlled,
                  "test_host": bool(self.controlled or self.mutant_core),
                  "gate_module": self.mutant_core or str(ROOT / "workbench/src/gates/core.ts"),
                  "started": delivery.utc_now()}
        self.daemons.append(record)
        if record["test_host"]:
            prefix = self.root / ("host-%02d" % record["generation"])
            ready = prefix.with_suffix(".ready.json")
            stdout = prefix.with_suffix(".stdout")
            stderr = prefix.with_suffix(".stderr")
            argv = ["node", str(HOST), str(self.state.resolve()),
                    str(self.boundary.resolve()) if self.controlled else "-",
                    str(ready), record["gate_module"], str(self.review_control)]
            record.update({"launch_argv": argv, "ready": str(ready),
                           "stdout_path": str(stdout), "stderr_path": str(stderr)})
            with stdout.open("xb") as out, stderr.open("xb") as err:
                process = subprocess.Popen(argv, cwd=self.root, env=dict(self.env, PATH=self.daemon_path),
                                           stdout=out, stderr=err, start_new_session=True)
            record["pid"] = process.pid
            self.host_processes[process.pid] = process
            self.active_daemon = record
            self.lifecycle("test_host_launched", **record)
            deadline = time.monotonic() + 10
            while not ready.exists():
                if process.poll() is not None or time.monotonic() >= deadline:
                    record["launch_exit"] = process.poll()
                    raise recovery.FixtureError("Test host did not become ready: " +
                                                stdout.read_text(encoding="utf-8") +
                                                stderr.read_text(encoding="utf-8"))
                time.sleep(0.02)
            announced = json.loads(ready.read_text(encoding="utf-8"))
            if (announced["pid"] != process.pid or announced["root"] != record["state"] or
                    announced["gate"] != record["gate_module"]):
                raise recovery.FixtureError("Test host ready identity does not match its launch")
            record["host_ready"] = announced
        else:
            record["launch_argv"] = [sys.executable, "-B", str(ENTRY), "--state", str(self.state), "daemon_start"]
            original_path = self.env["PATH"]
            self.env["PATH"] = self.daemon_path
            try:
                result = self.daemon_command("daemon_start")
            finally:
                self.env["PATH"] = original_path
            record.update({"pid": result["pid"], "start_result": result})
            self.active_daemon = record
        status, observation = self.inspect_owned(record)
        record.update({"status": status, "identity_check": observation,
                       "socket_bytes": len(endpoint.encode("utf-8"))})
        self.lifecycle("daemon_ready", **record)

    def inspect_owned(self, record):
        status = self.daemon_command("daemon_status")
        pid = record["pid"]
        pid_file = self.state / "daemon.pid"
        seen = self.process(["/bin/ps", "-p", str(pid), "-o", "pid=,ppid=,command="],
                            label="fixture:confirm-owned-daemon")
        script = HOST if record["test_host"] else DAEMON
        if (status.get("pid") != pid or status.get("root") != record["state"] or
                not pid_file.is_file() or int(pid_file.read_text(encoding="utf-8")) != pid or
                seen.returncode != 0 or str(script) not in seen.stdout or
                record["state"] not in seen.stdout or
                (pid in self.host_processes and self.host_processes[pid].poll() is not None)):
            raise recovery.FixtureError("Owned daemon identity could not be confirmed: " +
                                        repr({"record": record, "status": status, "ps": seen.stdout}))
        return status, seen.stdout

    def wait_exit(self, record):
        pid = record["pid"]
        process = self.host_processes.get(pid)
        deadline = time.monotonic() + 10
        while True:
            if process is not None:
                code = process.poll()
                if code is not None:
                    record["process_exit"] = code
                    break
            else:
                seen = self.process(["/bin/ps", "-p", str(pid), "-o", "pid=,stat=,command="],
                                    label="fixture:wait-daemon-exit")
                if seen.returncode == 1 and not seen.stdout.strip():
                    break
                if seen.returncode not in (0, 1):
                    raise recovery.FixtureError("Daemon exit observation failed: " + seen.stderr)
            if time.monotonic() >= deadline:
                raise recovery.FixtureError("Owned daemon did not exit before fixture deadline")
            time.sleep(0.05)
        record["confirmed_exited"] = delivery.utc_now()
        self.lifecycle("daemon_exit_confirmed", **record)

    def capture_state(self, record):
        database = self.state / "state.sqlite3"
        if not database.is_file():
            raise recovery.FixtureError("Live fixture database is missing before daemon stop")
        with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as db:
            db.row_factory = sqlite3.Row
            tables = {}
            for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
                name = row[0]
                quoted = '"' + name.replace('"', '""') + '"'
                tables[name] = [dict(item) for item in db.execute("SELECT * FROM " + quoted)]
        snapshot = {"test": self.artifact["test"], "database": str(database.resolve()),
                    "captured_at": delivery.utc_now(), "phase": "before-daemon-stop",
                    "daemon_pid": record["pid"], "daemon_generation": record["generation"],
                    "tables": tables}
        destination = Path(os.environ["COOP_E2E_READBACK_ROOT"]) / (self.root.name + ".json")
        recovery.write_new(destination, snapshot)
        self.artifact["state_readback"] = str(destination)
        self.lifecycle("state_readback_saved", path=str(destination),
                       daemon_pid=record["pid"], daemon_generation=record["generation"])

    def stop_daemon(self):
        record = self.active_daemon
        if record is None:
            return
        self.inspect_owned(record)
        try:
            # Keep the live WAL/SHM available for a read-only query. Persist the
            # result outside the temporary fixture before closing the database.
            self.capture_state(record)
        finally:
            self.daemon_command("daemon_stop")
            self.wait_exit(record)
            if (self.state / "daemon.pid").exists() or (self.state / "control.sock").exists():
                raise recovery.FixtureError("Graceful daemon stop left its endpoint or PID file")
            record["stopped"] = delivery.utc_now()
            self.active_daemon = None
            self.lifecycle("daemon_stopped", **record)

    def cleanup_fixture(self):
        # RecoveryCLI registers this bound method before its own setup. Run its
        # unchanged barrier/client cleanup before stopping the owning daemon.
        try:
            super().cleanup_fixture()
        finally:
            self.stop_daemon()

    def start_cli(self, command, *args):
        handle = super().start_cli(command, *args)
        if self.active_daemon is None:
            raise recovery.FixtureError("Async CLI has no explicitly started fixture daemon")
        handle["daemon_generation"] = self.active_daemon["generation"]
        handle["daemon_pid"] = self.active_daemon["pid"]
        self.lifecycle("cli_started", argv=handle["argv"], client_pid=handle["process"].pid,
                       daemon_generation=handle["daemon_generation"], daemon_pid=handle["daemon_pid"])
        return handle

    def wait_barrier(self, control, handle, prior=(), required=True):
        record = self.active_daemon
        if (record is None or record["generation"] != handle["daemon_generation"] or
                record["pid"] != handle["daemon_pid"]):
            raise recovery.FixtureError("Barrier belongs to a different daemon generation")
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            matches = [(path, data) for path, data in self.entries(control)
                       if str(path) not in prior and data["ppid"] == record["pid"]]
            if matches:
                path, data = matches[0]
                if handle["process"].poll() is not None:
                    raise recovery.FixtureError("Client exited before the daemon barrier was reached")
                if Path(data["release"]).resolve().parent != control.resolve():
                    raise recovery.FixtureError("Barrier release escaped its fixture control directory")
                if "candidate_directory" in data:
                    workspace = Path(data["candidate_directory"]).resolve()
                    status = self.status()
                    verification = status.get("verification")
                    attempt = status.get("current_attempt")
                    if not verification or not attempt:
                        raise recovery.FixtureError("Oracle barrier has no current verification identity")
                    expected = self.state.resolve() / "worktrees" / self.task / (
                        self.task + "-a" + str(attempt["fence"]) + "-verify-" + str(verification.get("ordinal")))
                    if workspace != expected or workspace != Path(verification["workspace"]).resolve():
                        raise recovery.FixtureError("Oracle barrier does not belong to the current verification worktree")
                self.artifact["barriers"].append({"entry": str(path), **data,
                                                 "daemon_generation": record["generation"]})
                handle["barrier"] = {"entry": str(path), **data}
                self.lifecycle("barrier_reached", client_pid=handle["process"].pid,
                               daemon_generation=record["generation"], entry=str(path), data=data)
                return path, data
            if handle["process"].poll() is not None:
                if not required:
                    return None
                result = self.complete(handle)
                raise recovery.FixtureError("Daemon did not reach the controlled barrier: " +
                                            result.stdout + result.stderr)
            time.sleep(0.02)
        raise recovery.FixtureError("Daemon barrier exceeded fixture deadline")

    def kill_owned_cli(self, handle, reason):
        if reason in ("cleanup of owned timed-out CLI", "concurrent command did not reject promptly"):
            # These are client cleanup paths, never faults in the live owner.
            return super().kill_owned_cli(handle, reason)
        if reason not in ("active independent oracle", "before real Git CAS", "after real Git CAS",
                          "verify before identity invalidation"):
            raise recovery.FixtureError("Unknown daemon fault window: " + reason)
        record = self.active_daemon
        barrier = handle.get("barrier")
        if (record is None or record["generation"] != handle["daemon_generation"] or
                record["pid"] != handle["daemon_pid"] or handle["process"].poll() is not None or
                not barrier or barrier["ppid"] != record["pid"]):
            raise recovery.FixtureError("Fault target does not match the active daemon and barrier")
        status, observation = self.inspect_owned(record)
        endpoint = self.state / "control.sock"
        socket_stat = endpoint.lstat()
        if not stat.S_ISSOCK(socket_stat.st_mode):
            raise recovery.FixtureError("Owned endpoint is not a Unix socket")
        evidence = {"pid": record["pid"], "signal": "SIGKILL", "signal_number": signal.SIGKILL,
                    "reason": reason, "target": "owned-daemon", "identity_check": observation,
                    "daemon_generation": record["generation"], "client_pid": handle["process"].pid,
                    "status": status, "barrier": barrier, "at": delivery.utc_now()}
        self.artifact["signals"].append(evidence)
        self.lifecycle("daemon_sigkill_requested", **evidence)
        os.kill(record["pid"], signal.SIGKILL)
        result = self.complete(handle)
        value = self.parse_cli(result)
        evidence.update({"client_exit": result.returncode, "client_result": value})
        if result.returncode == 0 or value.get("error") != "daemon_call_failed":
            raise recovery.FixtureError("Disconnected client did not report the real daemon call failure")
        self.wait_exit(record)
        # Default daemon_start is detached: no parent wait status is available.
        # Record the signal request and independent disappearance, never invent -9.
        if (int((self.state / "daemon.pid").read_text(encoding="utf-8")) != record["pid"] or
                endpoint.lstat().st_ino != socket_stat.st_ino):
            raise recovery.FixtureError("Crashed daemon endpoint ownership changed before cleanup")
        endpoint.unlink()
        (self.state / "daemon.pid").unlink()
        evidence["endpoint_cleanup"] = ["control.sock", "daemon.pid"]
        self.active_daemon = None
        self.lifecycle("crashed_endpoint_removed", **evidence)
        # This is an explicit fixture restart, not a failed business-call retry.
        self.start_daemon()

    def busy_probe(self, command):
        started = time.monotonic()
        prior = {str(path) for control in self.controls for path, _ in self.entries(control)}
        handle = self.start_cli(command, "--task", self.task)
        try:
            handle["process"].wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.check(False, "Concurrent " + command + " rejects immediately", "exit within 2s",
                       "still running after 2s")
            # Only the new request's barriers may be released. Never terminate
            # the daemon that still owns the original blocked operation.
            entries = [(path, data) for control in self.controls
                       for path, data in self.entries(control)
                       if str(path) not in prior and data["ppid"] == handle["daemon_pid"]]
            if entries:
                for entry in entries:
                    self.release(entry, "abort")
            else:
                self.kill_owned_cli(handle, "concurrent command did not reject promptly")
                return
        result = self.complete(handle)
        self.check(time.monotonic() - started < 2,
                   "Concurrent " + command + " returns without waiting for the live owner",
                   "under 2s", time.monotonic() - started)
        self.cli_result(result, ok=False, error="operation_busy",
                        claim="Live operation excludes concurrent " + command)


class DaemonDelivery(DaemonLifecycle, delivery.ManagedDeliveryCLI):
    pass


class DaemonRecovery(DaemonLifecycle, recovery.RecoveryCLI):
    pass


class DaemonRun(DaemonLifecycle, orchestration.RunCLI):
    pass


class DaemonCAS(DaemonLifecycle, cas.CASRace):
    pass
