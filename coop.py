#!/usr/bin/env python3
"""Single-host managed delivery for trusted collaborators, not an OS sandbox."""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shlex
import sqlite3
import subprocess
import sys
import uuid


REF = "refs/a2a/integration"
TIMEOUT = 60
ORACLE_TIMEOUT = 60
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z")
SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
PANE = re.compile(r"w[A-Za-z0-9]+:p[A-Za-z0-9]+\Z")
NAME = re.compile(r"[a-z][a-z0-9_-]{0,31}\Z")


def now():
    return datetime.now(timezone.utc).isoformat()


def token():
    return uuid.uuid4().hex


class Refusal(Exception):
    def __init__(self, code, **details):
        super().__init__(code)
        self.code = code
        self.details = details


def require(condition, code, **details):
    if not condition:
        raise Refusal(code, **details)


def absolute(value, kind=None):
    require(not any(ord(c) < 32 for c in value), "invalid_path", path=value)
    p = Path(value)
    require(p.is_absolute(), "invalid_path", path=value)
    if kind == "file":
        require(p.is_file(), "invalid_path", path=value, expected="file")
    if kind == "directory":
        require(p.is_dir(), "invalid_path", path=value, expected="directory")
    return p.resolve()


def identifier(value):
    require(ID.fullmatch(value) is not None, "invalid_id", value=value)
    return value


def full_sha(value):
    require(SHA.fullmatch(value) is not None, "invalid_commit", commit=value)
    return value


def text_input(value):
    require(bool(value.strip()) and not any(ord(c) < 32 for c in value),
            "invalid_text")
    return value


