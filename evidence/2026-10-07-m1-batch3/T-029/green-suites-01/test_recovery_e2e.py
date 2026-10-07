"""T-007 frozen-contract acceptance through real CLI, SQLite and Git.

Run: python3 -B acceptance/test_recovery_e2e.py
COOP_SCRIPT can select an unmodified historical entry point. No product source
is read or imported. Reuse only the existing independent fixture helpers;
explicit suite membership prevents running the inherited T-006 tests.
"""
import datetime
import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
import uuid

import test_coop_e2e as helper


ROOT = helper.ROOT
SCRIPT = helper.SCRIPT
EVIDENCE = ROOT / "evidence" / "2026-10-06-recovery-01"
REF = helper.INTEGRATION_REF
COMMANDS = helper.COMMANDS
ARTIFACTS = helper.ARTIFACTS
ASSERTIONS = []
TEST_RESULTS = []
REAL_GIT = shutil.which("git")


class FixtureError(RuntimeError):
    """An environment or fault-injection error, never a product red state."""


# These programs operate outside production. An orphan finishes through its
# own release file; the fixture never signals an oracle, Git, Herdr or a pane.
ORACLE_BARRIER = '''
import contextlib, io, json, os, pathlib, sys, time, traceback, uuid
control = pathlib.Path(CONTROL)
identity = uuid.uuid4().hex
entry = control / (identity + ".entry.json")
release = control / (identity + ".release")
entry.write_text(json.dumps({"pid": os.getpid(), "ppid": os.getppid(),
    "argv": sys.argv, "candidate_directory": sys.argv[1],
    "release": str(release), "phase": "oracle"}), encoding="utf-8")
deadline = time.monotonic() + 40
while not release.exists() and not (control / "release-all").exists():
    if time.monotonic() > deadline:
        raise RuntimeError("fixture oracle barrier expired")
    time.sleep(0.02)
stdout, stderr = io.StringIO(), io.StringIO()
code = 0
with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
    try:
        exec(compile(ORACLE_SOURCE, "frozen-independent-pagination-oracle", "exec"))
    except SystemExit as exit:
        code = exit.code
    except Exception:
        traceback.print_exc()
        code = 1
(control / (identity + ".result.json")).write_text(json.dumps({
    "pid": os.getpid(), "argv": sys.argv, "exit_code": code,
    "stdout": stdout.getvalue(), "stderr": stderr.getvalue()}), encoding="utf-8")
try:
    sys.stdout.write(stdout.getvalue())
    sys.stderr.write(stderr.getvalue())
finally:
    (control / (identity + ".done")).write_text("oracle exited", encoding="utf-8")
sys.exit(code)
'''

GIT_BARRIER = '''
import json, os, pathlib, subprocess, sys, time, uuid
args = sys.argv[1:]
control = pathlib.Path(CONTROL)
if "update-ref" not in args or REF not in args:
    os.execv(REAL_GIT, [REAL_GIT] + args)
identity = uuid.uuid4().hex
phase = (control / "phase").read_text(encoding="utf-8")
release = control / (identity + ".release")
data = {"pid": os.getpid(), "ppid": os.getppid(), "argv": [REAL_GIT] + args,
        "phase": phase, "release": str(release)}
def save(suffix):
    (control / (identity + suffix)).write_text(json.dumps(data), encoding="utf-8")
def barrier():
    save(".entry.json")
    deadline = time.monotonic() + 40
    while not release.exists() and not (control / "release-all").exists():
        if time.monotonic() > deadline:
            raise RuntimeError("fixture Git barrier expired")
        time.sleep(0.02)
    return release.read_text(encoding="utf-8") if release.exists() else "abort"
if phase == "before" and barrier() == "abort":
    data["executed_real_git"] = False
    save(".done.json")
    sys.exit(125)
p = subprocess.run([REAL_GIT] + args, text=True, capture_output=True)
data.update({"executed_real_git": True, "exit_code": p.returncode,
             "stdout": p.stdout, "stderr": p.stderr})
save(".result.json")
if phase == "after":
    barrier()
sys.stdout.write(p.stdout)
sys.stderr.write(p.stderr)
save(".done.json")
sys.exit(p.returncode)
'''


def write_new(path, value):
    with Path(path).open("x", encoding="utf-8") as out:
        json.dump(value, out, ensure_ascii=False, indent=2)
        out.write("\n")


