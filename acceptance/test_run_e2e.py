"""Independent T-008 contract checks through CLI, Git and read-only SQLite.

Run: python3 -B acceptance/test_run_e2e.py
COOP_SCRIPT selects a frozen parent or a controller-owned candidate/mutant.
Herdr/Codex substitutes below establish isolated orchestration evidence only.
They do not establish a real Herdr, model, service-tier or reliability claim.
"""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import unittest
import uuid

import test_coop_e2e as helper
import test_recovery_e2e as recovery


ROOT = helper.ROOT
SCRIPT = helper.SCRIPT
EVIDENCE = ROOT / "evidence/2026-10-06-run-01"
CONTRACT = ROOT / ".project-map/specs/supervised-run-2026-10-06.md"
COMMANDS = helper.COMMANDS
ARTIFACTS = helper.ARTIFACTS
ASSERTIONS = recovery.ASSERTIONS
TEST_RESULTS = []
write_new = recovery.write_new


# This external executable implements only the public Herdr shapes documented
# by the skill and recorded in managed-01/live-02. It never calls real Herdr or
# runs a model. All requests, raw replies and simulated identities are retained.
HERDR_BOUNDARY = r'''
import fcntl, json, os, pathlib, sys, time, traceback, uuid
control = pathlib.Path(CONTROL)
argv = sys.argv[1:]
tool = pathlib.Path(sys.argv[0]).name
started = time.time()
def option(flag):
    return argv[argv.index(flag) + 1]
def reply(kind, **values):
    return {"id": "isolated:" + kind, "result": dict(type=kind, **values)}
def target(store):
    value = option("--pane") if "--pane" in argv else argv[2]
    for p in store["panes"].values():
        if value in (p["pane_id"], p.get("name")):
            return p
    raise LookupError(value)
def public(p):
    return {k: v for k, v in p.items() if k not in ("shell_pid", "agent_pid", "agent_argv", "prompted")}
code, stdout, stderr = 0, "", ""
# Freeze one post-prompt observation outside the store lock so the controller
# can replace the attempt before the old run continues. This is a boundary
# scheduling fixture, not a production fault switch.
if tool == "herdr" and argv[:2] == ["agent", "get"]:
    observed = json.loads((control / "store.json").read_text())
    try:
        p = target(observed)
        if (observed["scenario"] == "hold-observe" and p.get("prompted") and
                p.get("name") == "check-run" and not (control / "release-observe").exists()):
            # Only the old run's first observation owns this barrier. A later
            # controller reclaim must inspect the same pane without deadlocking.
            try:
                (control / "observe-once").mkdir()
            except FileExistsError:
                pass
            else:
                entry = control / (uuid.uuid4().hex + ".observe-entry.json")
                entry.write_text(json.dumps({"argv": sys.argv, "pid": os.getpid(), "pane_id": p["pane_id"]}))
                deadline = time.monotonic() + 12
                while not (control / "release-observe").exists():
                    if time.monotonic() >= deadline:
                        (control / "fixture-error").write_text("observation barrier expired")
                        break
                    time.sleep(0.02)
    except LookupError:
        pass
with (control / "lock").open("a") as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    store = json.loads((control / "store.json").read_text())
    try:
        if tool == "codex":
            if argv != ["--version"]:
                raise RuntimeError("Fixture forbids actual model execution")
            stdout = "codex-cli 0.160.1\n"
        elif argv == ["status"] or argv == ["status", "--json"]:
            stdout = json.dumps({"client": {"version": "isolated-0.9.3"},
                                 "server": {"status": "running", "version": "isolated-0.9.1"}}) + "\n"
        elif argv[:2] in (["pane", "list"], ["agent", "list"]):
            agents = argv[0] == "agent"
            key = "agents" if agents else "panes"
            value = reply(key + "_list", **{key: [public(p) for p in store["panes"].values()
                                                     if not agents or p.get("agent")]})
            stdout = json.dumps(value) + "\n"
        elif argv[:2] == ["pane", "split"]:
            if "--no-focus" not in argv:
                raise RuntimeError("Fixture requires explicit --no-focus")
            parent = target(store)
            number = store["next"]
            store["next"] += 1
            pane_id = "wcheck:p" + str(number)
            cwd = option("--cwd")
            p = {"pane_id": pane_id, "terminal_id": "isolated-term-" + str(number),
                 "workspace_id": "wcheck", "tab_id": "wcheck:t1", "cwd": cwd,
                 "foreground_cwd": cwd, "focused": False, "revision": 0,
                 "agent_status": "unknown", "shell_pid": 31000 + number,
                 "agent_pid": 42000 + number}
            store["panes"][pane_id] = p
            stdout = json.dumps(reply("pane_info", pane=public(p))) + "\n"
        elif argv[:2] == ["pane", "get"]:
            stdout = json.dumps(reply("pane_info", pane=public(target(store)))) + "\n"
        elif argv[:2] == ["pane", "process-info"]:
            p = target(store)
            is_agent = bool(p.get("agent"))
            pid = p["agent_pid"] if is_agent else p["shell_pid"]
            args = p.get("agent_argv", ["-zsh"])
            name = "codex" if is_agent else "zsh"
            info = {"pane_id": p["pane_id"], "shell_pid": p["shell_pid"],
                    "foreground_process_group_id": pid,
                    "foreground_processes": [{"pid": pid, "name": name, "argv": args,
                                              "argv0": name, "cmdline": " ".join(args), "cwd": p["cwd"]}]}
            if is_agent and p.get("prompted") and store["scenario"] == "helper-joins":
                # Shape observed in the real live-auto-01 failure: same Codex
                # group leader, a transient shell member without argv metadata.
                info["foreground_processes"].append({"pid": pid + 1000, "name": "zsh", "cwd": p["cwd"]})
            elif is_agent and p.get("prompted") and store["scenario"] == "leader-changed":
                info["foreground_process_group_id"] = pid + 2000
                info["foreground_processes"].append({"pid": pid + 2000, "name": "codex",
                    "argv": args, "argv0": "codex", "cmdline": " ".join(args), "cwd": p["cwd"]})
            stdout = json.dumps(reply("pane_process_info", process_info=info)) + "\n"
        elif argv[:2] == ["agent", "start"]:
            p = target(store)
            native = argv[argv.index("--") + 1:]
            p.update({"agent": "codex", "name": argv[2], "agent_status": "idle",
                      "interactive_ready": True, "revision": 2, "state_change_seq": 1,
                      "agent_argv": ["codex"] + native})
            if store["scenario"] == "startup-blocked":
                p["agent_status"] = "blocked"
                p["interactive_ready"] = False
                code = 1
                stderr = json.dumps({"error": {"code": "agent_not_ready",
                                               "message": "isolated approval waiting"}}) + "\n"
            else:
                stdout = json.dumps(reply("agent_started", agent=public(p), argv=p["agent_argv"])) + "\n"
        elif argv[:2] in (["agent", "get"], ["agent", "wait"]):
            stdout = json.dumps(reply("agent_info", agent=public(target(store)))) + "\n"
        elif argv[:2] in (["agent", "read"], ["pane", "read"]):
            p = target(store)
            stdout = "Isolated boundary: " + p["agent_status"] + ".\n"
            if p["agent_status"] == "blocked":
                stdout += "Permission required. Awaiting explicit approval.\n"
        elif argv[:2] == ["agent", "prompt"]:
            p = target(store)
            p["prompted"] = True
            p["agent_status"] = "done"
            p["state_change_seq"] += 1
            store["prompts"].append({"pane_id": p["pane_id"], "name": p["name"], "text": argv[3]})
            # The successful reply describes delivery, before subsequent live
            # identity changes. Nothing in this fixture submits a candidate.
            stdout = json.dumps(reply("agent_prompted", agent=public(p))) + "\n"
            if store["scenario"] == "identity-changed":
                p["terminal_id"] = "isolated-replaced-terminal"
                p["agent_status"] = "unknown"
            elif store["scenario"] == "post-prompt-blocked":
                p["agent_status"] = "blocked"
                p["interactive_ready"] = False
        elif argv[:2] == ["pane", "close"]:
            p = target(store)
            store["closes"].append(p["pane_id"])
            del store["panes"][p["pane_id"]]
            stdout = json.dumps(reply("pane_closed", pane_id=p["pane_id"])) + "\n"
        else:
            raise RuntimeError("Unsupported isolated boundary command: " + repr(argv))
    except LookupError as exc:
        code = 1
        stderr = json.dumps({"error": {"code": "pane_not_found", "message": str(exc)}}) + "\n"
    except Exception:
        code = 97
        stderr = traceback.format_exc()
        (control / "fixture-error").write_text(stderr)
    temporary = control / (uuid.uuid4().hex + ".store.tmp")
    temporary.write_text(json.dumps(store), encoding="utf-8")
    temporary.replace(control / "store.json")
    with (control / "boundary.jsonl").open("a", encoding="utf-8") as out:
        out.write(json.dumps({"layer": "isolated-herdr-codex-substitute", "pid": os.getpid(),
            "argv": sys.argv, "cwd": os.getcwd(), "started_epoch": started,
            "finished_epoch": time.time(), "exit_code": code, "stdout": stdout,
            "stderr": stderr, "panes_after": store["panes"], "prompts_after": len(store["prompts"]),
            "closes_after": store["closes"]}, ensure_ascii=False) + "\n")
sys.stdout.write(stdout)
sys.stderr.write(stderr)
sys.exit(code)
'''


