"""Independent CLI acceptance for managed-delivery contract v1.

Run with Python 3.9: python3 -B acceptance/test_coop_e2e.py
COOP_SCRIPT selects the entry point, including a controller-owned gate mutant.
No product module is imported or read. Expectations come from the frozen
contracts and literal requests; the reference is only a candidate fixture.
Each invocation saves raw output and command traces in a new check-*.json.
Temporary repositories are retained so failed runs remain inspectable.
"""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(os.environ.get("COOP_SCRIPT", str(ROOT / "acceptance/entry/a2a_gates.py"))).resolve()
EVIDENCE = ROOT / "evidence" / "2026-10-06-managed-01"
REFERENCE = ROOT / "acceptance" / "reference" / "pager.py"
ORACLE = ROOT / "acceptance" / "pagination_oracle.py"
CONTRACT = ROOT / "fixtures" / "pagination" / "CONTRACT.md"
STARTER = ROOT / "fixtures" / "pagination" / "pager.py"
INTEGRATION_REF = "refs/heads/main"
COMMANDS = []
ARTIFACTS = []


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def record_process(argv, cwd, process, started, label):
    entry = {
        "label": label, "argv": [str(arg) for arg in argv],
        "cwd": str(cwd), "started": started, "finished": utc_now(),
        "exit_code": process.returncode,
        "stdout": process.stdout, "stderr": process.stderr,
    }
    COMMANDS.append(entry)
    return entry


