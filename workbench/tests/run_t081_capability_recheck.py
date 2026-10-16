#!/usr/bin/env python3
"""Prepare and (outside this sandbox) run the T-081 capability layout probe.

This script never starts Codex or a model.  It creates disposable Git fixtures,
records the current CLI help and execpolicy decisions, and runs the two direct
Git probes through ``codex sandbox`` when invoked by the controller outside the
managed sandbox.  Every command is passed as an argv list; no shell is used.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXTERNAL = Path(
    "/Volumes/WD-Elements/a2a-evidence/2026-10-14-batch14/T-081/sandbox-probe-01"
)
DEFAULT_TMP = Path("/tmp/t081-capability-recheck-01")
DEFAULT_EVIDENCE = REPO_ROOT / "evidence/2026-10-14-batch14/T-081/CAPABILITY-RECHECK-01"
PERMISSION_PROFILE = ":workspace"
COMMAND_ENV = None
CONFIG_OVERRIDES = [
    ["model_reasoning_effort=\"xhigh\""],
    ["service_tier=\"default\""],
    ["check_for_update_on_startup=false"],
    ["tui.notifications=false"],
    ["sandbox_workspace_write.network_access=false"],
    ["features.network_proxy=false"],
]


def command(argv: list[str], cwd: Path | None = None, timeout: int = 60) -> dict:
    """Run one argv and retain the complete bounded result."""
    try:
        result = subprocess.run(
            argv,
            cwd=str(cwd) if cwd else None,
            env=(COMMAND_ENV.copy() if COMMAND_ENV is not None else os.environ.copy()),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "argv": argv,
            "cwd": str(cwd) if cwd else None,
            "exit": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired as error:
        return {
            "argv": argv,
            "cwd": str(cwd) if cwd else None,
            "exit": None,
            "stdout": error.stdout or "",
            "stderr": error.stderr or "",
            "outcome": "timeout",
        }
    except OSError as error:
        return {
            "argv": argv,
            "cwd": str(cwd) if cwd else None,
            "exit": None,
            "stdout": "",
            "stderr": str(error),
            "outcome": "spawn_error",
        }


def git(directory: Path, *args: str, timeout: int = 60) -> dict:
    return command(["git", "-C", str(directory), *args], timeout=timeout)


def require_ok(row: dict, label: str) -> str:
    if row.get("exit") != 0:
        raise RuntimeError(f"{label} failed: {row}")
    return str(row.get("stdout", "")).strip()


def make_fixture(root: Path) -> dict:
    """Create G/T, a shared repo, a bare repo, and a detached worker worktree."""
    if root.exists():
        raise RuntimeError(f"fixture already exists; preserving it: {root}")
    root.mkdir(parents=True)
    repo = root / "repo"
    bare = root / "local.git"
    worker = root / "worker"
    require_ok(command(["git", "init", "--bare", str(bare)]), "git init bare")
    require_ok(command(["git", "init", "-b", "main", str(repo)]), "git init repo")
    require_ok(git(repo, "config", "user.name", "T-081 capability probe"), "git config name")
    require_ok(git(repo, "config", "user.email", "t081-capability@example.invalid"), "git config email")
    (repo / "README.txt").write_text("G\n", encoding="utf-8")
    require_ok(git(repo, "add", "README.txt"), "seed add")
    require_ok(git(repo, "commit", "-m", "G"), "seed G")
    G = require_ok(git(repo, "rev-parse", "HEAD"), "read G")
    (repo / "README.txt").write_text("T\n", encoding="utf-8")
    require_ok(git(repo, "add", "README.txt"), "target add")
    require_ok(git(repo, "commit", "-m", "T"), "seed T")
    T = require_ok(git(repo, "rev-parse", "HEAD"), "read T")
    require_ok(git(repo, "update-ref", "refs/heads/main", G, T), "restore main to G")
    require_ok(git(repo, "push", str(bare), f"{G}:refs/heads/main"), "seed bare main")
    require_ok(git(repo, "worktree", "add", "--detach", str(worker), G), "add worker worktree")
    return {
        "root": str(root),
        "repo": str(repo),
        "bare": str(bare),
        "worker": str(worker),
        "work_ref": "refs/heads/main",
        "G": G,
        "T": T,
    }


def run_sandbox_probe(fixture: dict, codex: str) -> dict:
    worker = Path(fixture["worker"])
    bare = fixture["bare"]
    ref = fixture["work_ref"]
    T = fixture["T"]
    G = fixture["G"]
    prefix = [codex, "sandbox", "--permission-profile", PERMISSION_PROFILE, "--cd", str(worker)]
    for override in CONFIG_OVERRIDES:
        prefix += ["-c", *override]
    update = prefix + ["--", "git", "update-ref", ref, T, G]
    push = prefix + ["--", "git", "push", bare, f"{T}:refs/heads/t081-probe"]
    return {
        "strategy": "codex sandbox equivalent to product --sandbox workspace-write",
        "worker_cwd": str(worker),
        "commands": [command(update, cwd=worker), command(push, cwd=worker)],
        "readback": {
            "main": git(Path(fixture["repo"]), "rev-parse", ref),
            "reflog": git(Path(fixture["repo"]), "reflog", "show", "--format=%H %gs", ref),
            "bare_refs": command(["git", "-C", fixture["bare"], "show-ref"], timeout=60),
        },
    }


def run_help_probe(codex: str) -> dict:
    return {
        "version": command([codex, "--version"]),
        "root_help": command([codex, "--help"]),
        "sandbox_help": command([codex, "sandbox", "--help"]),
        "sandbox_macos_help": command([codex, "sandbox", "macos", "--help"]),
        "execpolicy_help": command([codex, "execpolicy", "--help"]),
    }


def run_execpolicy_probe(codex: str, output: Path) -> dict:
    rules = output / "probe.rules"
    rules.write_text(
        'prefix_rule(pattern=["git", "add"], decision="allow", justification="T-081 probe")\n'
        'prefix_rule(pattern=["git", "commit"], decision="allow", justification="T-081 probe")\n',
        encoding="utf-8",
    )
    cases = {
        "commit": ["git", "commit", "-m", "probe"],
        "commit_with_C": ["git", "-C", "/other", "commit", "-m", "probe"],
        "config": ["git", "config", "--local", "core.hooksPath", "/tmp/hook"],
        "update_ref": ["git", "update-ref", "refs/heads/main", "T", "G"],
        "push": ["git", "push", "/tmp/local.git", "T:refs/heads/probe"],
    }
    results = {}
    for label, argv in cases.items():
        results[label] = command(
            [codex, "execpolicy", "check", "--pretty", "--rules", str(rules), "--", *argv]
        )
    return {"rules": str(rules), "cases": results}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", default=shutil.which("codex") or "codex")
    parser.add_argument("--external-root", type=Path, default=DEFAULT_EXTERNAL)
    parser.add_argument("--tmp-root", type=Path, default=DEFAULT_TMP)
    parser.add_argument("--output", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--codex-home", type=Path, help="Fresh isolated CODEX_HOME for sandbox probes (required with --run-sandbox).")
    parser.add_argument("--run-sandbox", action="store_true", help="Run probes; controller uses this outside managed sandbox.")
    args = parser.parse_args()
    global COMMAND_ENV
    if args.run_sandbox:
        if args.codex_home is None:
            raise SystemExit("--codex-home is required with --run-sandbox; pass a fresh isolated home")
        home = args.codex_home.resolve()
        if home.exists():
            raise SystemExit(f"refusing existing CODEX_HOME; preserve it and choose a fresh path: {home}")
        home.mkdir(parents=True)
        (home / "config.toml").write_text("[permissions]\n", encoding="utf-8")
        COMMAND_ENV = os.environ.copy()
        COMMAND_ENV["CODEX_HOME"] = str(home)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {
        "status": "INCOMPLETE",
        "task": "T-081",
        "model_turns_started": 0,
        "codex": str(Path(args.codex).resolve()) if Path(args.codex).exists() else args.codex,
        "source_argv": sys.argv,
        "product_cli_overrides": CONFIG_OVERRIDES,
        "permission_profile": PERMISSION_PROFILE,
        "codex_home": str(args.codex_home.resolve()) if args.codex_home else None,
        "help": run_help_probe(args.codex),
        "execpolicy": run_execpolicy_probe(args.codex, out),
        "fixtures": [],
    }
    if args.run_sandbox:
        for label, root in (("external", args.external_root), ("tmp", args.tmp_root)):
            fixture = make_fixture(root.resolve())
            row = {"label": label, "fixture": fixture}
            try:
                row["probe"] = run_sandbox_probe(fixture, args.codex)
            except Exception as error:
                row["probe_error"] = repr(error)
            report["fixtures"].append(row)
        def valid_probe(row):
            commands = row.get("probe", {}).get("commands", [])
            if len(commands) != 2:
                return False
            for result in commands:
                error_text = result.get("stderr", "").lower()
                if result.get("exit") is None:
                    return False
                if any(marker in error_text for marker in (
                    "required arguments were not provided",
                    "usage: codex sandbox",
                    "sandbox_apply",
                    "sandbox-exec:",
                    "invalid permission profile",
                    "permission profile",
                )):
                    return False
            return True
        report["status"] = "PASS" if report["fixtures"] and all(valid_probe(row) for row in report["fixtures"]) else "INCOMPLETE"
    else:
        report["status"] = "READY"
        report["run_instruction"] = "Run this script outside the managed sandbox with --run-sandbox."
    (out / "run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] in {"PASS", "READY"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