class Coop:
    def __init__(self, state, task_id):
        self.root = absolute(state)
        self.root.mkdir(parents=True, exist_ok=True)
        self.task_id = identifier(task_id)
        self.db = sqlite3.connect(str(self.root / "state.sqlite3"), timeout=30,
                                  isolation_level=None)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS attempts (id TEXT PRIMARY KEY, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS verifications (id TEXT PRIMARY KEY, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT NOT NULL,
                type TEXT NOT NULL, task TEXT NOT NULL, attempt TEXT, details TEXT NOT NULL
            );
        """)

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.commit()
        finally:
            if self.db.in_transaction:
                self.db.rollback()

    def load(self, table, key):
        row = self.db.execute("SELECT data FROM " + table + " WHERE id=?", (key,)).fetchone()
        require(row is not None, "unknown_task" if table == "tasks" else "unknown_attempt")
        return json.loads(row[0])

    def save(self, table, key, value):
        self.db.execute("INSERT INTO " + table + "(id,data) VALUES (?,?) "
                        "ON CONFLICT(id) DO UPDATE SET data=excluded.data",
                        (key, json.dumps(value, ensure_ascii=False)))

    def event(self, kind, details=None, attempt=None):
        self.db.execute("INSERT INTO events(time,type,task,attempt,details) VALUES (?,?,?,?,?)",
                        (now(), kind, self.task_id, attempt,
                         json.dumps(details or {}, ensure_ascii=False)))

    def task(self):
        return self.load("tasks", self.task_id)

    def current(self, task):
        require(task["current_attempt"] is not None, "no_current_attempt")
        return self.load("attempts", task["current_attempt"])

    def public_task(self, task):
        result = dict(task)
        if task["current_attempt"]:
            result["current_attempt"] = self.current(task)
        return result

    def run(self, argv, *, cwd=None, timeout=TIMEOUT, env=None, attempt=None):
        record = {"argv": argv, "cwd": str(cwd) if cwd else None, "started": now()}
        self.event("command_intent", record, attempt)
        try:
            p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            def decoded(value):
                return value.decode("utf-8", "replace") if isinstance(value, bytes) else value
            record.update(returncode=None, stdout=decoded(exc.stdout), stderr=decoded(exc.stderr),
                          ended=now(), outcome="timeout")
            self.event("command_result", record, attempt)
            raise Refusal("command_timeout", **record)
        except (FileNotFoundError, PermissionError) as exc:
            record.update(returncode=None, ended=now(), outcome="not_started", reason=str(exc))
            self.event("command_result", record, attempt)
            raise Refusal("command_unavailable", **record)
        record.update(returncode=p.returncode, stdout=p.stdout, stderr=p.stderr, ended=now())
        self.event("command_result", record, attempt)
        return record

    def git(self, repo, *args, allowed=(0,), attempt=None, env=None):
        r = self.run(["git", "-C", str(repo), *args], attempt=attempt, env=env)
        require(r["returncode"] in allowed, "git_failed", command=r)
        return r

    def head(self, repo):
        return self.git(repo, "rev-parse", "--verify", "HEAD")["stdout"].strip()

    def integration_head(self, repo):
        r = self.git(repo, "rev-parse", "--verify", "--quiet", REF, allowed=(0, 1))
        return r["stdout"].strip() if r["returncode"] == 0 else None

    def commit_exists(self, repo, commit):
        full_sha(commit)
        r = self.git(repo, "cat-file", "-t", commit, allowed=(0, 128))
        require(r["returncode"] == 0 and r["stdout"].strip() == "commit", "invalid_commit")

    def ancestor(self, repo, old, new):
        r = self.git(repo, "merge-base", "--is-ancestor", old, new, allowed=(0, 1))
        return r["returncode"] == 0

    def create(self, args):
        repo = absolute(args.repo, "directory")
        oracle = absolute(args.oracle, "file")
        instructions = absolute(args.instructions, "file")
        full_sha(args.base)
        top = self.git(repo, "rev-parse", "--show-toplevel")["stdout"].strip()
        require(Path(top).resolve() == repo, "invalid_repo")
        self.commit_exists(repo, args.base)
        oracle_bytes = oracle.read_bytes()
        instruction_bytes = instructions.read_bytes()
        instruction_bytes.decode("utf-8")
        with self.transaction():
            require(self.db.execute("SELECT 1 FROM tasks WHERE id=?", (self.task_id,)).fetchone()
                    is None, "task_exists")
            g = self.integration_head(repo)
            require(g is None or g == args.base, "integration_conflict", expected=args.base, actual=g)
            snapshot = self.root / "tasks" / (self.task_id + "-" + token())
            task = {"task_id": self.task_id, "repo": str(repo), "base_commit": args.base,
                    "oracle": str(snapshot / "oracle.py"),
                    "instructions": str(snapshot / "instructions.txt"),
                    "spec_rev": 1, "fence": 0, "state": "creating", "current_attempt": None,
                    "candidate_commit": None, "verification": None, "integration_intent": None}
            self.save("tasks", self.task_id, task)
            self.event("create_intent", {"task": task, "oracle_source": str(oracle),
                                         "instructions_source": str(instructions)})
        snapshot.mkdir(parents=True)
        with (snapshot / "oracle.py").open("xb") as f:
            f.write(oracle_bytes)
        with (snapshot / "instructions.txt").open("xb") as f:
            f.write(instruction_bytes)
        with self.transaction():
            if g is None:
                r = self.git(repo, "update-ref", REF, args.base, "0" * len(args.base), allowed=(0, 128))
                require(r["returncode"] == 0, "integration_conflict", command=r)
            require(self.integration_head(repo) == args.base, "integration_conflict")
            task["state"] = "ready"
            self.save("tasks", self.task_id, task)
            self.event("created", {"task": task})
        return {"task": self.public_task(task)}

    def reserve_claim(self, owner, dispatch=None):
        text_input(owner)
        task = self.task()
        require(task["state"] == "ready" and task["current_attempt"] is None, "already_claimed",
                state=task["state"])
        attempt_id = token()
        task["fence"] += 1
        attempt = {"task_id": self.task_id, "attempt_id": attempt_id, "session_id": token(),
                   "fence": task["fence"], "spec_rev": task["spec_rev"], "owner": owner,
                   "workspace": str(self.root / "worktrees" / attempt_id),
                   "base_commit": task["base_commit"], "state": "preparing", "dispatch": dispatch}
        task.update(state="preparing", current_attempt=attempt_id, candidate_commit=None,
                    verification=None, integration_intent=None)
        self.save("tasks", self.task_id, task)
        self.save("attempts", attempt_id, attempt)
        self.event("claim_intent", {"attempt": attempt}, attempt_id)
        return task, attempt

    def prepare_claim(self, task, attempt):
        workspace = Path(attempt["workspace"])
        workspace.parent.mkdir(parents=True, exist_ok=True)
        require(not workspace.exists(), "workspace_exists", workspace=str(workspace))
        r = self.git(task["repo"], "worktree", "add", "--detach", str(workspace),
                     task["base_commit"], allowed=(0, 128), attempt=attempt["attempt_id"])
        with self.transaction():
            current = self.task()
            if r["returncode"] != 0:
                attempt["state"] = "worktree_failed"
                self.save("attempts", attempt["attempt_id"], attempt)
                if current["current_attempt"] == attempt["attempt_id"]:
                    current["state"] = "paused"
                    self.save("tasks", self.task_id, current)
                self.event("worktree_failed", r, attempt["attempt_id"])
            else:
                require(current["current_attempt"] == attempt["attempt_id"], "stale_attempt")
                attempt["state"] = "claimed"
                current["state"] = "claimed"
                self.save("attempts", attempt["attempt_id"], attempt)
                self.save("tasks", self.task_id, current)
                self.event("claimed", {"attempt": attempt}, attempt["attempt_id"])
        require(r["returncode"] == 0, "worktree_failed", command=r)
        return attempt

    def claim(self, args):
        with self.transaction():
            task, attempt = self.reserve_claim(args.owner)
        return {"attempt": self.prepare_claim(task, attempt)}

    def invalidate(self, task, reason):
        if task["current_attempt"]:
            attempt = self.current(task)
            attempt.update(state="revoked", revocation_reason=reason)
            self.save("attempts", attempt["attempt_id"], attempt)
            self.event("revoked", {"reason": reason}, attempt["attempt_id"])
        task.update(state="ready", current_attempt=None, candidate_commit=None,
                    verification=None, integration_intent=None)
        self.save("tasks", self.task_id, task)

    def revoke(self, args):
        text_input(args.reason)
        with self.transaction():
            task = self.task()
            require(task["state"] != "accepted", "already_accepted")
            require(task["integration_intent"] is None, "needs_reconciliation")
            self.invalidate(task, args.reason)
        return {"task": self.public_task(task)}

    def revise(self, args):
        with self.transaction():
            task = self.task()
            require(task["state"] != "accepted", "already_accepted")
            require(task["integration_intent"] is None, "needs_reconciliation")
            require(args.spec_rev > task["spec_rev"], "stale_spec")
            self.invalidate(task, "spec revised")
            task["spec_rev"] = args.spec_rev
            self.save("tasks", self.task_id, task)
            self.event("revised", {"spec_rev": args.spec_rev})
        return {"task": self.public_task(task)}

    def submit(self, args):
        identifier(args.attempt)
        identifier(args.session)
        full_sha(args.commit)
        with self.transaction():
            task = self.task()
            require(task["current_attempt"] == args.attempt, "stale_attempt")
            attempt = self.current(task)
            require(attempt["session_id"] == args.session, "stale_session")
            require(attempt["fence"] == args.fence, "stale_fence")
            require(task["spec_rev"] == args.spec_rev == attempt["spec_rev"], "stale_spec")
            require(task["state"] in ("claimed", "submitted"), "invalid_state", state=task["state"])
            if task["candidate_commit"] is not None:
                require(task["candidate_commit"] == args.commit, "candidate_conflict")
            self.commit_exists(task["repo"], args.commit)
            require(self.ancestor(task["repo"], task["base_commit"], args.commit), "not_descendant")
            require(self.head(attempt["workspace"]) == args.commit, "workspace_head_mismatch")
            dirty = self.git(attempt["workspace"], "status", "--porcelain=v1", "--untracked-files=all")
            require(not dirty["stdout"], "dirty_worktree", status=dirty["stdout"])
            task.update(state="submitted", candidate_commit=args.commit)
            attempt["state"] = "submitted"
            self.save("tasks", self.task_id, task)
            self.save("attempts", attempt["attempt_id"], attempt)
            self.event("submitted", {"commit": args.commit, "spec_rev": args.spec_rev}, args.attempt)
        return {"task": self.public_task(task)}

    def verify(self, args):
        with self.transaction():
            task = self.task()
            require(task["state"] == "submitted", "not_submitted", state=task["state"])
            attempt = self.current(task)
            g = self.integration_head(task["repo"])
            require(g is not None, "integration_conflict")
            self.commit_exists(task["repo"], g)
            verification = {"verification_id": token(), "task_id": self.task_id,
                            "attempt_id": attempt["attempt_id"], "session_id": attempt["session_id"],
                            "fence": attempt["fence"], "spec_rev": task["spec_rev"],
                            "G": g, "C": task["candidate_commit"], "M": None,
                            "oracle": task["oracle"], "state": "running", "started": now()}
            workspace = self.root / "verification" / verification["verification_id"]
            verification["workspace"] = str(workspace)
            task.update(state="verifying", verification=verification)
            self.save("tasks", self.task_id, task)
            self.save("verifications", verification["verification_id"], verification)
            self.event("verification_intent", verification, attempt["attempt_id"])
        workspace.parent.mkdir(parents=True, exist_ok=True)
        c = verification["C"]
        if self.ancestor(task["repo"], g, c):
            m = c
            self.git(task["repo"], "worktree", "add", "--detach", str(workspace), m)
        else:
            self.git(task["repo"], "worktree", "add", "--detach", str(workspace), g)
            env = dict(os.environ, GIT_AUTHOR_NAME="A2A", GIT_AUTHOR_EMAIL="a2a@localhost",
                       GIT_COMMITTER_NAME="A2A", GIT_COMMITTER_EMAIL="a2a@localhost")
            merged = self.git(workspace, "-c", "core.hooksPath=/dev/null", "merge", "--no-ff",
                              "--no-commit", "--no-edit", c, allowed=(0, 1), env=env)
            if merged["returncode"] != 0:
                verification.update(state="merge_failed", merge=merged, ended=now())
                self.finish_verification(verification, passed=False)
                raise Refusal("merge_conflict", verification=verification)
            tree = self.git(workspace, "write-tree")["stdout"].strip()
            m = self.git(workspace, "commit-tree", tree, "-p", g, "-p", c,
                         "-m", "A2A managed integration " + self.task_id, env=env)["stdout"].strip()
            self.git(workspace, "reset", "--hard", m)
        verification["M"] = m
        with self.transaction():
            self.save("verifications", verification["verification_id"], verification)
            current = self.task()
            if current["current_attempt"] == verification["attempt_id"] and current["state"] == "verifying":
                current["verification"] = verification
                self.save("tasks", self.task_id, current)
            self.event("merge_candidate", {"G": g, "C": c, "M": m,
                                           "workspace": str(workspace)}, attempt["attempt_id"])
        argv = ["python3", "-I", "-B", task["oracle"], str(workspace)]
        try:
            result = self.run(argv, cwd=workspace, timeout=ORACLE_TIMEOUT,
                              attempt=attempt["attempt_id"])
        except Refusal as exc:
            verification.update(state="unknown", result=exc.details, ended=now())
            self.finish_verification(verification, passed=False, unknown=True)
            raise Refusal("verification_unknown", verification=verification)
        passed = result["returncode"] == 0
        verification.update(state="passed" if passed else "failed", result=result, ended=now())
        self.finish_verification(verification, passed)
        require(passed, "oracle_failed", verification=verification)
        return {"task": self.public_task(self.task()), "verification": verification}

    def finish_verification(self, verification, passed, unknown=False):
        rejection = None
        with self.transaction():
            self.save("verifications", verification["verification_id"], verification)
            self.event("verification_result", verification, verification["attempt_id"])
            task = self.task()
            if task["current_attempt"] != verification["attempt_id"]:
                rejection = "stale_attempt"
            elif task["spec_rev"] != verification["spec_rev"]:
                rejection = "stale_spec"
            elif task["state"] != "verifying" or task["verification"]["verification_id"] != verification["verification_id"]:
                rejection = "verification_superseded"
            else:
                task.update(state="verified" if passed else "paused" if unknown else "submitted",
                            verification=verification)
                self.save("tasks", self.task_id, task)
        require(rejection is None, rejection)

    def integrate(self, args):
        with self.transaction():
            task = self.task()
            if task["state"] == "accepted":
                return {"task": self.public_task(task), "replayed": True}
            intent = task["integration_intent"]
            require(task["state"] == "verified" or intent is not None, "not_verified")
            verification = task["verification"]
            attempt = self.current(task)
            require(verification is not None and verification["state"] == "passed", "not_verified")
            require(verification["attempt_id"] == attempt["attempt_id"] and
                    verification["session_id"] == attempt["session_id"] and
                    verification["fence"] == attempt["fence"] and
                    verification["spec_rev"] == task["spec_rev"] and
                    verification["C"] == task["candidate_commit"], "stale_verification")
            actual = self.integration_head(task["repo"])
            if intent is not None:
                require(intent["state"] == "pending" and actual == intent["M"],
                        "needs_reconciliation", integration_intent=intent, actual=actual)
                task["state"] = "accepted"
                intent["state"] = "completed"
                task["integration_intent"] = intent
                attempt["state"] = "accepted"
                self.save("attempts", attempt["attempt_id"], attempt)
                self.save("tasks", self.task_id, task)
                self.event("integrated_reconciled", intent, attempt["attempt_id"])
                return {"task": self.public_task(task), "reconciled": True}
            if actual != verification["G"]:
                task.update(state="submitted", verification=None)
                self.save("tasks", self.task_id, task)
                self.event("integration_conflict", {"expected": verification["G"], "actual": actual},
                           attempt["attempt_id"])
                conflict = True
            else:
                conflict = False
                intent = {"intent_id": token(), "G": verification["G"], "M": verification["M"],
                          "verification_id": verification["verification_id"],
                          "attempt_id": attempt["attempt_id"], "state": "pending", "created": now()}
                task.update(state="integrating", integration_intent=intent)
                self.save("tasks", self.task_id, task)
                self.event("integration_intent", intent, attempt["attempt_id"])
        require(not conflict, "integration_conflict", expected=verification["G"], actual=actual)
        with self.transaction():
            task = self.task()
            require(task["integration_intent"] == intent, "needs_reconciliation")
            r = self.git(task["repo"], "update-ref", REF, intent["M"], intent["G"], allowed=(0, 128))
            if r["returncode"] != 0:
                intent.update(state="conflict", result=r)
                task.update(state="submitted", verification=None, integration_intent=None)
                self.save("tasks", self.task_id, task)
                self.event("integration_conflict", intent, attempt["attempt_id"])
            else:
                intent.update(state="completed", result=r)
                task.update(state="accepted", integration_intent=intent)
                attempt["state"] = "accepted"
                self.save("attempts", attempt["attempt_id"], attempt)
                self.save("tasks", self.task_id, task)
                self.event("integrated", intent, attempt["attempt_id"])
        require(r["returncode"] == 0, "integration_conflict", command=r)
        return {"task": self.public_task(task)}

    def status(self, args):
        return {"task": self.public_task(self.task())}

    def events(self, args):
        rows = self.db.execute("SELECT seq,time,type,task,attempt,details FROM events "
                               "WHERE task=? ORDER BY seq", (self.task_id,)).fetchall()
        return {"events": [{"seq": r[0], "time": r[1], "type": r[2], "task": r[3],
                            "attempt": r[4], "details": json.loads(r[5])} for r in rows]}

    def herdr(self, *args, mutation=False, attempt=None):
        require(os.environ.get("HERDR_ENV") == "1", "herdr_context_required")
        # The session/socket context remains; every pane target is an explicit live handle.
        env = {k: v for k, v in os.environ.items()
               if k not in ("HERDR_PANE_ID", "HERDR_TAB_ID", "HERDR_WORKSPACE_ID")}
        r = self.run(["herdr", *args], env=env, attempt=attempt)
        if r["returncode"] != 0:
            raise Refusal("herdr_side_effect_unknown" if mutation else "herdr_failed", response=r)
        try:
            response = json.loads(r["stdout"])
        except json.JSONDecodeError as exc:
            raise Refusal("herdr_response_unknown", response=r, reason=str(exc))
        require(isinstance(response, dict) and isinstance(response.get("result"), dict),
                "herdr_response_unknown", response=r)
        return response["result"], r

    def inventory(self):
        result, raw = self.herdr("pane", "list")
        require(isinstance(result.get("panes"), list), "herdr_response_unknown", response=raw)
        return result["panes"]

    def set_dispatch(self, attempt_id, dispatch, kind):
        with self.transaction():
            attempt = self.load("attempts", attempt_id)
            attempt["dispatch"] = dispatch
            self.save("attempts", attempt_id, attempt)
            self.event(kind, dispatch, attempt_id)

    def snapshot_bound(self, dispatch, attempt_id):
        panes = self.inventory()
        pane = next((p for p in panes if p.get("pane_id") == dispatch.get("pane_id")), None)
        if pane is None:
            return {"absent": True, "inventory": panes}
        require(pane.get("terminal_id") == dispatch.get("terminal_id"), "identity_conflict", pane=pane)
        result, raw = self.herdr("pane", "process-info", "--pane", pane["pane_id"], attempt=attempt_id)
        require(isinstance(result.get("process_info"), dict), "herdr_response_unknown", response=raw)
        snapshot = {"pane": pane, "process_info": result["process_info"], "process_response": raw}
        if pane.get("agent"):
            result, raw = self.herdr("agent", "get", pane["pane_id"], attempt=attempt_id)
            require(isinstance(result.get("agent"), dict), "herdr_response_unknown", response=raw)
            snapshot.update(agent=result["agent"], agent_response=raw)
            env = {k: v for k, v in os.environ.items()
                   if k not in ("HERDR_PANE_ID", "HERDR_TAB_ID", "HERDR_WORKSPACE_ID")}
            raw = self.run(["herdr", "agent", "read", pane["pane_id"], "--source", "detection",
                            "--lines", "80"], env=env, attempt=attempt_id)
            require(raw["returncode"] == 0, "herdr_failed", response=raw)
            snapshot["read_response"] = raw
        return snapshot

    def bind_agent(self, dispatch, snapshot):
        agent = snapshot.get("agent")
        require(agent is not None and agent.get("agent") == "codex" and
                agent.get("name") == dispatch["name"] and
                agent.get("terminal_id") == dispatch["terminal_id"],
                "identity_conflict", snapshot=snapshot)
        info = snapshot["process_info"]
        require(info.get("shell_pid") == dispatch["shell_pid"], "identity_conflict", snapshot=snapshot)
        pids = sorted(p["pid"] for p in info.get("foreground_processes", []) if "pid" in p)
        require(bool(pids), "identity_unknown", snapshot=snapshot)
        dispatch.update(agent_pids=pids, native_session=agent.get("agent_session"),
                        agent_identity={"agent": agent["agent"], "name": agent["name"]})

    def dispatch(self, args):
        require(PANE.fullmatch(args.parent_pane) is not None, "invalid_pane")
        require(NAME.fullmatch(args.name) is not None, "invalid_name")
        require(os.environ.get("HERDR_ENV") == "1", "herdr_context_required")
        panes = self.inventory()
        parent = next((p for p in panes if p.get("pane_id") == args.parent_pane), None)
        require(parent is not None, "parent_not_live")
        agents, raw = self.herdr("agent", "list")
        require(isinstance(agents.get("agents"), list), "herdr_response_unknown", response=raw)
        require(not any(a.get("name") == args.name for a in agents["agents"]), "name_in_use")
        version = self.run(["codex", "--version"])
        require(version["returncode"] == 0 and version["stdout"].strip() == "codex-cli 0.160.1",
                "cli_version_mismatch", response=version, expected="codex-cli 0.160.1")
        runtime = self.run(["herdr", "status"])
        require(runtime["returncode"] == 0, "herdr_failed", response=runtime)
        record = {"state": "reserved", "name": args.name, "parent_pane": args.parent_pane,
                  "parent_terminal": parent["terminal_id"], "cli_version": version,
                  "herdr_version": runtime, "prompt_sent": False, "created": now()}
        with self.transaction():
            for row in self.db.execute("SELECT data FROM attempts").fetchall():
                previous = json.loads(row[0])
                old = previous.get("dispatch")
                require(previous["task_id"] != self.task_id or old is None or old["state"] == "reclaimed",
                        "dispatch_exists", attempt=previous["attempt_id"])
            task, attempt = self.reserve_claim(args.name, record)
        attempt = self.prepare_claim(task, attempt)
        aid = attempt["attempt_id"]
        record["state"] = "split_pending"
        self.set_dispatch(aid, record, "dispatch_split_intent")
        try:
            result, raw = self.herdr("pane", "split", args.parent_pane, "--direction", "down",
                                     "--cwd", attempt["workspace"], "--no-focus", mutation=True, attempt=aid)
            pane = result.get("pane")
            require(isinstance(pane, dict) and PANE.fullmatch(pane.get("pane_id", "")) is not None and
                    pane.get("terminal_id") and pane["pane_id"] != args.parent_pane,
                    "herdr_response_unknown", response=raw)
            record.update(state="pane_created", pane_id=pane["pane_id"],
                          terminal_id=pane["terminal_id"], split_response=raw)
            self.set_dispatch(aid, record, "dispatch_pane_created")
            result, raw = self.herdr("pane", "process-info", "--pane", pane["pane_id"], attempt=aid)
            info = result.get("process_info")
            require(isinstance(info, dict) and info.get("shell_pid"),
                    "identity_unknown", response=raw)
            record.update(shell_pid=info["shell_pid"], shell_response=raw)
            startup = ["agent", "start", args.name, "--kind", "codex", "--pane", pane["pane_id"],
                       "--timeout", "30000", "--", "-m", "gpt-6.1-sol", "-c",
                       'model_reasoning_effort="xhigh"', "-c", 'service_tier="fast"',
                       "-c", "check_for_update_on_startup=false", "--no-alt-screen",
                       "-C", attempt["workspace"], "--add-dir", str(self.root)]
            record.update(state="start_pending", startup_argv=["herdr", *startup])
            self.set_dispatch(aid, record, "dispatch_start_intent")
            try:
                result, raw = self.herdr(*startup, mutation=True, attempt=aid)
            except Refusal as exc:
                record.update(state="startup_unknown", startup_error=exc.code,
                              startup_response=exc.details)
                self.set_dispatch(aid, record, "dispatch_start_failed")
                # Read-only inspection can retain an identity for later controller reclamation.
                snapshot = self.snapshot_bound(record, aid)
                record["startup_snapshot"] = snapshot
                if snapshot.get("agent"):
                    self.bind_agent(record, snapshot)
                self.set_dispatch(aid, record, "dispatch_start_observed")
                raise
            record.update(state="started", startup_response=raw)
            self.set_dispatch(aid, record, "dispatch_started")
            snapshot = self.snapshot_bound(record, aid)
            record["startup_snapshot"] = snapshot
            self.bind_agent(record, snapshot)
            self.set_dispatch(aid, record, "dispatch_identity_bound")
            agent = snapshot["agent"]
            require(agent.get("agent_status") in ("idle", "done") and
                    agent.get("interactive_ready") is True, "startup_not_ready", snapshot=snapshot)
            submit_argv = ["python3", str(Path(__file__).resolve()), "--state", str(self.root), "submit",
                           "--task", self.task_id, "--attempt", aid, "--session", attempt["session_id"],
                           "--fence", str(attempt["fence"]), "--spec-rev", str(attempt["spec_rev"]),
                           "--commit", "FULL_COMMIT_SHA"]
            prompt = ("你是本地受管理任务的 worker。只执行当前 task/attempt；你不是唯一 agent，"
                      "保留其他人的改动。不要改变验收 oracle、状态数据库、规格或其他任务。\n"
                      + "task=" + self.task_id + " attempt=" + aid + " session=" + attempt["session_id"]
                      + " fence=" + str(attempt["fence"]) + " spec_rev=" + str(attempt["spec_rev"])
                      + "\nworkspace=" + attempt["workspace"] + " base_commit=" + attempt["base_commit"]
                      + "\n任务说明（已冻结）：\n" + Path(task["instructions"]).read_text(encoding="utf-8")
                      + "\n完成本地实现后，在该 worktree 创建 commit 并保持 worktree 干净。"
                      "通过 git rev-parse HEAD 获取完整 SHA，替换下面 FULL_COMMIT_SHA，精确提交一次：\n"
                      + shlex.join(submit_argv)
                      + "\n成功交付只进入 submitted。不要 verify、integrate 或自行宣布 accepted。"
                      "遇到权限/启动问题停止并报告；不要自动答复、重发或扩大范围。")
            record.update(state="prompt_pending", submit_argv=submit_argv, prompt=prompt)
            self.set_dispatch(aid, record, "dispatch_prompt_intent")
            result, raw = self.herdr("agent", "prompt", pane["pane_id"], prompt,
                                     mutation=True, attempt=aid)
            record.update(state="dispatched", prompt_sent=True, prompt_response=raw)
            self.set_dispatch(aid, record, "dispatched")
        except Refusal as exc:
            record.update(state="paused", failure={"error": exc.code, "details": exc.details})
            self.set_dispatch(aid, record, "dispatch_paused")
            # A partial external effect stays bound to its attempt; a second dispatch is refused.
            with self.transaction():
                current = self.task()
                if current["current_attempt"] == aid and current["state"] == "claimed":
                    current["state"] = "paused"
                    self.save("tasks", self.task_id, current)
            raise
        return {"attempt": self.load("attempts", aid), "dispatch": record}

    def bound_attempt(self):
        # Revocation retains the pane binding even after current_attempt is cleared.
        records = [json.loads(row[0]) for row in self.db.execute("SELECT data FROM attempts").fetchall()]
        bound = [a for a in records if a["task_id"] == self.task_id and a.get("dispatch") and
                 a["dispatch"]["state"] != "reclaimed"]
        require(len(bound) == 1, "no_bound_pane" if not bound else "identity_conflict")
        return bound[0]

    def observe(self, args):
        self.task()
        attempt = self.bound_attempt()
        dispatch = attempt["dispatch"]
        require(dispatch.get("pane_id") is not None, "needs_reconciliation", dispatch=dispatch)
        snapshot = self.snapshot_bound(dispatch, attempt["attempt_id"])
        self.event("observed", snapshot, attempt["attempt_id"])
        return {"observation": snapshot, "attempt": attempt}

    def reclaim(self, args):
        attempt = self.bound_attempt()
        aid = attempt["attempt_id"]
        dispatch = attempt["dispatch"]
        require(dispatch.get("pane_id") and dispatch["pane_id"] != dispatch["parent_pane"],
                "needs_reconciliation", dispatch=dispatch)
        snapshot = self.snapshot_bound(dispatch, aid)
        self.event("reclaim_observation", snapshot, aid)
        if not snapshot.get("absent"):
            info = snapshot["process_info"]
            require(info.get("shell_pid") == dispatch.get("shell_pid"), "identity_conflict")
            agent = snapshot.get("agent")
            if agent:
                require(agent.get("agent") == "codex" and agent.get("name") == dispatch["name"],
                        "identity_conflict", snapshot=snapshot)
                pids = sorted(p["pid"] for p in info.get("foreground_processes", []) if "pid" in p)
                require(dispatch.get("agent_pids") == pids, "identity_conflict", snapshot=snapshot)
                require(not dispatch.get("native_session") or
                        agent.get("agent_session") == dispatch["native_session"],
                        "identity_conflict", snapshot=snapshot)
            else:
                require(info.get("foreground_process_group_id") == info.get("shell_pid") and
                        all(p.get("pid") == info["shell_pid"] for p in info.get("foreground_processes", [])),
                        "identity_unknown", snapshot=snapshot)
        with self.transaction():
            task = self.task()
            if task["state"] != "accepted" and task["current_attempt"] is not None:
                require(task["integration_intent"] is None, "needs_reconciliation")
                self.invalidate(task, "controller reclaim")
            dispatch["state"] = "close_pending"
            attempt = self.load("attempts", aid)
            attempt["dispatch"] = dispatch
            self.save("attempts", aid, attempt)
            self.event("reclaim_intent", dispatch, aid)
        if not snapshot.get("absent"):
            result, raw = self.herdr("pane", "close", dispatch["pane_id"], mutation=True, attempt=aid)
            dispatch["close_response"] = raw
            panes = self.inventory()
            require(not any(p.get("pane_id") == dispatch["pane_id"] for p in panes),
                    "needs_reconciliation", panes=panes)
            dispatch["closed_inventory"] = panes
        else:
            dispatch["absent_inventory"] = snapshot["inventory"]
        dispatch["state"] = "reclaimed"
        self.set_dispatch(aid, dispatch, "reclaimed")
        return {"task": self.public_task(self.task()), "attempt": self.load("attempts", aid)}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--state", required=True)
    commands = p.add_subparsers(dest="command", required=True)
    for name in ("create", "claim", "revoke", "revise", "submit", "verify", "integrate", "status",
                 "events", "dispatch", "observe", "reclaim"):
        s = commands.add_parser(name)
        s.add_argument("--task", required=True)
        if name == "create":
            for field in ("repo", "base", "oracle", "instructions"):
                s.add_argument("--" + field, required=True)
        elif name == "claim":
            s.add_argument("--owner", required=True)
        elif name == "revoke":
            s.add_argument("--reason", required=True)
        elif name == "revise":
            s.add_argument("--spec-rev", type=int, required=True)
        elif name == "submit":
            for field in ("attempt", "session", "commit"):
                s.add_argument("--" + field, required=True)
            for field in ("fence", "spec-rev"):
                s.add_argument("--" + field, type=int, required=True)
        elif name == "dispatch":
            s.add_argument("--parent-pane", required=True)
            s.add_argument("--name", required=True)
    return p


def main():
    args = parser().parse_args()
    coop = None
    try:
        coop = Coop(args.state, args.task)
        result = getattr(coop, args.command)(args)
    except Refusal as exc:
        if coop is not None:
            coop.event("rejected", {"command": args.command, "error": exc.code,
                                    "details": exc.details, "input": vars(args)},
                       getattr(args, "attempt", None))
        print(json.dumps({"ok": False, "error": exc.code, "details": exc.details}, ensure_ascii=False))
        return 1
    except (FileNotFoundError, PermissionError, FileExistsError, IsADirectoryError,
            NotADirectoryError, UnicodeDecodeError) as exc:
        detail = {"command": args.command, "exception": type(exc).__name__, "reason": str(exc)}
        if coop is not None:
            coop.event("local_io_failed", detail)
        print(json.dumps({"ok": False, "error": "local_io_failed", "details": detail}, ensure_ascii=False))
        return 1
    finally:
        if coop is not None:
            coop.db.close()
    print(json.dumps({"ok": True, **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