class RecoveryCLI(helper.ManagedDeliveryCLI):
    def setUp(self):
        self.handles = []
        self.controls = []
        self.sequence = 0
        self.business_failures = []
        self.addCleanup(self.cleanup_fixture)
        super().setUp()
        if not REAL_GIT:
            raise FixtureError("Real Git executable is unavailable")
        self.original_path = self.env.get("PATH", "")
        self.oracle_control = self.root / "oracle barrier"
        self.oracle_control.mkdir()
        self.controls.append(self.oracle_control)
        # create freezes this external oracle; later source changes are unused.
        source = ("CONTROL = " + repr(str(self.oracle_control)) + "\n" +
                  "ORACLE_SOURCE = " + repr(helper.ORACLE.read_text(encoding="utf-8")) +
                  "\n" + ORACLE_BARRIER)
        self.oracle.write_text(source, encoding="utf-8")
        self.artifact = ARTIFACTS[-1]
        self.artifact.update({"oracle_control": str(self.oracle_control),
                              "snapshots": [], "signals": [], "barriers": []})

    def check(self, condition, claim, expected, observed):
        assertion = {"test": self.id(), "claim": claim, "expected": expected,
                     "observed": observed, "pass": bool(condition)}
        ASSERTIONS.append(assertion)
        if not condition:
            self.business_failures.append(assertion)

    def finish_checks(self):
        if self.business_failures:
            self.fail("BUSINESS_RED " + json.dumps(self.business_failures,
                                                   ensure_ascii=False))

    def start_cli(self, command, *args):
        self.sequence += 1
        prefix = self.root / ("cli-%03d-%s" % (self.sequence, command))
        stdout_path = Path(str(prefix) + ".stdout")
        stderr_path = Path(str(prefix) + ".stderr")
        argv = self.cli_argv(command, *args)
        started = helper.utc_now()
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            p = subprocess.Popen(argv, cwd=str(self.root), env=self.env,
                                 stdout=stdout, stderr=stderr)
        handle = {"process": p, "argv": argv, "started": started,
                  "stdout_path": stdout_path, "stderr_path": stderr_path,
                  "command": command, "recorded": False}
        self.handles.append(handle)
        write_new(Path(str(prefix) + ".launch.json"), {
            "argv": argv, "pid": p.pid, "cwd": str(self.root), "started": started,
            "stdout_path": str(stdout_path), "stderr_path": str(stderr_path),
            "environment": {key: self.env.get(key) for key in
                            ("PATH", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM")}})
        return handle

    def complete(self, handle, timeout=12):
        p = handle["process"]
        try:
            p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            raise FixtureError("CLI exceeded fixture deadline: " + repr(handle["argv"]))
        result = subprocess.CompletedProcess(
            handle["argv"], p.returncode,
            handle["stdout_path"].read_text(encoding="utf-8"),
            handle["stderr_path"].read_text(encoding="utf-8"))
        if not handle["recorded"]:
            record = helper.record_process(handle["argv"], self.root, result,
                                           handle["started"], "coop:" + handle["command"])
            record.update({"pid": p.pid, "stdout_path": str(handle["stdout_path"]),
                           "stderr_path": str(handle["stderr_path"]),
                           "signal": -p.returncode if p.returncode < 0 else None})
            handle["recorded"] = True
        return result

    def kill_owned_cli(self, handle, reason):
        p = handle["process"]
        if p.poll() is not None:
            raise FixtureError("Target CLI exited before injection: " + reason)
        observation = self.process(["ps", "-p", str(p.pid), "-o", "pid=,ppid=,command="],
                                   label="fixture:confirm-owned-cli")
        if (observation.returncode != 0 or str(SCRIPT) not in observation.stdout or
                str(self.state) not in observation.stdout or
                self.task not in observation.stdout or p.poll() is not None):
            raise FixtureError("CLI PID identity could not be confirmed: " + observation.stdout)
        entry = {"pid": p.pid, "argv": handle["argv"], "signal": "SIGKILL",
                 "signal_number": signal.SIGKILL, "reason": reason,
                 "identity_check": observation.stdout, "at": helper.utc_now()}
        self.artifact["signals"].append(entry)
        p.send_signal(signal.SIGKILL)
        result = self.complete(handle)
        if result.returncode != -signal.SIGKILL:
            raise FixtureError("Expected owned CLI SIGKILL was not observed")
        entry["exit_code"] = result.returncode
        entry["alive_after"] = p.poll() is None

    def entries(self, control):
        return [(path, json.loads(path.read_text(encoding="utf-8")))
                for path in sorted(control.glob("*.entry.json"))]

    def wait_barrier(self, control, handle, prior=(), required=True):
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            matches = [(path, data) for path, data in self.entries(control)
                       if str(path) not in prior and data["ppid"] == handle["process"].pid]
            if matches:
                path, data = matches[0]
                if handle["process"].poll() is not None:
                    raise FixtureError("CLI died before a controlled barrier was reached")
                self.artifact["barriers"].append({"entry": str(path), **data})
                return path, data
            if handle["process"].poll() is not None:
                if not required:
                    return None
                result = self.complete(handle)
                raise FixtureError("Fault injector did not reach target boundary: " +
                                   result.stdout + result.stderr)
            time.sleep(0.02)
        raise FixtureError("Fault injector boundary timed out")

    def release(self, entry, action="continue"):
        path, data = entry
        Path(data["release"]).write_text(action, encoding="utf-8")
        self.artifact["barriers"].append({"released_entry": str(path),
                                         "action": action, "at": helper.utc_now()})

    def wait_done(self, entry):
        path, data = entry
        stem = path.name[:-11]
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            if any((path.parent / (stem + suffix)).exists()
                   for suffix in (".done", ".done.json")):
                return
            time.sleep(0.02)
        raise FixtureError("Released external wrapper did not finish")

    def snapshot(self, label):
        self.sequence += 1
        database = self.state / "state.sqlite3"
        tables = {}
        # Observe an unspecified schema without importing private code or writing
        # state. All tables/columns are retained for independent diagnosis.
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as db:
            db.row_factory = sqlite3.Row
            for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
                name = row[0]
                quoted = '"' + name.replace('"', '""') + '"'
                tables[name] = [dict(value) for value in db.execute("SELECT * FROM " + quoted)]
        log = self.process([REAL_GIT, "-C", str(self.repo), "reflog", "show",
                            "--format=%H %gs", REF], label="git:snapshot-reflog")
        if log.returncode != 0 and self.ref_or_missing() is not None:
            raise FixtureError("Cannot observe reflog of existing integration ref")
        value = {"label": label, "database": str(database), "tables": tables,
                 "status": self.status(), "events": self.events(),
                 "refs": self.git("show-ref").stdout,
                 "reflog": log.stdout, "reflog_exit": log.returncode,
                 "worktrees": self.git("worktree", "list", "--porcelain").stdout}
        path = self.root / ("snapshot-%03d-%s.json" % (self.sequence, label))
        write_new(path, value)
        self.artifact["snapshots"].append(str(path))
        return value

    def rows(self, snapshot, domain):
        return [json.loads(row["data"]) if "data" in row else row
                for name, rows in snapshot["tables"].items()
                if domain in name.lower() and "event" not in name.lower()
                for row in rows]

    def verification_id(self, snapshot):
        value = snapshot["status"]["verification"]
        if isinstance(value, dict):
            return value.get("verification_id")
        if value is None:
            rows = self.rows(snapshot, "verification")
            if len(rows) == 1:
                return rows[0].get("verification_id")
        return value

    def intent(self, snapshot):
        # The observed public status expands this domain entity. Preserve the
        # full read-only SQLite snapshot rather than prescribe a new table.
        value = snapshot["status"].get("integration_intent")
        if not isinstance(value, dict):
            raise FixtureError("Cannot observe persisted integration intent: " + repr(value))
        return value

    def same_intent(self, before, after):
        # Only state/recording timestamps may advance. G/M, verification and
        # any identity binding must remain exactly the original intent.
        excluded = {"state", "status", "accepted_at", "updated_at", "finished_at",
                    "completed_at"}
        left, right = self.intent(before), self.intent(after)
        binding = {key: value for key, value in left.items() if key not in excluded}
        self.check(all(right.get(key) == value for key, value in binding.items()),
                   "Recovery retains the original integration intent and bindings", binding, right)

    def preserved_history(self, before, after):
        self.check(after["events"][:len(before["events"])] == before["events"],
                   "Recovery preserves the complete prior event prefix", before["events"],
                   after["events"][:len(before["events"])])

    def ref_or_missing(self):
        p = self.process([REAL_GIT, "-C", str(self.repo), "rev-parse", "--verify",
                          "--quiet", REF], label="git:ref-or-missing")
        if p.returncode not in (0, 1):
            raise FixtureError("Cannot observe Git reference: " + p.stderr)
        return p.stdout.strip() if p.returncode == 0 else None

    def setup_candidate(self, verified=False):
        self.create()
        attempt = self.claim()
        candidate = self.candidate(attempt, good=True)
        self.submit(attempt, candidate)
        self.artifact.update({"attempt": attempt, "candidate_commit": candidate})
        if verified:
            handle = self.start_cli("verify", "--task", self.task)
            entry = self.wait_barrier(self.oracle_control, handle)
            self.release(entry)
            self.cli_result(self.complete(handle), ok=True)
        return attempt, candidate

    def cli_result(self, process, ok=None, error=None, claim=None):
        value = self.parse_cli(process)
        if claim:
            good = ((ok is None or value["ok"] is ok) and
                    (error is None or value.get("error") == error))
            self.check(good, claim, {"ok": ok, "error": error}, value)
        else:
            if ok is not None:
                self.assertIs(value["ok"], ok, value)
            if error is not None:
                self.assertEqual(value.get("error"), error, value)
        return value

    def install_git_wrapper(self, phase):
        control = self.root / ("git barrier " + phase)
        control.mkdir()
        self.controls.append(control)
        (control / "phase").write_text(phase, encoding="utf-8")
        bin_dir = self.root / "wrapped tools"
        bin_dir.mkdir()
        wrapper = bin_dir / "git"
        wrapper.write_text("#!" + sys.executable + "\nCONTROL = " + repr(str(control)) +
                           "\nREAL_GIT = " + repr(REAL_GIT) + "\nREF = " + repr(REF) +
                           "\n" + GIT_BARRIER, encoding="utf-8")
        wrapper.chmod(0o755)
        self.env["PATH"] = str(bin_dir) + os.pathsep + self.original_path
        return control

    def start_git_fault(self, phase):
        control = self.install_git_wrapper(phase)
        handle = self.start_cli("integrate", "--task", self.task)
        entry = self.wait_barrier(control, handle)
        data = entry[1]
        if phase == "after" and (not data.get("executed_real_git") or data.get("exit_code") != 0):
            raise FixtureError("After-CAS injection did not observe successful real Git CAS")
        before = self.snapshot("at-" + phase + "-CAS-barrier")
        self.kill_owned_cli(handle, phase + " real Git CAS")
        # Before-CAS must abort the orphan without writing the ref. After-CAS
        # releases an already completed real update; it cannot execute twice.
        (control / "phase").write_text("record-only", encoding="utf-8")
        self.release(entry, "abort")
        self.wait_done(entry)
        return control, before

    def busy_probe(self, command):
        started = time.monotonic()
        handle = self.start_cli(command, "--task", self.task)
        try:
            handle["process"].wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.check(False, "Concurrent " + command + " rejects immediately", "exit within 2s",
                       "still running after 2s")
            # Preserve the original operation. Release only this second caller's
            # external barriers, or stop its confirmed owned CLI if it has none.
            entries = [(path, data) for control in self.controls
                       for path, data in self.entries(control)
                       if data["ppid"] == handle["process"].pid]
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

    def cas_records(self, control):
        return [json.loads(path.read_text(encoding="utf-8"))
                for path in sorted(control.glob("*.result.json"))]

    def cleanup_fixture(self):
        for control in self.controls:
            (control / "release-all").write_text("abort", encoding="utf-8")
        for handle in self.handles:
            if handle["process"].poll() is None:
                try:
                    self.complete(handle, timeout=3)
                except FixtureError:
                    self.kill_owned_cli(handle, "cleanup of owned timed-out CLI")
            else:
                self.complete(handle)

    def test_live_verify_excludes_verify_and_integrate(self):
        attempt, candidate = self.setup_candidate()
        original = self.start_cli("verify", "--task", self.task)
        entry = self.wait_barrier(self.oracle_control, original)
        before = self.snapshot("live-oracle")
        for command in ("verify", "integrate"):
            self.busy_probe(command)
        self.check(len(self.entries(self.oracle_control)) == 1,
                   "Busy commands never start a second oracle", 1,
                   len(self.entries(self.oracle_control)))
        self.check(original["process"].poll() is None, "Original oracle owner remains live",
                   "live", original["process"].poll())
        self.release(entry)
        self.cli_result(self.complete(original), ok=True,
                        claim="Original live verify completes after barrier release")
        after = self.snapshot("live-oracle-released")
        self.check(after["status"]["state"] == "verified", "Original candidate becomes verified",
                   "verified", after["status"]["state"])
        self.check("verification_interrupted" not in json.dumps(after["events"]),
                   "Busy probes do not mark normal verification interrupted", False,
                   after["events"])
        self.check(self.ref() == self.base, "Live verification never integrates", self.base, self.ref())
        self.preserved_history(before, after)
        self.finish_checks()

    def test_live_integrate_excludes_verify_and_integrate(self):
        self.setup_candidate(verified=True)
        control = self.install_git_wrapper("before")
        original = self.start_cli("integrate", "--task", self.task)
        entry = self.wait_barrier(control, original)
        before = self.snapshot("live-integrate")
        for command in ("verify", "integrate"):
            self.busy_probe(command)
        self.check(len(self.entries(control)) == 1, "Busy commands never start a second CAS", 1,
                   len(self.entries(control)))
        self.release(entry)
        self.cli_result(self.complete(original), ok=True,
                        claim="Original live integration completes after barrier release")
        after = self.snapshot("live-integrate-released")
        self.check(after["status"]["state"] == "accepted", "Original integration is accepted",
                   "accepted", after["status"]["state"])
        self.same_intent(before, after)
        self.preserved_history(before, after)
        self.finish_checks()

    def test_interrupted_verify_gets_new_id_worktree_and_full_oracle(self):
        attempt, candidate = self.setup_candidate()
        original = self.start_cli("verify", "--task", self.task)
        old_entry = self.wait_barrier(self.oracle_control, original)
        before = self.snapshot("before-verify-kill")
        old_id = self.verification_id(before)
        if not old_id:
            raise FixtureError("Cannot observe original verification ID at oracle boundary")
        self.kill_owned_cli(original, "active independent oracle")
        prior = [str(path) for path, data in self.entries(self.oracle_control)]
        recovery = self.start_cli("verify", "--task", self.task)
        new_entry = self.wait_barrier(self.oracle_control, recovery, prior, required=False)
        self.check(new_entry is not None, "Recovery starts a new real independent oracle",
                   "new oracle barrier", new_entry[1] if new_entry else None)
        self.release(old_entry)
        self.wait_done(old_entry)
        if new_entry:
            self.check(recovery["process"].poll() is None,
                       "Orphan oracle completion cannot satisfy new blocked verification",
                       "live", recovery["process"].poll())
            self.check(new_entry[1]["candidate_directory"] != old_entry[1]["candidate_directory"],
                       "Recovery uses an independent verification worktree",
                       "new worktree", new_entry[1]["candidate_directory"])
            self.release(new_entry)
        self.cli_result(self.complete(recovery), ok=True,
                        claim="Fresh verify recovers after original CLI SIGKILL")
        after = self.snapshot("after-verify-recovery")
        new_id = self.verification_id(after)
        self.check(bool(new_id) and new_id != old_id, "Recovery creates a new verification ID",
                   "different from " + str(old_id), new_id)
        old_rows = [row for row in self.rows(after, "verification")
                    if old_id in row.values()]
        self.check(any("interrupted" in row.values() for row in old_rows),
                   "Old verification persists with explicit interrupted status", "interrupted", old_rows)
        self.check("verification_interrupted" in json.dumps(after["events"][len(before["events"]):]),
                   "Recovery appends verification_interrupted event", "verification_interrupted",
                   after["events"][len(before["events"]):])
        old_before = [row for row in self.rows(before, "verification") if old_id in row.values()]
        # State and completion metadata may change; original inputs must survive.
        frozen_keys = {"G", "C", "M", "session_id", "fence",
                       "candidate_commit", "attempt_id", "spec_rev", "base_commit",
                       "merged_commit", "oracle", "oracle_path", "workspace", "worktree",
                       "command_intent", "command_intent_json"}
        if len(old_before) == len(old_rows) == 1:
            inputs = {key: value for key, value in old_before[0].items() if key in frozen_keys}
            self.check(all(old_rows[0].get(key) == value for key, value in inputs.items()),
                       "Interrupted verification preserves its original frozen inputs", inputs, old_rows[0])
            result = old_rows[0].get("result") or {}
            self.check(result.get("returncode") in (None, "unknown"),
                       "Lost old oracle exit is unknown rather than fabricated success",
                       "unknown", result)
        new_verification = after["status"]["verification"]
        result = new_verification.get("result", {}) if isinstance(new_verification, dict) else {}
        self.check(new_id != old_id and result.get("returncode") == 0,
                   "Verified state is bound to the complete new oracle exit", "new oracle exit 0", result)
        self.check(Path(old_entry[1]["candidate_directory"]).is_dir(),
                   "Old verification worktree is retained", True,
                   Path(old_entry[1]["candidate_directory"]).is_dir())
        self.check(after["status"]["candidate_commit"] == candidate,
                   "Recovery retains the current candidate", candidate,
                   after["status"]["candidate_commit"])
        self.check(after["status"]["state"] == "verified", "Only the complete new oracle verifies",
                   "verified", after["status"]["state"])
        self.check(self.ref() == self.base, "Verification recovery leaves integration ref unchanged",
                   self.base, self.ref())
        self.preserved_history(before, after)
        self.finish_checks()

    def recover_integration(self, phase):
        attempt, candidate = self.setup_candidate(verified=True)
        control, before = self.start_git_fault(phase)
        expected = self.base if phase == "before" else candidate
        actual = self.ref()
        if actual != expected:
            raise FixtureError("Declared CAS injection boundary was not confirmed: " +
                               repr({"expected": expected, "actual": actual}))
        log_before = self.reflog()
        calls_before = len(self.cas_records(control))
        p = self.process(self.cli_argv("integrate", "--task", self.task),
                         label="coop:integration-recovery")
        self.cli_result(p, ok=True, claim="Integrate recovers the original " + phase + "-CAS intent")
        after = self.snapshot("after-" + phase + "-CAS-recovery")
        self.same_intent(before, after)
        self.check(after["status"]["state"] == "accepted", "Recovered integration becomes accepted",
                   "accepted", after["status"]["state"])
        self.check(self.ref() == candidate, "Recovered integration points at the verified candidate",
                   candidate, self.ref())
        expected_delta = 1 if phase == "before" else 0
        self.check(len(self.reflog().splitlines()) == len(log_before.splitlines()) + expected_delta,
                   "Recovery performs exactly the missing Git effect", expected_delta,
                   len(self.reflog().splitlines()) - len(log_before.splitlines()))
        self.check(len(self.cas_records(control)) == calls_before + expected_delta,
                   "Recovery does not issue a duplicate CAS after Git already changed", expected_delta,
                   len(self.cas_records(control)) - calls_before)
        self.preserved_history(before, after)
        accepted_log = self.reflog()
        p = self.process(self.cli_argv("integrate", "--task", self.task),
                         label="coop:integration-replay")
        self.parse_cli(p)
        replay = self.snapshot("after-integration-replay")
        self.check(self.reflog() == accepted_log, "Successful integration replay adds no reflog",
                   accepted_log, self.reflog())
        self.check(replay["status"] == after["status"], "Successful integration replay preserves state",
                   after["status"], replay["status"])
        self.same_intent(before, replay)
        self.finish_checks()

    def test_before_CAS_recovers_same_intent_once(self):
        self.recover_integration("before")

    def test_after_CAS_recovers_bookkeeping_without_Git_write(self):
        self.recover_integration("after")

    def unknown_reference(self, delete):
        attempt, candidate = self.setup_candidate(verified=True)
        control, before = self.start_git_fault("after")
        if delete:
            p = self.process([REAL_GIT, "-C", str(self.repo), "update-ref", "-d", REF, candidate],
                             label="git:external-delete")
            if p.returncode != 0:
                raise FixtureError("External reference deletion failed: " + p.stderr)
            external = None
        else:
            (self.repo / "external.txt").write_text("External writer after CAS\n", encoding="utf-8")
            self.git("add", "external.txt")
            self.git("commit", "-m", "Independent external third value")
            external = self.git("rev-parse", "HEAD").stdout.strip()
            p = self.process([REAL_GIT, "-C", str(self.repo), "update-ref", REF, external, candidate],
                             label="git:external-third-value")
            if p.returncode != 0:
                raise FixtureError("External reference fixture failed: " + p.stderr)
        if self.ref_or_missing() != external:
            raise FixtureError("External reference injection could not be confirmed")
        # Deleted refs have no reflog command output, so retain raw log presence.
        git_dir = Path(self.git("rev-parse", "--absolute-git-dir").stdout.strip())
        log_path = git_dir / "logs" / REF
        raw_log = log_path.read_text(encoding="utf-8") if log_path.exists() else None
        previous_events = self.events()
        for command, extra in (("integrate", []), ("integrate", []),
                               ("revoke", ["--reason", "Cannot bypass pending intent"]),
                               ("revise", ["--spec-rev", "2"])):
            p = self.process(self.cli_argv(command, "--task", self.task, *extra),
                             label="coop:unknown-ref-" + command)
            self.cli_result(p, ok=False,
                            error="needs_reconciliation" if command == "integrate" else None,
                            claim="Unknown ref rejects " + command + " without bypassing pending intent")
            status = self.status()
            self.check(status["state"] != "accepted", "Unknown ref is never accepted",
                       "not accepted", status["state"])
            self.check(self.ref_or_missing() == external, "Unknown ref remains unchanged",
                       external, self.ref_or_missing())
            current_log = log_path.read_text(encoding="utf-8") if log_path.exists() else None
            self.check(current_log == raw_log, "Unknown ref recovery never writes Git reflog",
                       raw_log, current_log)
            events = self.events()
            self.check(events[:len(previous_events)] == previous_events,
                       "Unknown ref rejection retains previous history", previous_events,
                       events[:len(previous_events)])
            previous_events = events
        # snapshot uses show-ref; a deleted integration ref still has repo HEAD.
        after = self.snapshot("unknown-ref-rejected")
        self.same_intent(before, after)
        self.preserved_history(before, after)
        self.check(len(self.cas_records(control)) == 1, "Unknown ref never retries Git CAS", 1,
                   len(self.cas_records(control)))
        self.finish_checks()

    def test_after_CAS_external_X_requires_reconciliation(self):
        self.unknown_reference(delete=False)

    def test_after_CAS_deleted_ref_requires_reconciliation(self):
        self.unknown_reference(delete=True)

    def stale_after_interruption(self, revise):
        old, candidate = self.setup_candidate()
        original = self.start_cli("verify", "--task", self.task)
        old_entry = self.wait_barrier(self.oracle_control, original)
        before = self.snapshot("before-stale-verify-kill")
        self.kill_owned_cli(original, "verify before identity invalidation")
        if revise:
            self.cli("revise", "--task", self.task, "--spec-rev", "2")
        else:
            self.cli("revoke", "--task", self.task, "--reason", "Revoked after interruption")
        current = self.claim(owner="replacement-after-interruption")
        self.submit(old, candidate, ok=False, error="stale_attempt")
        p = self.process(self.cli_argv("verify", "--task", self.task), label="coop:stale-verify")
        self.cli_result(p, ok=False, claim="Recovery never revives an invalidated candidate")
        status = self.status()
        self.check(status["candidate_commit"] is None, "Old candidate remains invalidated", None,
                   status["candidate_commit"])
        self.check(len(self.entries(self.oracle_control)) == 1,
                   "Invalidated candidate never starts another oracle", 1,
                   len(self.entries(self.oracle_control)))
        self.release(old_entry)
        self.wait_done(old_entry)
        replacement = self.candidate(current, good=True)
        self.submit(current, replacement)
        recovery = self.start_cli("verify", "--task", self.task)
        new_entry = self.wait_barrier(self.oracle_control, recovery)
        self.release(new_entry)
        self.cli_result(self.complete(recovery), ok=True,
                        claim="Current replacement candidate can be verified")
        self.cli("integrate", "--task", self.task)
        after = self.snapshot("replacement-accepted")
        self.check(self.ref() == replacement and self.ref() != candidate,
                   "Only replacement candidate integrates", replacement, self.ref())
        self.check(Path(old_entry[1]["candidate_directory"]).is_dir() and
                   Path(old["workspace"]).is_dir(), "Invalidated worktrees remain inspectable",
                   True, [old_entry[1]["candidate_directory"], old["workspace"]])
        old_id = self.verification_id(before)
        self.check(any(old_id in row.values() for row in self.rows(after, "verification")),
                   "Interrupted old verification is retained after identity invalidation", old_id,
                   self.rows(after, "verification"))
        self.preserved_history(before, after)
        self.finish_checks()

    def test_interrupted_verify_revoke_reclaim_rejects_old_identity(self):
        self.stale_after_interruption(revise=False)

    def test_interrupted_verify_spec_change_rejects_old_candidate(self):
        self.stale_after_interruption(revise=True)


class EvidenceResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        TEST_RESULTS.append({"test": test.id(), "status": "PASS"})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        product = isinstance(test, RecoveryCLI) and bool(test.business_failures)
        TEST_RESULTS.append({"test": test.id(), "status": "INCOMPLETE",
                             "classification": "business-red" if product else "fixture-error",
                             "traceback": self._exc_info_to_string(err, test)})

    def addError(self, test, err):
        super().addError(test, err)
        TEST_RESULTS.append({"test": test.id(), "status": "INCOMPLETE",
                             "classification": "fixture-error",
                             "traceback": self._exc_info_to_string(err, test)})


def run_suite():
    names = [name for name in RecoveryCLI.__dict__ if name.startswith("test_")]
    suite = unittest.TestSuite(RecoveryCLI(name) for name in names)
    result = unittest.TextTestRunner(verbosity=2, resultclass=EvidenceResult).run(suite)
    write_new(os.environ["COOP_E2E_TRACE"], {
        "results": TEST_RESULTS, "assertions": ASSERTIONS, "artifacts": ARTIFACTS,
        "commands": COMMANDS, "tests_run": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors)})
    return 0 if result.wasSuccessful() else 1


def main():
    if sys.argv[1:] == ["--run-suite"]:
        return run_suite()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    evidence_path = EVIDENCE / ("check-" + stamp + "-" + uuid.uuid4().hex[:8] + ".json")
    artifact_root = Path(tempfile.mkdtemp(prefix="a2a-recovery-check-"))
    for source, destination in ((Path(__file__), "recovery-acceptance-source.py"),
                                (Path(helper.__file__), "helper-source.py"),
                                (ROOT / ".project-map/specs/recovery-2026-10-06.md",
                                 "recovery-contract.md")):
        shutil.copyfile(source, artifact_root / destination)
    trace_path = artifact_root / "subprocess-trace.json"
    env = dict(os.environ, COOP_E2E_ARTIFACT_ROOT=str(artifact_root),
               COOP_E2E_TRACE=str(trace_path))
    argv = [sys.executable, "-B", str(Path(__file__).resolve()), "--run-suite"]
    started = helper.utc_now()
    completed = subprocess.run(argv, cwd=str(ROOT), env=env, text=True, capture_output=True)
    trace = json.loads(trace_path.read_text(encoding="utf-8")) if trace_path.is_file() else None
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT),
                          text=True, capture_output=True)
    record = {"role": "recovery-check", "ticket": "T-007",
              "contract": ".project-map/specs/recovery-2026-10-06.md",
              "status": "PASS" if completed.returncode == 0 else "INCOMPLETE",
              "started": started, "finished": helper.utc_now(),
              "command": ["python3", "-B", "acceptance/test_recovery_e2e.py"],
              "actual_command": argv, "COOP_SCRIPT": str(SCRIPT), "cwd": str(ROOT),
              "repository_head": head.stdout.strip(), "python": sys.version,
              "real_git": REAL_GIT, "exit_code": completed.returncode,
              "stdout": completed.stdout, "stderr": completed.stderr,
              "artifact_root": str(artifact_root), "trace_path": str(trace_path), "trace": trace,
              "independence": "Frozen recovery contract, no product import/source read, real "
                              "multi-process CLI, read-only SQLite, real Git CAS and reflog.",
              "limitations": ["No new Herdr/model or reliability claim.",
                              "Parent contract-red is not a repaired-candidate pass.",
                              "T-006 and representative gate mutant are controller-owned follow-up."]}
    write_new(evidence_path, record)
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    print("Acceptance evidence: " + str(evidence_path))
    print("Retained isolated artifacts: " + str(artifact_root))
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