class ManagedDeliveryCLI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SCRIPT.is_file():
            raise AssertionError(
                "EXPECTED_RED missing feature: CLI entry point does not exist: "
                + str(SCRIPT))

    def setUp(self):
        run_root = Path(os.environ["COOP_E2E_ARTIFACT_ROOT"])
        self.root = Path(tempfile.mkdtemp(prefix=self._testMethodName + "-",
                                          dir=str(run_root)))
        self.repo = self.root / "isolated repo"
        self.state = self.root / "isolated state"
        self.repo.mkdir()
        self.env = dict(os.environ)
        # Only temporary Git repositories use these settings.
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
                    "GIT_COMMON_DIR", "GIT_CONFIG_COUNT"):
            self.env.pop(key, None)
        self.env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                         "GIT_TERMINAL_PROMPT": "0", "PYTHONDONTWRITEBYTECODE": "1"})
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Independent acceptance fixture")
        self.git("config", "user.email", "a2a-check@example.invalid")
        self.git("config", "core.logAllRefUpdates", "always")
        self.git("config", "commit.gpgsign", "false")
        shutil.copyfile(STARTER, self.repo / "pager.py")
        shutil.copyfile(CONTRACT, self.repo / "CONTRACT.md")
        self.git("add", "pager.py", "CONTRACT.md")
        self.git("commit", "-m", "Independent faulty starter")
        self.base = self.git("rev-parse", "HEAD").stdout.strip()
        self.oracle = self.root / "oracle snapshot source.py"
        shutil.copyfile(ORACLE, self.oracle)
        self.instructions = self.root / "instructions.txt"
        self.instructions.write_text(CONTRACT.read_text(encoding="utf-8"),
                                     encoding="utf-8")
        self.task = "check-" + uuid.uuid4().hex
        ARTIFACTS.append({"test": self.id(), "root": str(self.root),
                          "repo": str(self.repo), "state": str(self.state),
                          "base_commit": self.base, "task": self.task})

    def process(self, argv, cwd=None, input_text=None, label="process"):
        cwd = Path(cwd or self.root)
        argv = [str(arg) for arg in argv]
        started = utc_now()
        try:
            p = subprocess.run(argv, cwd=str(cwd), env=self.env,
                               input=input_text, text=True, capture_output=True,
                               timeout=45)
        except subprocess.TimeoutExpired as exc:
            COMMANDS.append({"label": label, "argv": argv, "cwd": str(cwd),
                             "started": started, "finished": utc_now(),
                             "timeout": 45, "stdout": str(exc.stdout or ""),
                             "stderr": str(exc.stderr or "")})
            self.fail("Timed out at real subprocess boundary: " + repr(argv))
        record_process(argv, cwd, p, started, label)
        return p

    def git(self, *args, cwd=None):
        p = self.process(["git", "-C", str(cwd or self.repo)] + list(args),
                         label="git")
        self.assertEqual(p.returncode, 0, p.stderr)
        return p

    def cli_argv(self, command, *args):
        return [sys.executable, "-B", str(SCRIPT), "--state", str(self.state),
                command] + [str(arg) for arg in args]

    def parse_cli(self, p):
        self.assertIn(p.returncode, (0, 1),
                      "Contract-valid command failed outside the gate: " + p.stderr)
        try:
            result = json.loads(p.stdout)
        except json.JSONDecodeError:
            self.fail("CLI must return one JSON object: " + repr(p.stdout))
        self.assertIsInstance(result, dict)
        self.assertIs(result.get("ok"), p.returncode == 0, result)
        if p.returncode == 1:
            self.assertIsInstance(result.get("error"), str, result)
            self.assertTrue(result["error"], result)
        return result

    def cli(self, command, *args, ok=True, error=None):
        p = self.process(self.cli_argv(command, *args), label="coop:" + command)
        result = self.parse_cli(p)
        self.assertEqual(p.returncode, 0 if ok else 1, result)
        if error is not None:
            self.assertEqual(result["error"], error, result)
        return result

    def create(self, task=None):
        task = task or self.task
        card = {
            "id": task, "source": None, "goal": self.instructions.read_text(encoding="utf-8"),
            "non_goals": ["不改变独立分页合同"], "paths": {"allow": ["."], "deny": []},
            "completion_conditions": [{"argv": [sys.executable, "-I", "-B", "-c",
                                                 self.oracle.read_text(encoding="utf-8"), "{worktree}"]}],
            "red_commands": [], "task_type": "后端逻辑", "repair_target": None,
            "complexity": "M", "executor": {"cli": "Codex", "model": "gpt-6.1-sol", "effort": "xhigh"},
            "base_commit": None, "writer": None,
        }
        self.card_source = self.root / (task + ".card.json")
        self.card_source.write_text(json.dumps(card, ensure_ascii=False), encoding="utf-8")
        self.cli("card_save", "--task", task, "--card", self.card_source, "--expected-version", "0")
        result = self.cli("create", "--task", task, "--repo", self.repo,
                          "--branch", INTEGRATION_REF, "--card-version", "1")
        self.assertIsInstance(result.get("task"), dict, result)
        self.assertEqual(result["task"]["spec_rev"], 1)
        self.assertTrue((self.state / "state.sqlite3").is_file())
        return result["task"]

    def claim(self, task=None, owner="independent-check", overlap_reason=None):
        task = task or self.task
        ordinal = self.status(task)["fence"] + 1
        extra = ("--overlap-reason", overlap_reason) if overlap_reason is not None else ()
        result = self.cli("claim", "--task", task, "--owner", owner, *extra)
        attempt = result.get("attempt")
        self.assertIsInstance(attempt, dict, result)
        for key in ("attempt_id", "session_id", "fence", "spec_rev", "workspace",
                    "base_commit"):
            self.assertIn(key, attempt)
        self.assertTrue(attempt["attempt_id"])
        self.assertTrue(attempt["session_id"])
        self.assertIs(type(attempt["fence"]), int)
        self.assertGreater(attempt["fence"], 0)
        self.assertEqual(attempt["base_commit"], self.base)
        workspace = Path(attempt["workspace"]).resolve()
        self.assertTrue(workspace.is_dir())
        self.assertNotEqual(workspace, self.repo.resolve())
        self.assertIn((self.state / "worktrees").resolve(), workspace.parents)
        self.assertEqual(workspace, (self.state / "worktrees" / task / f"{task}-a{ordinal}").resolve())
        self.assertEqual(self.git("symbolic-ref", "HEAD", cwd=workspace).stdout.strip(),
                         f"refs/heads/a2a/{task}-a{ordinal}")
        self.assertEqual(self.git("rev-parse", "HEAD", cwd=workspace).stdout.strip(),
                         self.base)
        return attempt

    def candidate(self, attempt, good):
        workspace = Path(attempt["workspace"])
        # This fixture is copied before calling production; it is not an answer
        # inferred from coop output, its internals, or a worker's test result.
        source = REFERENCE if good else STARTER
        shutil.copyfile(source, workspace / "pager.py")
        with (workspace / "pager.py").open("a", encoding="utf-8") as out:
            out.write("\n# Independent candidate " + uuid.uuid4().hex + "\n")
        self.git("add", "pager.py", cwd=workspace)
        self.git("commit", "-m", "Independent candidate fixture", cwd=workspace)
        commit = self.git("rev-parse", "HEAD", cwd=workspace).stdout.strip()
        self.assertEqual(len(commit), 40)
        self.assertNotEqual(commit, self.base)
        return commit

    def submit(self, attempt, commit, task=None, ok=True, error=None, **changes):
        identity = {"attempt": attempt["attempt_id"], "session": attempt["session_id"],
                    "fence": attempt["fence"], "spec-rev": attempt["spec_rev"]}
        identity.update(changes)
        args = ["--task", task or self.task]
        for key, value in identity.items():
            args.extend(["--" + key, str(value)])
        args.extend(["--commit", commit])
        return self.cli("submit", *args, ok=ok, error=error)

    def status(self, task=None):
        result = self.cli("status", "--task", task or self.task)
        task_record = result.get("task")
        self.assertIsInstance(task_record, dict, result)
        for key in ("state", "current_attempt", "candidate_commit", "verification"):
            self.assertIn(key, task_record)
        return task_record

    def business_state(self, task=None):
        record = self.status(task)
        return {key: record[key] for key in
                ("state", "current_attempt", "candidate_commit", "verification")}

    def assert_current_attempt(self, task_record, attempt):
        current = task_record["current_attempt"]
        # The contract fixes the association, but does not fix whether status
        # expands current_attempt or returns its ID.
        if isinstance(current, dict):
            current = current.get("attempt_id")
        self.assertEqual(current, attempt["attempt_id"])

    def ref(self):
        return self.git("rev-parse", INTEGRATION_REF).stdout.strip()

    def reflog(self):
        return self.git("reflog", "show", "--format=%H %gs", INTEGRATION_REF).stdout

    def events(self, task=None):
        result = self.cli("events", "--task", task or self.task)
        self.assertIsInstance(result.get("events"), list, result)
        self.assertTrue(all(isinstance(event, dict) for event in result["events"]))
        return result["events"]

    def assert_rejection_recorded(self, error, before, task=None):
        after = self.events(task)
        self.assertEqual(after[:len(before)], before, "Earlier events were changed")
        self.assertGreater(len(after), len(before), "Rejection event is missing")
        # Detail keys are unspecified; the stable public error must survive in
        # the new event(s), not merely appear in an older successful event.
        self.assertIn(error, json.dumps(after[len(before):], ensure_ascii=False))
        return after

    def assert_novel_pagination_inputs(self, workspace):
        # Literal expected values from CONTRACT.md, independent of either pager.
        cases = [
            ({"items": [{"id": "zebra-91", "ts": 14, "extra": {"k": [7]}},
                        {"id": "oak-03", "ts": -4, "value": "first"},
                        {"id": "pine-62", "ts": 14, "value": "tie"}],
              "limit": 1, "after": [13, "absent-needle"]},
             {"items": [{"id": "pine-62", "ts": 14, "value": "tie"}],
              "next_cursor": [14, "pine-62"]}),
            ({"items": [{"id": "zebra-91", "ts": 14, "extra": {"k": [7]}},
                        {"id": "pine-62", "ts": 14, "value": "tie"}],
              "limit": 100, "after": [14, "pine-62"]},
             {"items": [{"id": "zebra-91", "ts": 14, "extra": {"k": [7]}}],
              "next_cursor": None}),
            ({"items": [], "limit": False, "after": ["bad", 9]},
             {"error": "invalid_limit"}),
        ]
        for request, expected in cases:
            with self.subTest(request=request):
                p = self.process([sys.executable, "-B", str(workspace / "pager.py")],
                                 cwd=workspace, input_text=json.dumps(request),
                                 label="novel-pagination-input")
                COMMANDS[-1]["input"] = request
                COMMANDS[-1]["expected"] = expected
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual(json.loads(p.stdout), expected)

    def test_concurrent_claim_is_unique_persistent_and_task_specific(self):
        # Two independently named tasks prevent one fixed-ID answer from passing.
        for suffix in ("alpha", "beta"):
            task = self.task + "-" + suffix
            with self.subTest(task=task):
                self.create(task)
                clients = []
                for index in range(4):
                    argv = self.cli_argv("claim", "--task", task, "--owner",
                                         "race-owner-" + str(index))
                    started = utc_now()
                    p = subprocess.Popen(argv, cwd=str(self.root), env=self.env,
                                         text=True, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                    clients.append((argv, started, p))
                completed_clients = []
                # Reap every client before asserting, even when one is faulty.
                for argv, started, p in clients:
                    try:
                        stdout, stderr = p.communicate(timeout=45)
                    except subprocess.TimeoutExpired:
                        p.kill()
                        stdout, stderr = p.communicate()
                    completed = subprocess.CompletedProcess(argv, p.returncode,
                                                            stdout, stderr)
                    record_process(argv, self.root, completed, started, "concurrent-claim")
                    completed_clients.append(completed)
                outcomes = [(p, self.parse_cli(p)) for p in completed_clients]
                winners = [value for p, value in outcomes if p.returncode == 0]
                self.assertEqual(len(winners), 1, outcomes)
                self.assertEqual(sum(p.returncode == 1 for p, value in outcomes), 3)
                winner = winners[0]["attempt"]
                self.assert_current_attempt(self.status(task), winner)
                self.assertEqual(self.status(task), self.status(task),
                                 "Fresh CLI readers disagree on durable state")
                race_events = self.events(task)
                loser_codes = [value["error"] for p, value in outcomes if p.returncode == 1]
                for code in set(loser_codes):
                    recorded = sum(code in json.dumps(event, ensure_ascii=False)
                                   for event in race_events)
                    self.assertGreaterEqual(recorded, loser_codes.count(code),
                                            "Concurrent rejection events were lost")
                before = self.business_state(task)
                previous_events = self.events(task)
                duplicate = self.cli("create", "--task", task, "--repo", self.repo,
                                     "--branch", INTEGRATION_REF, "--card-version", "1", ok=False)
                self.assertEqual(self.business_state(task), before)
                self.assert_rejection_recorded(duplicate["error"], previous_events, task)
                self.cli("revoke", "--task", task, "--reason", "End this independent claim race before the next task")
                self.assertFalse(Path(winner["workspace"]).exists())
                self.assertEqual(self.git("rev-parse", f"refs/a2a/attempts/{task}/a1").stdout.strip(), self.base)

    def test_identity_gates_and_revocation_reject_old_verified_attempt(self):
        self.create()
        attempt = self.claim()
        commit = self.candidate(attempt, good=True)
        before = self.business_state()
        for field, value, error in (
                ("session", "wrong-session-" + uuid.uuid4().hex, "stale_session"),
                ("fence", attempt["fence"] + 31, "stale_fence"),
                ("spec-rev", attempt["spec_rev"] + 7, "stale_spec")):
            with self.subTest(field=field):
                events = self.events()
                self.submit(attempt, commit, ok=False, error=error, **{field: value})
                self.assertEqual(self.business_state(), before)
                self.assertEqual(self.ref(), self.base)
                self.assert_rejection_recorded(error, events)
        self.submit(attempt, commit)
        self.cli("verify", "--task", self.task)
        self.assertEqual(self.status()["state"], "verified")
        events = self.events()
        self.cli("revoke", "--task", self.task, "--reason", "Independent revocation probe")
        revoked = self.status()
        self.assertEqual(revoked["state"], "ready")
        self.assertIsNone(revoked["candidate_commit"])
        self.assertIsNone(revoked["verification"])
        self.assertFalse(Path(attempt["workspace"]).exists())
        self.assertEqual(self.git("rev-parse", f"refs/a2a/attempts/{self.task}/a1").stdout.strip(), commit)
        self.assertEqual(self.git("rev-parse", f"refs/heads/a2a/{self.task}-a1").stdout.strip(), commit)
        retained = self.events()
        self.assertEqual(retained[:len(events)], events)
        denied = self.cli("integrate", "--task", self.task, ok=False)
        self.assertEqual(self.ref(), self.base)
        self.assert_rejection_recorded(denied["error"], retained)
        current = self.claim(owner="replacement-owner")
        self.assertGreater(current["fence"], attempt["fence"])
        self.assertNotEqual(current["attempt_id"], attempt["attempt_id"])
        self.assertNotEqual(current["session_id"], attempt["session_id"])
        before = self.business_state()
        events = self.events()
        self.submit(attempt, commit, ok=False, error="stale_attempt")
        self.assertEqual(self.business_state(), before)
        self.assert_current_attempt(self.status(), current)
        self.assert_rejection_recorded("stale_attempt", events)

    def test_unverified_and_oracle_failed_candidate_never_changes_ref(self):
        self.create()
        attempt = self.claim()
        commit = self.candidate(attempt, good=False)
        self.submit(attempt, commit)
        submitted = self.status()
        self.assertEqual(submitted["state"], "submitted")
        self.assertEqual(submitted["candidate_commit"], commit)
        events = self.events()
        denied = self.cli("integrate", "--task", self.task, ok=False)
        self.assertEqual(self.business_state(), {key: submitted[key] for key in
                         ("state", "current_attempt", "candidate_commit", "verification")})
        self.assertEqual(self.ref(), self.base)
        self.assert_rejection_recorded(denied["error"], events)
        events = self.events()
        self.cli("verify", "--task", self.task, ok=False, error="oracle_failed")
        self.assertNotIn(self.status()["state"], ("verified", "accepted"))
        self.assertEqual(self.ref(), self.base)
        self.assert_rejection_recorded("oracle_failed", events)
        events = self.events()
        denied = self.cli("integrate", "--task", self.task, ok=False)
        self.assertEqual(self.ref(), self.base)
        self.assert_rejection_recorded(denied["error"], events)

    def test_oracle_rejects_candidate_missing_limit_upper_bound(self):
        self.create()
        attempt = self.claim()
        workspace = Path(attempt["workspace"])
        reference = REFERENCE.read_text(encoding="utf-8")
        self.assertEqual(reference.count("not 1 <= limit <= 100"), 1)
        (workspace / "pager.py").write_text(
            reference.replace("not 1 <= limit <= 100", "limit < 1", 1), encoding="utf-8")
        self.git("add", "pager.py", cwd=workspace)
        self.git("commit", "-m", "Known-bad candidate omits limit upper bound", cwd=workspace)
        commit = self.git("rev-parse", "HEAD", cwd=workspace).stdout.strip()
        self.submit(attempt, commit)
        self.cli("verify", "--task", self.task, ok=False, error="oracle_failed")
        self.assertNotIn(self.status()["state"], ("verified", "accepted"))
        self.assertEqual(self.ref(), self.base)

    def test_good_candidate_uses_oracle_snapshot_and_integrates_once(self):
        self.create()
        attempt = self.dispatch_candidate_attempt()
        commit = self.candidate(attempt, good=True)
        self.assert_novel_pagination_inputs(Path(attempt["workspace"]))
        # Replacing the caller-owned source must not replace the registered oracle.
        self.oracle.write_text("import sys\nprint('changed oracle source')\nsys.exit(23)\n",
                               encoding="utf-8")
        changed_card = json.loads(self.card_source.read_text(encoding="utf-8"))
        changed_card["completion_conditions"][0]["argv"] = [sys.executable, "-c", "import sys; sys.exit(23)"]
        self.card_source.write_text(json.dumps(changed_card), encoding="utf-8")
        self.cli("card_save", "--task", self.task, "--card", self.card_source, "--expected-version", "1")
        self.submit(attempt, commit)
        self.assertEqual(self.status()["state"], "submitted")
        self.assertEqual(self.ref(), self.base)
        self.cli("verify", "--task", self.task)
        verified = self.status()
        self.assertEqual(verified["state"], "verified")
        self.assertEqual(verified["candidate_commit"], commit)
        self.assertIsNotNone(verified["verification"])
        self.assert_current_attempt(verified, attempt)
        log_before = self.reflog()
        self.cli("integrate", "--task", self.task)
        self.assertEqual(self.ref(), commit)
        accepted = self.status()
        self.assertEqual(accepted["state"], "accepted")
        self.assertEqual(accepted["candidate_commit"], commit)
        self.assertEqual(accepted["verification"], verified["verification"])
        log_after = self.reflog()
        self.assertEqual(len(log_after.splitlines()), len(log_before.splitlines()) + 1)
        events = self.events()
        # Replay may report a no-op success or a stable rejection. The contract
        # requires exactly one effect, rather than a particular replay status.
        replay = self.process(self.cli_argv("integrate", "--task", self.task),
                              label="coop:integrate-replay")
        result = self.parse_cli(replay)
        self.assertEqual(self.ref(), commit)
        self.assertEqual(self.reflog(), log_after, "Integration replay wrote the ref again")
        self.assertEqual(self.business_state(), {key: accepted[key] for key in
                         ("state", "current_attempt", "candidate_commit", "verification")})
        if not result["ok"]:
            self.assert_rejection_recorded(result["error"], events)
        for command, extra in (("revoke", ["--reason", "cannot undo accepted"]),
                               ("revise", ["--spec-rev", "2"])):
            events = self.events()
            rejected = self.cli(command, "--task", self.task, *extra, ok=False)
            self.assertEqual(self.status()["state"], "accepted")
            self.assertEqual(self.ref(), commit)
            self.assertEqual(self.reflog(), log_after)
            self.assert_rejection_recorded(rejected["error"], events)

    def test_baseline_change_after_verification_revalidates_and_integrates(self):
        self.create()
        attempt = self.dispatch_candidate_attempt()
        candidate = self.candidate(attempt, good=True)
        self.submit(attempt, candidate)
        first = self.cli("verify", "--task", self.task)["verification"]
        self.assertEqual(self.status()["state"], "verified")
        (self.repo / "external-change.txt").write_text("Independent baseline change\n",
                                                       encoding="utf-8")
        self.git("add", "external-change.txt")
        self.git("commit", "-m", "External change after verification")
        external = self.git("rev-parse", "HEAD").stdout.strip()
        log_before = self.reflog()
        events = self.events()
        self.cli("integrate", "--task", self.task)
        state = self.status()
        v = state["verification"]
        self.assertEqual(state["state"], "accepted")
        self.assertNotEqual(v["verification_id"], first["verification_id"])
        self.assertEqual(v["C"], candidate)
        self.assertEqual(v["G"], external)
        self.assertEqual(self.ref(), v["M"])
        for ancestor in (external, candidate):
            self.git("merge-base", "--is-ancestor", ancestor, self.ref())
        self.assertEqual((self.repo / "external-change.txt").read_bytes(), b"Independent baseline change\n")
        self.assertEqual(len(self.reflog().splitlines()), len(log_before.splitlines()) + 1)
        checks = [event for event in self.events()[len(events):] if event["type"] == "completion_check"]
        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0]["details"]["verification_id"], v["verification_id"])
        self.assertEqual(checks[0]["details"]["result"]["returncode"], 0)
        self.assert_novel_pagination_inputs(self.repo)
        accepted_log = self.reflog()
        self.cli("integrate", "--task", self.task)
        self.assertEqual(self.reflog(), accepted_log)

    def test_submit_requires_clean_head_and_cannot_replace_frozen_candidate(self):
        self.create()
        attempt = self.claim()
        candidate = self.candidate(attempt, good=True)
        workspace = Path(attempt["workspace"])
        before = self.business_state()
        with (workspace / "pager.py").open("a", encoding="utf-8") as out:
            out.write("\n# dirty worktree must not be accepted\n")
        events = self.events()
        denied = self.submit(attempt, candidate, ok=False)
        self.assertEqual(self.business_state(), before)
        self.assert_rejection_recorded(denied["error"], events)
        self.git("checkout", "--", "pager.py", cwd=workspace)
        for wrong_commit in (candidate[:12], self.base):
            events = self.events()
            denied = self.submit(attempt, wrong_commit, ok=False)
            self.assertEqual(self.business_state(), before)
            self.assertEqual(self.ref(), self.base)
            self.assert_rejection_recorded(denied["error"], events)
        self.submit(attempt, candidate)
        frozen = self.business_state()
        self.submit(attempt, candidate)
        self.assertEqual(self.business_state(), frozen)
        # Changing the worktree after submission must not change the stored
        # candidate or the independent detached worktree used by verify.
        later_bad = self.candidate(attempt, good=False)
        events = self.events()
        denied = self.submit(attempt, later_bad, ok=False)
        self.assertEqual(self.business_state(), frozen)
        self.assert_rejection_recorded(denied["error"], events)
        self.cli("verify", "--task", self.task)
        self.assertEqual(self.status()["state"], "verified")
        self.assertEqual(self.status()["candidate_commit"], candidate)
        # W07 / decision 02: a manual claim has no managed launch provenance.
        # The complete managed frozen-C integration is a separate explicit case.
        events = self.events()
        log_before = self.reflog()
        reply = self.cli("integrate", "--task", self.task, "--score-file", self.score_file(attempt),
                         ok=False, error="score_provenance_required")
        self.assertEqual(self.ref(), self.base, "W07-MANUAL-SOURCE: refuse before Git changes")
        self.assertEqual(self.reflog(), log_before)
        self.assertEqual(self.status()["candidate_commit"], candidate)
        self.assert_rejection_recorded(reply["error"], events)

    def test_spec_revision_invalidates_candidate_and_old_identity(self):
        self.create()
        old = self.claim()
        candidate = self.candidate(old, good=True)
        self.submit(old, candidate)
        prior_events = self.events()
        self.cli("revise", "--task", self.task, "--spec-rev", "2")
        revised = self.status()
        self.assertEqual(revised["state"], "ready")
        self.assertEqual(revised["spec_rev"], 2)
        self.assertIsNone(revised["candidate_commit"])
        self.assertIsNone(revised["verification"])
        self.assertEqual(self.events()[:len(prior_events)], prior_events)
        events = self.events()
        self.submit(old, candidate, ok=False, error="stale_attempt")
        self.assert_rejection_recorded("stale_attempt", events)
        current = self.claim(owner="revised-owner")
        self.assertEqual(current["spec_rev"], 2)
        self.assertGreater(current["fence"], old["fence"])
        new_candidate = self.candidate(current, good=True)
        before = self.business_state()
        events = self.events()
        self.submit(current, new_candidate, ok=False, error="stale_spec", **{"spec-rev": 1})
        self.assertEqual(self.business_state(), before)
        self.assert_rejection_recorded("stale_spec", events)
        events = self.events()
        denied = self.cli("revise", "--task", self.task, "--spec-rev", "2", ok=False)
        self.assertEqual(self.business_state(), before)
        self.assert_rejection_recorded(denied["error"], events)
        self.assertEqual(self.ref(), self.base)


