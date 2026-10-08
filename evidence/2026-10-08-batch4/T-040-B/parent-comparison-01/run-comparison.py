#!/usr/bin/env python3
"""Run the controller's bounded, serial parent/candidate comparison."""
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent
SETUP = json.loads((OUT / "setup.json").read_text(encoding="utf-8"))
EXTERNAL = Path(SETUP["external_root"])
SHARED = Path("/Users/luckye/Documents/Code/synara")
FILES = [
    ("desktop", "src/appSnapManager.test.ts"),
    ("desktop", "src/cuaDriverHost.test.ts"),
    ("desktop", "src/macAppIcon.native.test.ts"),
    ("server", "src/orchestration/Layers/ProviderCommandReactor.test.ts"),
]


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def append(name, record):
    with (OUT / name).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def revision(tree):
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tree, text=True).strip()


def a_timing():
    output = subprocess.check_output(["ps", "-axo", "pid=,command="], text=True)
    active = []
    for line in output.splitlines():
        pid, _, command = line.strip().partition(" ")
        if pid and int(pid) != os.getpid() and (
            "/T-040-A/timing-01/" in command or
            "T-040-A/timing-01/run-timing.py" in command or
            "acceptance/test_recovery_e2e.py" in command or
            ("packages/a2a-gates/src/cli.ts" in command and "--state" in command)
        ):
            active.append({"pid": int(pid), "command": command.strip()})
    return active


def command(label, tree, argv, env, timeout):
    if revision(SHARED) != SETUP["shared_checkout_head"]:
        raise RuntimeError("Shared fork HEAD changed; preserve state and ask controller.")
    blockers = a_timing()
    if blockers:
        append("conflicts.jsonl", {"at": now(), "label": label, "before_start": True, "A_processes": blockers})
        raise RuntimeError("A timing is active; no B command was started.")
    started = now()
    begin = time.monotonic()
    with (OUT / (label + ".log")).open("x", encoding="utf-8") as log:
        child = subprocess.Popen(argv, cwd=tree, env=env, start_new_session=True,
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        append("commands.jsonl", {"event": "start", "label": label, "at": started,
               "commit": revision(tree), "cwd": str(tree), "argv": argv, "pid": child.pid,
               "environment": {key: env[key] for key in ("HOME", "CODEX_HOME", "CLAUDE_CONFIG_DIR", "A2A_SYNARA_SLOT")}})
        checks = 0
        while child.poll() is None:
            time.sleep(1)
            blockers = a_timing()
            checks += 1
            if blockers or time.monotonic() - begin > timeout:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                append("conflicts.jsonl", {"at": now(), "label": label, "A_processes": blockers,
                       "own_group_stopped": child.pid, "timeout": not bool(blockers)})
                raise RuntimeError("B command stopped; evidence retained, controller decision required.")
    record = {"event": "end", "label": label, "started": started, "ended": now(),
              "commit": revision(tree), "exit": child.returncode,
              "elapsed_seconds": time.monotonic() - begin, "A_guard_checks": checks,
              "A_overlap_observed": False}
    append("commands.jsonl", record)
    return record


def environment():
    env = os.environ.copy()
    for key in ("BUN_OPTIONS", "NODE_OPTIONS", "A2A_WORKBENCH", "A2A_WORKBENCH_DATA_DIR",
                "A2A_TIMING_ENABLE", "A2A_TIMING_MARKS", "A2A_MUTANT_CORE", "A2A_MUTANT_CLI"):
        env.pop(key, None)
    env.update({"A2A_SYNARA_SLOT": "b4compare", "HOME": str(EXTERNAL / "h"),
                "CODEX_HOME": str(EXTERNAL / "codex"), "CLAUDE_CONFIG_DIR": str(EXTERNAL / "claude"),
                "XDG_CONFIG_HOME": str(EXTERNAL / "xdg")})
    for key in ("HOME", "CODEX_HOME", "CLAUDE_CONFIG_DIR", "XDG_CONFIG_HOME"):
        Path(env[key]).mkdir(exist_ok=True)
    return env


def main():
    env = environment()
    for kind in ("parent", "candidate"):
        tree = Path(SETUP["revisions"][kind]["path"])
        assert revision(tree) == SETUP["revisions"][kind]["commit"]
        result = command("install-" + kind, tree, [str(tree / "a2a/scripts/bun"), "install", "--frozen-lockfile"], env, 1800)
        if result["exit"] != 0:
            raise RuntimeError("Dependency installation failed; retain setup evidence.")
    for package, test in FILES:
        stem = Path(test).stem.replace(".test", "")
        for round_number in (1, 2, 3):
            for kind in ("parent", "candidate"):
                tree = Path(SETUP["revisions"][kind]["path"])
                label = f"{stem}-{round_number}-{kind}"
                output = OUT / (label + ".json")
                argv = [str(tree / "a2a/scripts/bun"), "run", "env", "TMPDIR=" + str(EXTERNAL / "t"),
                        "bun", "run", "--cwd", "apps/" + package, "test", test,
                        "--reporter=json", "--outputFile=" + str(output)]
                result = command(label, tree, argv, env, 600)
                if not output.is_file():
                    raise RuntimeError("Vitest did not produce its result artifact; setup failure is not a test result.")
                report = json.loads(output.read_text(encoding="utf-8"))
                result.update(test_file=test, package=package, kind=kind, round=round_number,
                              numTotalTests=report["numTotalTests"], numPassedTests=report["numPassedTests"],
                              numFailedTests=report["numFailedTests"], success=report["success"],
                              failures=[a["fullName"] for f in report["testResults"] for a in f["assertionResults"] if a["status"] == "failed"])
                append("results.jsonl", result)
                print(json.dumps({"label": label, "exit": result["exit"], "failed": result["numFailedTests"]}), flush=True)
    append("completion.jsonl", {"status": "COMPLETE", "ended": now(), "runs": 24,
           "shared_checkout_head": revision(SHARED), "test_or_product_source_edited": False})


if __name__ == "__main__":
    try:
        main()
    except BaseException as error:
        append("completion.jsonl", {"status": "INCOMPLETE", "ended": now(), "error": str(error)})
        raise