class ContractMissing(AssertionError):
    """The requested new CLI contract is absent, not an old product defect."""


def scalar_values(value):
    """Read public event values without prescribing their nesting or keys."""
    if isinstance(value, dict):
        return [item for child in value.values() for item in scalar_values(child)]
    if isinstance(value, list):
        return [item for child in value for item in scalar_values(child)]
    return [value]


def named_values(value, name):
    if isinstance(value, dict):
        return ([value[name]] if name in value else []) + [item for child in value.values()
                                                        for item in named_values(child, name)]
    if isinstance(value, list):
        return [item for child in value for item in named_values(child, name)]
    return []


class RunCLI(recovery.RecoveryCLI):
    def setUp(self):
        super().setUp()
        # Use the independent frozen pagination oracle without a barrier unless
        # a particular test explicitly controls it.
        (self.oracle_control / "release-all").write_text("continue", encoding="utf-8")
        self.boundary = self.root / "isolated boundary"
        self.boundary.mkdir()
        self.bin = self.root / "external bin"
        self.bin.mkdir()
        self.parent_pane = "wcheck:p1"
        self.unrelated_pane = "wcheck:p2"
        panes = {}
        for number, name in ((1, "controller-sentinel"), (2, "unrelated-sentinel")):
            pane_id = "wcheck:p" + str(number)
            panes[pane_id] = {"pane_id": pane_id, "terminal_id": "sentinel-term-" + str(number),
                              "workspace_id": "wcheck", "tab_id": "wcheck:t1", "cwd": str(self.root),
                              "foreground_cwd": str(self.root), "focused": number == 1,
                              "agent": "codex", "name": name, "agent_status": "working",
                              "interactive_ready": False, "shell_pid": 31000 + number,
                              "agent_pid": 42000 + number, "agent_argv": ["codex"]}
        write_new(self.boundary / "store.json", {"panes": panes, "next": 3,
                  "scenario": "done-no-submit", "prompts": [], "closes": []})
        for tool in ("herdr", "codex"):
            executable = self.bin / tool
            executable.write_text("#!" + sys.executable + "\nCONTROL = " + repr(str(self.boundary)) +
                                  "\n" + HERDR_BOUNDARY, encoding="utf-8")
            executable.chmod(0o700)
        self.env.update({"PATH": str(self.bin) + os.pathsep + self.original_path,
                         "HERDR_ENV": "1", "HERDR_PANE_ID": self.parent_pane,
                         "HERDR_WORKSPACE_ID": "wcheck", "HERDR_TAB_ID": "wcheck:t1"})
        self.artifact.update({"evidence_layer": "isolated-orchestration",
                              "boundary": str(self.boundary),
                              "boundary_log": str(self.boundary / "boundary.jsonl")})
        self.addCleanup(self.boundary_health)
        self.sentinels = dict(panes)

    def boundary_health(self):
        # Release only the external fixture barrier before the inherited owned
        # CLI cleanup. Never signal Herdr or simulated process identities.
        (self.boundary / "release-observe").write_text("release", encoding="utf-8")
        marker = self.boundary / "fixture-error"
        if marker.exists():
            raise recovery.FixtureError(marker.read_text(encoding="utf-8"))

    def store(self):
        return json.loads((self.boundary / "store.json").read_text(encoding="utf-8"))

    def scenario(self, value):
        # Test-only fixture state; production SQLite is never written here.
        import fcntl
        with (self.boundary / "lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            store = self.store()
            store["scenario"] = value
            temp = self.boundary / (uuid.uuid4().hex + ".store.tmp")
            write_new(temp, store)
            temp.replace(self.boundary / "store.json")

    def run_args(self, seconds=3, name="check-run"):
        return ("--task", self.task, "--parent-pane", self.parent_pane,
                "--name", name, "--wait-seconds", str(seconds))

    def start_run(self, seconds=3):
        return self.start_cli("run", *self.run_args(seconds))

    def wait_prompt(self, handle, prior=0):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            store = self.store()
            if len(store["prompts"]) > prior:
                return store["prompts"][-1]["pane_id"]
            if handle["process"].poll() is not None:
                self.new_result(self.complete(handle), "run")
                self.check(False, "Valid run dispatches one prompt before ending", True, store)
                self.finish_checks()
            time.sleep(0.03)
        raise recovery.FixtureError("Run did not reach the isolated prompt boundary in 5 seconds")

    def current_attempt(self):
        snapshot = self.snapshot("read-current-attempt")
        current = snapshot["status"]["current_attempt"]
        if isinstance(current, dict):
            return current
        matches = [r for r in self.rows(snapshot, "attempt") if r.get("attempt_id") == current]
        if len(matches) != 1:
            raise recovery.FixtureError("Cannot observe the current attempt: " + repr(current))
        return matches[0]

    def guard(self, command, attempt, ok=True, error=None, task=None):
        p = self.process(self.cli_argv(command, "--task", task or self.task,
                                     "--attempt", attempt), label="coop:" + command + "-guard")
        value = self.new_result(p, command, ok=ok, error=error)
        return value

    def unchanged(self, before, after, claim):
        for key in ("status", "refs", "reflog", "worktrees"):
            self.check(before[key] == after[key], claim + ": " + key,
                       before[key], after[key])
        for domain in ("attempt", "verification", "integration"):
            self.check(self.rows(before, domain) == self.rows(after, domain),
                       claim + ": persisted " + domain,
                       self.rows(before, domain), self.rows(after, domain))
        self.preserved_history(before, after)

    def only_own_close(self, *own):
        store = self.store()
        self.check(store["closes"] == list(own), "Only explicitly owned panes are closed",
                   list(own), store["closes"])
        for pane_id, sentinel in self.sentinels.items():
            self.check(store["panes"].get(pane_id) == sentinel,
                       "Parent and unrelated pane identities remain unchanged: " + pane_id,
                       sentinel, store["panes"].get(pane_id))

    def failed_run(self, process, error=None):
        value = self.new_result(process, "run", ok=False, error=error)
        run = value.get("run")
        self.check(isinstance(run, dict) and bool(run.get("run_id")) and
                   run.get("outcome") != "completed", "Created failed run remains inspectable",
                   "run_id and non-completed outcome", run)
        self.check(self.ref() == self.base and self.status()["state"] != "accepted",
                   "Failure never accepts or updates integration ref", self.base, self.ref())
        if isinstance(run, dict):
            self.persisted_run_receipt(run)
        return value

    def persisted_run_receipt(self, run):
        # Events are the public persistence boundary. SQLite is retained only
        # as supporting raw evidence; no new table or internal layout is owed.
        events = self.events()
        run_id, outcome = run.get("run_id"), run.get("outcome")
        linked = [event for event in events if run_id in scalar_values(event) and
                  outcome in scalar_values(event)] if run_id and outcome else []
        self.check(bool(linked), "Public events persist run_id and final outcome together",
                   {"run_id": run_id, "outcome": outcome}, events)

    def new_result(self, process, command, ok=True, error=None):
        missing = process.returncode == 2 and (
            (command == "run" and "invalid choice: 'run'" in process.stderr) or
            (command in ("verify", "integrate", "reclaim") and
             "unrecognized arguments: --attempt" in process.stderr))
        if missing:
            ASSERTIONS.append({"test": self.id(), "claim": "New CLI contract exists",
                               "expected": command + " contract", "observed": process.stderr,
                               "pass": False, "classification": "expected-contract-red"})
            raise ContractMissing("EXPECTED_CONTRACT_RED new command/guard missing: " + command)
        marker = self.boundary / "fixture-error"
        if marker.exists():
            raise recovery.FixtureError(marker.read_text(encoding="utf-8"))
        try:
            return self.cli_result(process, ok=ok, error=error,
                                   claim="Frozen CLI result for " + command)
        except AssertionError:
            self.check(False, "Contract-valid CLI returns a JSON gate result: " + command,
                       "exit 0/1 and a JSON object", {"exit": process.returncode,
                       "stdout": process.stdout, "stderr": process.stderr})
            self.finish_checks()

    def test_run_entry_point_completes_registered_task(self):
        self.create()
        original_head = self.git("rev-parse", "HEAD").stdout.strip()
        handle = self.start_run(seconds=8)
        pane = self.wait_prompt(handle)
        attempt = self.current_attempt()
        candidate = self.candidate(attempt, good=True)
        self.submit(attempt, candidate)
        value = self.new_result(self.complete(handle), "run")
        run = value.get("run", {})
        self.check(bool(run.get("run_id")) and run.get("attempt_id") == attempt["attempt_id"] and
                   run.get("outcome") == "completed", "Completed run binds the dispatched attempt",
                   {"attempt_id": attempt["attempt_id"], "outcome": "completed"}, run)
        accepted = self.snapshot("automatic-run-accepted")
        self.check(value.get("task", {}).get("state") == "accepted" and
                   accepted["status"]["state"] == "accepted", "CLI and SQLite agree on accepted task",
                   "accepted", [value.get("task"), accepted["status"]])
        self.check(self.ref() == candidate and candidate != self.base,
                   "Automatic run integrates the explicit new Git candidate", candidate, self.ref())
        self.persisted_run_receipt(run)
        self.check(self.git("rev-parse", "HEAD").stdout.strip() == original_head,
                   "User branch remains at its original head", original_head,
                   self.git("rev-parse", "HEAD").stdout.strip())
        readback = self.root / "authoritative accepted readback"
        self.git("worktree", "add", "--detach", str(readback), self.ref())
        self.assert_novel_pagination_inputs(readback)
        self.only_own_close(pane)
        self.check(len(self.store()["prompts"]) == 1, "Normal run prompts exactly once", 1,
                   len(self.store()["prompts"]))
        self.check(Path(attempt["workspace"]).is_dir(), "Reclaim preserves attempt worktree", True,
                   Path(attempt["workspace"]).is_dir())
        self.finish_checks()

    def test_transient_shell_member_keeps_same_agent_owner(self):
        self.scenario("helper-joins")
        self.test_run_entry_point_completes_registered_task()

    def test_new_foreground_leader_is_not_owned_even_with_old_pid_present(self):
        self.create()
        self.scenario("leader-changed")
        handle = self.start_run(seconds=2)
        pane = self.wait_prompt(handle)
        self.failed_run(self.complete(handle))
        self.check(pane in self.store()["panes"] and not self.store()["closes"],
                   "Changed leader is not reclaimed as the old worker", "pane retained", self.store())
        self.check(self.ref() == self.base and not self.entries(self.oracle_control),
                   "Changed leader does not verify or integrate", self.base, self.ref())
        self.finish_checks()

    def test_verify_expected_attempt_uses_real_gate(self):
        attempt, candidate = self.setup_candidate()
        before = self.snapshot("before-new-verify-guard")
        p = self.process(self.cli_argv("verify", "--task", self.task,
                                     "--attempt", attempt["attempt_id"]), label="coop:verify-guard")
        if p.returncode == 2:
            after = self.snapshot("after-missing-verify-guard")
            self.check(before["status"] == after["status"] and before["refs"] == after["refs"],
                       "Missing guard cannot verify or change Git", before["status"], after["status"])
        self.new_result(p, "verify")
        self.check(self.ref() == self.base, "Verify never integrates", self.base, self.ref())
        self.check(self.status()["state"] == "verified", "Matching guard permits verification",
                   "verified", self.status()["state"])
        self.finish_checks()

    def test_integrate_expected_attempt_uses_real_git_gate(self):
        attempt, candidate = self.setup_candidate()
        self.cli("verify", "--task", self.task)
        before = self.snapshot("before-new-integrate-guard")
        self.guard("integrate", attempt["attempt_id"])
        after = self.snapshot("after-new-integrate-guard")
        self.check(after["status"]["state"] == "accepted" and self.ref() == candidate,
                   "Matching integrate guard advances actual Git and task", candidate, self.ref())
        self.check(before["reflog"] != after["reflog"], "First guarded integration records a Git update",
                   "new reflog entry", after["reflog"])
        self.finish_checks()

    def test_fixture_existing_dispatch_submit_oracle_integration_and_reclaim(self):
        """Trust preparation for the new external fixture on the old public API."""
        self.create()
        value = self.cli("dispatch", "--task", self.task, "--parent-pane", self.parent_pane,
                         "--name", "fixture-preparation")
        attempt = value["attempt"]
        pane = self.store()["prompts"][0]["pane_id"]
        self.check(self.status()["state"] != "accepted" and self.ref() == self.base,
                   "Simulated done never accepts during fixture preparation", self.base, self.ref())
        candidate = self.candidate(attempt, good=True)
        self.submit(attempt, candidate)
        self.cli("verify", "--task", self.task)
        self.cli("integrate", "--task", self.task)
        self.cli("reclaim", "--task", self.task)
        self.check(self.ref() == candidate and self.status()["state"] == "accepted",
                   "Existing real gates work with this external boundary", candidate, self.ref())
        self.check(len(self.entries(self.oracle_control)) == 1,
                   "Real frozen independent oracle executes once", 1,
                   len(self.entries(self.oracle_control)))
        self.only_own_close(pane)
        self.finish_checks()

    def test_done_without_submit_hits_deadline_and_cannot_accept_committed_candidate(self):
        self.create()
        before = self.snapshot("before-done-run")
        handle = self.start_run(seconds=2)
        pane = self.wait_prompt(handle)
        attempt = self.current_attempt()
        candidate = self.candidate(attempt, good=True)
        # An eligible real commit exists, but no explicit submit is sent.
        self.failed_run(self.complete(handle), error="run_deadline")
        after = self.snapshot("done-without-submit-ended")
        self.check(after["refs"] == before["refs"] and after["reflog"] == before["reflog"],
                   "Done and candidate commit do not move any Git ref", before["refs"], after["refs"])
        self.check(after["status"]["candidate_commit"] is None and
                   len(self.entries(self.oracle_control)) == 0,
                   "No submit means no persisted candidate and no oracle", None,
                   [after["status"]["candidate_commit"], self.entries(self.oracle_control)])
        self.check(self.git("rev-parse", "HEAD", cwd=attempt["workspace"]).stdout.strip() == candidate,
                   "Timeout preserves the unsubmitted real candidate", candidate,
                   self.git("rev-parse", "HEAD", cwd=attempt["workspace"]).stdout.strip())
        self.only_own_close(pane)
        self.finish_checks()

    def test_concurrent_duplicate_run_has_one_prompt_and_one_attempt(self):
        self.create()
        first = self.start_run(seconds=8)
        pane = self.wait_prompt(first)
        attempt = self.current_attempt()
        before = self.snapshot("before-concurrent-run")
        started = time.monotonic()
        p = self.process(self.cli_argv("run", *self.run_args(8, "duplicate-run")),
                         label="coop:duplicate-run")
        elapsed = time.monotonic() - started
        self.new_result(p, "run", ok=False, error="run_busy")
        self.check(elapsed < 3, "Second live run refuses promptly", "under 3 seconds", elapsed)
        after = self.snapshot("after-concurrent-run-rejection")
        self.unchanged(before, after, "Busy run cannot affect the first attempt")
        self.check(len(self.store()["prompts"]) == 1 and len(self.rows(after, "attempt")) == 1,
                   "Concurrent duplicate sends one prompt and creates one attempt", [1, 1],
                   [len(self.store()["prompts"]), len(self.rows(after, "attempt"))])
        candidate = self.candidate(attempt, good=True)
        self.submit(attempt, candidate)
        self.new_result(self.complete(first), "run")
        self.check(self.ref() == candidate, "First executor still completes", candidate, self.ref())
        self.only_own_close(pane)
        self.finish_checks()

    def test_invalid_wait_values_have_no_worker_or_business_side_effect(self):
        self.create()
        before = self.snapshot("before-invalid-wait")
        for value in ("0", "-1", "1.5", "true", "not-a-number", ""):
            p = self.process(self.cli_argv("run", *self.run_args(value)), label="coop:invalid-wait")
            if p.returncode == 2 and "invalid choice: 'run'" in p.stderr:
                self.new_result(p, "run")
            self.check(p.returncode in (1, 2), "Invalid wait is rejected: " + repr(value),
                       "exit 1 or syntax exit 2", p.returncode)
            if p.returncode in (0, 1):
                rejected = self.new_result(p, "run", ok=False)
                self.check(not rejected.get("run"), "Invalid wait returns no created run receipt",
                           None, rejected.get("run"))
            after = self.snapshot("invalid-wait-" + uuid.uuid4().hex[:6])
            self.unchanged(before, after, "Invalid wait has no side effect")
            self.check(not named_values(after["events"][len(before["events"]):], "run_id"),
                       "Invalid wait has no public run receipt", "no new run_id", after["events"])
            self.check(not self.store()["prompts"] and self.store()["next"] == 3,
                       "Invalid wait cannot split a pane or prompt", [0, 3],
                       [len(self.store()["prompts"]), self.store()["next"]])
        self.only_own_close()
        self.finish_checks()

    def test_replacement_attempt_is_not_verified_integrated_or_closed_by_old_run(self):
        self.create()
        self.scenario("hold-observe")
        old_run = self.start_run(seconds=10)
        old_pane = self.wait_prompt(old_run)
        old = self.current_attempt()
        deadline = time.monotonic() + 5
        while not list(self.boundary.glob("*.observe-entry.json")):
            if old_run["process"].poll() is not None:
                self.new_result(self.complete(old_run), "run")
                self.check(False, "Run observes its bound pane before completion", True, False)
                self.finish_checks()
            if time.monotonic() >= deadline:
                raise recovery.FixtureError("Cannot synchronize the old run's observation")
            time.sleep(0.03)
        self.cli("revoke", "--task", self.task, "--reason", "Independent attempt replacement")
        # The existing dispatch gate requires the old pane to be explicitly
        # reclaimed before dispatching another bound worker for this task.
        # The old run is still frozen at its external observation boundary.
        self.guard("reclaim", old["attempt_id"])
        value = self.cli("dispatch", "--task", self.task, "--parent-pane", self.parent_pane,
                         "--name", "replacement-worker")
        replacement = value["attempt"]
        new_pane = self.store()["prompts"][-1]["pane_id"]
        candidate = self.candidate(replacement, good=True)
        self.submit(replacement, candidate)
        before = self.snapshot("replacement-submitted-before-old-run-resumes")
        (self.boundary / "release-observe").write_text("release", encoding="utf-8")
        value = self.failed_run(self.complete(old_run), error="run_superseded")
        after = self.snapshot("superseded-run-ended")
        self.check(value.get("run", {}).get("attempt_id") == old["attempt_id"],
                   "Old run remains bound to its original attempt", old["attempt_id"], value.get("run"))
        self.check(after["status"] == before["status"] and after["status"]["state"] == "submitted",
                   "Old run leaves replacement submission unchanged", before["status"], after["status"])
        self.check(after["refs"] == before["refs"] and after["reflog"] == before["reflog"] and
                   not self.entries(self.oracle_control),
                   "Old run cannot verify or integrate the replacement", before["refs"], after["refs"])
        self.check(new_pane in self.store()["panes"] and new_pane not in self.store()["closes"],
                   "Replacement worker stays live", new_pane, self.store())
        closed = self.store()["closes"]
        self.check(closed in ([], [old_pane]), "Superseded run may clean only its historical pane",
                   [[], [old_pane]], closed)
        self.check(Path(old["workspace"]).is_dir() and Path(replacement["workspace"]).is_dir(),
                   "Both attempt worktrees remain inspectable", True,
                   [old["workspace"], replacement["workspace"]])
        self.only_own_close(*closed)
        self.preserved_history(before, after)
        self.finish_checks()

    def test_oracle_failure_is_not_success_and_reclaims_only_owned_pane(self):
        self.create()
        handle = self.start_run(seconds=8)
        pane = self.wait_prompt(handle)
        attempt = self.current_attempt()
        candidate = self.candidate(attempt, good=False)
        self.submit(attempt, candidate)
        before = self.snapshot("bad-candidate-submitted")
        self.failed_run(self.complete(handle))
        after = self.snapshot("oracle-rejected-run")
        self.check(after["refs"] == before["refs"] and after["reflog"] == before["reflog"],
                   "Oracle rejection leaves Git refs and reflog unchanged", before["refs"], after["refs"])
        results = [json.loads(p.read_text()) for p in self.oracle_control.glob("*.result.json")]
        self.check(len(results) == 1 and results[0]["exit_code"] != 0,
                   "Actual frozen independent oracle rejects the bad candidate", "one nonzero oracle",
                   results)
        self.only_own_close(pane)
        self.check(Path(attempt["workspace"]).is_dir(), "Rejected candidate worktree survives", True,
                   Path(attempt["workspace"]).is_dir())
        self.finish_checks()

    def test_startup_blocked_preserves_scene_without_prompt_or_close(self):
        self.create()
        self.scenario("startup-blocked")
        p = self.process(self.cli_argv("run", *self.run_args(2)), label="coop:startup-blocked-run")
        self.failed_run(p)
        self.check(not self.store()["prompts"] and len(self.store()["panes"]) == 3,
                   "Startup approval waiting preserves pane and sends no task", [0, 3],
                   [len(self.store()["prompts"]), len(self.store()["panes"])])
        self.only_own_close()
        self.finish_checks()

    def test_post_prompt_blocked_preserves_scene_without_answer_or_reprompt(self):
        self.create()
        self.scenario("post-prompt-blocked")
        handle = self.start_run(seconds=2)
        pane = self.wait_prompt(handle)
        self.failed_run(self.complete(handle))
        self.check(pane in self.store()["panes"] and len(self.store()["prompts"]) == 1,
                   "Approval waiting preserves worker and sends no second prompt", [True, 1],
                   [pane in self.store()["panes"], len(self.store()["prompts"])])
        self.only_own_close()
        self.finish_checks()

    def test_unknown_identity_cannot_succeed_or_close_replaced_terminal(self):
        self.create()
        self.scenario("identity-changed")
        handle = self.start_run(seconds=2)
        pane = self.wait_prompt(handle)
        self.failed_run(self.complete(handle))
        self.check(pane in self.store()["panes"] and
                   self.store()["panes"][pane]["terminal_id"] == "isolated-replaced-terminal",
                   "Unknown terminal identity is retained without guessed cleanup",
                   "isolated-replaced-terminal", self.store()["panes"].get(pane))
        self.check(not self.entries(self.oracle_control) and len(self.store()["prompts"]) == 1,
                   "Unknown identity has no oracle execution or automatic retry", [0, 1],
                   [len(self.entries(self.oracle_control)), len(self.store()["prompts"])])
        self.only_own_close()
        self.finish_checks()

    def test_stale_verify_integrate_guards_preserve_current_and_accepted_state(self):
        self.create()
        old = self.claim(owner="old-guard-owner")
        self.cli("revoke", "--task", self.task, "--reason", "Guard fixture replacement")
        current = self.claim(owner="current-guard-owner")
        candidate = self.candidate(current, good=True)
        self.submit(current, candidate)
        for command in ("verify", "integrate"):
            before = self.snapshot("before-stale-" + command)
            self.guard(command, old["attempt_id"], ok=False, error="stale_attempt")
            after = self.snapshot("after-stale-" + command)
            self.unchanged(before, after, "Stale " + command + " guard")
        self.check(not self.entries(self.oracle_control), "Stale guards start no oracle", [],
                   self.entries(self.oracle_control))
        self.guard("verify", current["attempt_id"])
        self.guard("integrate", current["attempt_id"])
        self.check(self.ref() == candidate and self.status()["state"] == "accepted",
                   "Matching guards permit normal acceptance", candidate, self.ref())
        for command in ("verify", "integrate"):
            before = self.snapshot("before-accepted-stale-" + command)
            self.guard(command, old["attempt_id"], ok=False, error="stale_attempt")
            after = self.snapshot("after-accepted-stale-" + command)
            self.unchanged(before, after, "Accepted idempotence still checks " + command + " ownership")
        before = self.snapshot("before-matching-integrate-replay")
        self.guard("integrate", current["attempt_id"])
        after = self.snapshot("after-matching-integrate-replay")
        self.unchanged(before, after, "Matching accepted integration replays without a Git write")
        self.finish_checks()

    def test_reclaim_guard_targets_history_and_rejects_foreign_and_unknown_attempt(self):
        self.create()
        old = self.cli("dispatch", "--task", self.task, "--parent-pane", self.parent_pane,
                       "--name", "historical-owner")["attempt"]
        old_pane = self.store()["prompts"][-1]["pane_id"]
        self.cli("revoke", "--task", self.task, "--reason", "Preserve history for guarded reclaim")
        current = self.claim(owner="current-owner")
        candidate = self.candidate(current, good=True)
        self.submit(current, candidate)
        other_task = "foreign-" + uuid.uuid4().hex
        self.create(task=other_task)
        foreign = self.cli("dispatch", "--task", other_task, "--parent-pane", self.parent_pane,
                           "--name", "foreign-owner")["attempt"]
        foreign_pane = self.store()["prompts"][-1]["pane_id"]
        before = self.snapshot("before-historical-reclaim")
        self.guard("reclaim", old["attempt_id"])
        after = self.snapshot("after-historical-reclaim")
        self.check(after["status"] == before["status"] and after["refs"] == before["refs"] and
                   after["reflog"] == before["reflog"],
                   "Historical reclaim does not revoke the current task or change Git", before["status"],
                   after["status"])
        self.only_own_close(old_pane)
        self.check(foreign_pane in self.store()["panes"],
                   "Foreign worker remains live", foreign_pane, self.store())
        # A second dispatch is legal after historical reclaim. Replaying the
        # old historical ID must then leave this new binding untouched.
        self.cli("revoke", "--task", self.task, "--reason", "Bind current replacement after cleanup")
        replacement = self.cli("dispatch", "--task", self.task, "--parent-pane", self.parent_pane,
                               "--name", "current-bound-owner")["attempt"]
        current_pane = self.store()["prompts"][-1]["pane_id"]
        before = self.snapshot("before-historical-reclaim-replay")
        self.guard("reclaim", old["attempt_id"])
        after = self.snapshot("after-historical-reclaim-replay")
        self.unchanged(before, after, "Historical reclaim replay is harmless")
        self.only_own_close(old_pane)
        self.check(current_pane in self.store()["panes"] and foreign_pane in self.store()["panes"],
                   "Current and foreign bound workers remain live", [current_pane, foreign_pane], self.store())
        for invalid in (foreign["attempt_id"], "unknown-" + uuid.uuid4().hex):
            before = self.snapshot("before-invalid-reclaim")
            foreign_before = self.business_state(other_task)
            self.guard("reclaim", invalid, ok=False)
            after = self.snapshot("after-invalid-reclaim")
            self.unchanged(before, after, "Invalid reclaim attempt leaves all bindings unchanged")
            self.check(self.business_state(other_task) == foreign_before,
                       "Cross-task reclaim does not revoke foreign task", foreign_before,
                       self.business_state(other_task))
            self.only_own_close(old_pane)
        self.check(all(Path(a["workspace"]).is_dir() for a in (old, current, replacement, foreign)),
                   "Guarded reclaim preserves every attempt worktree", True,
                   [a["workspace"] for a in (old, current, replacement, foreign)])
        self.finish_checks()

    def test_matching_reclaim_guard_is_idempotent_after_automatic_success(self):
        self.create()
        handle = self.start_run(seconds=8)
        pane = self.wait_prompt(handle)
        attempt = self.current_attempt()
        candidate = self.candidate(attempt, good=True)
        self.submit(attempt, candidate)
        self.new_result(self.complete(handle), "run")
        before = self.snapshot("before-accepted-reclaim-replay")
        self.guard("reclaim", attempt["attempt_id"])
        self.guard("reclaim", attempt["attempt_id"])
        after = self.snapshot("after-accepted-reclaim-replay")
        self.unchanged(before, after, "Accepted own reclaim replay retains task and Git")
        self.only_own_close(pane)
        self.finish_checks()

    def test_attempt_guards_preserve_existing_live_operation_lock(self):
        attempt, candidate = self.setup_candidate()
        (self.oracle_control / "release-all").unlink()
        handle = self.start_cli("verify", "--task", self.task, "--attempt", attempt["attempt_id"])
        deadline = time.monotonic() + 5
        while not self.entries(self.oracle_control):
            if handle["process"].poll() is not None:
                self.new_result(self.complete(handle), "verify")
                self.check(False, "Guarded verification runs the frozen oracle", True, False)
                self.finish_checks()
            if time.monotonic() > deadline:
                raise recovery.FixtureError("Guarded verification did not reach oracle boundary")
            time.sleep(0.03)
        entry = self.entries(self.oracle_control)[0]
        before = self.snapshot("guarded-live-oracle")
        for command in ("verify", "integrate"):
            self.guard(command, attempt["attempt_id"], ok=False, error="operation_busy")
        after = self.snapshot("guarded-busy-rejections")
        self.unchanged(before, after, "Attempt guards do not bypass existing operation lock")
        self.check(len(self.entries(self.oracle_control)) == 1,
                   "Busy guarded calls never launch a second oracle", 1,
                   len(self.entries(self.oracle_control)))
        self.release(entry)
        self.new_result(self.complete(handle), "verify")
        self.guard("integrate", attempt["attempt_id"])
        self.check(self.ref() == candidate and self.status()["state"] == "accepted",
                   "Original locked operation remains usable", candidate, self.ref())
        self.finish_checks()


class EvidenceResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        TEST_RESULTS.append({"test": test.id(), "status": "PASS"})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        category = ("expected-contract-red" if issubclass(err[0], ContractMissing) else
                    "business-red" if test.business_failures else "fixture-error")
        TEST_RESULTS.append({"test": test.id(), "status": "INCOMPLETE", "classification": category,
                             "traceback": self._exc_info_to_string(err, test)})

    def addError(self, test, err):
        super().addError(test, err)
        TEST_RESULTS.append({"test": test.id(), "status": "INCOMPLETE",
                             "classification": "fixture-error",
                             "traceback": self._exc_info_to_string(err, test)})


def run_suite():
    names = [name for name in RunCLI.__dict__ if name.startswith("test_")]
    suite = unittest.TestSuite(RunCLI(name) for name in names)
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
    stem = "check-" + stamp + "-" + uuid.uuid4().hex[:8]
    evidence_path = EVIDENCE / (stem + ".json")
    artifact_root = EVIDENCE / (stem + "-artifacts")
    artifact_root.mkdir(exist_ok=False)
    for source, name in ((Path(__file__), "run-acceptance-source.py"),
                         (Path(helper.__file__), "managed-helper-source.py"),
                         (Path(recovery.__file__), "recovery-helper-source.py"),
                         (CONTRACT, "run-contract.md"), (SCRIPT, "selected-entry-point.py")):
        shutil.copyfile(source, artifact_root / name)
    trace_path = artifact_root / "subprocess-trace.json"
    # Freeze executable bytes once: concurrent production edits cannot mix code
    # versions within this suite. No expected value is read from these bytes.
    frozen_script = artifact_root / "selected-entry-point.py"
    env = dict(os.environ, COOP_E2E_ARTIFACT_ROOT=str(artifact_root), COOP_E2E_TRACE=str(trace_path),
               COOP_SCRIPT=str(frozen_script))
    argv = [sys.executable, "-B", str(Path(__file__).resolve()), "--run-suite"]
    started = helper.utc_now()
    p = subprocess.run(argv, cwd=str(ROOT), env=env, text=True, capture_output=True)
    trace = json.loads(trace_path.read_text(encoding="utf-8")) if trace_path.is_file() else None
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True, capture_output=True)
    write_new(evidence_path, {
        "role": "run-check", "ticket": "T-008", "contract": str(CONTRACT.relative_to(ROOT)),
        "status": "PASS" if p.returncode == 0 else "INCOMPLETE",
        "started": started, "finished": helper.utc_now(),
        "command": ["python3", "-B", "acceptance/test_run_e2e.py"], "actual_command": argv,
        "COOP_SCRIPT": str(SCRIPT), "executed_source_snapshot": str(frozen_script),
        "cwd": str(ROOT), "repository_head": head.stdout.strip(),
        "python": sys.version, "real_git": recovery.REAL_GIT, "exit_code": p.returncode,
        "stdout": p.stdout, "stderr": p.stderr, "artifact_root": str(artifact_root),
        "trace_path": str(trace_path), "trace": trace,
        "independence": "Frozen contract; no product import or source-derived expected values. "
                        "Real CLI subprocesses, real Git and read-only SQLite observations.",
        "fixture_authorities": ["/Users/luckye/.agents/skills/herdr/SKILL.md",
                                "evidence/2026-10-06-managed-01/live-02/dispatch.json"],
        "limitations": ["Isolated orchestration only; real Herdr/Codex run is controller-owned.",
                        "New-command expected-red is not evidence of an old defect.",
                        "Counterfactual, candidate approval and ticket closure are controller-owned."]})
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    print("Acceptance evidence: " + str(evidence_path))
    print("Retained isolated artifacts: " + str(artifact_root))
    return p.returncode


if __name__ == "__main__":
    sys.exit(main())