def run_suite():
    started = utc_now()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ManagedDeliveryCLI)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    trace = {"started": started, "finished": utc_now(), "tests_run": result.testsRun,
             "failures": len(result.failures), "errors": len(result.errors),
             "skipped": len(result.skipped), "artifacts": ARTIFACTS,
             "commands": COMMANDS}
    trace_path = Path(os.environ["COOP_E2E_TRACE"])
    with trace_path.open("x", encoding="utf-8") as out:
        json.dump(trace, out, ensure_ascii=False, indent=2)
        out.write("\n")
    return 0 if result.wasSuccessful() else 1


def main():
    if sys.argv[1:] == ["--run-suite"]:
        return run_suite()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    evidence_path = EVIDENCE / ("check-" + stamp + "-" + uuid.uuid4().hex[:8] + ".json")
    artifact_root = Path(tempfile.mkdtemp(prefix="a2a-check-"))
    trace_path = artifact_root / "subprocess-trace.json"
    env = dict(os.environ)
    env["COOP_E2E_ARTIFACT_ROOT"] = str(artifact_root)
    env["COOP_E2E_TRACE"] = str(trace_path)
    argv = [sys.executable, "-B", str(Path(__file__).resolve()), "--run-suite"]
    started = utc_now()
    missing_feature = not SCRIPT.is_file()
    completed = subprocess.run(argv, cwd=str(ROOT), env=env, text=True, capture_output=True)
    trace = json.loads(trace_path.read_text(encoding="utf-8")) if trace_path.is_file() else None
    code_revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT),
                                   text=True, capture_output=True)
    record = {
        "role": "a2a-check", "ticket": "T-006", "contract":
        ".project-map/specs/managed-delivery-2026-10-06.md (CLI contract v1)",
        "status": "PASS" if completed.returncode == 0 else "INCOMPLETE",
        "classification": "expected-red-missing-feature" if missing_feature else
        ("contract-suite-pass" if completed.returncode == 0 else "contract-suite-red"),
        "started": started, "finished": utc_now(),
        "command": ["python3", "-B", "acceptance/test_coop_e2e.py"],
        "actual_command": argv, "cwd": str(ROOT), "coop_script": str(SCRIPT),
        "exit_code": completed.returncode, "stdout": completed.stdout,
        "stderr": completed.stderr, "python": sys.version,
        "repository_head": code_revision.stdout.strip(),
        "artifact_root": str(artifact_root), "trace": trace,
        "independence": "No coop source read or import; contract literal expectations; "
                        "reference copied only as candidate; real Git and CLI subprocesses.",
        "limitations": ["No Herdr or model dispatch claim; controller runs that boundary.",
                        "Gate-mutant counterfactual is pending controller COOP_SCRIPT run.",
                        "Status associations are tested; verification/event internal schema "
                        "is not frozen and no private schema is assumed."],
    }
    with evidence_path.open("x", encoding="utf-8") as out:
        json.dump(record, out, ensure_ascii=False, indent=2)
        out.write("\n")
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    print("Acceptance evidence: " + str(evidence_path))
    print("Retained isolated artifacts: " + str(artifact_root))
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
