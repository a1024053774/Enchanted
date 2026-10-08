#!/usr/bin/env python3
"""Drive the retained UI fixture through the real gate CLI, preserving every result."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
step = sys.argv[1]
record = root / ((sys.argv[3] if len(sys.argv) > 3 else step) + ".json")
assert not record.exists(), "Evidence label already exists"
fixture_file = Path(sys.argv[2]) if len(sys.argv) > 2 else root / "fixture.json"
fixture = json.loads(fixture_file.read_text(encoding="utf-8"))
env = os.environ.copy()
env["A2A_SYNARA_SLOT"] = "t038"
env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0", "PYTHONDONTWRITEBYTECODE": "1"})
for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_CONFIG_COUNT"):
    env.pop(key, None)
cwd = "/Users/luckye/Documents/Code/synara-t038"
commands = []
def run(argv):
    start = time.time()
    p = subprocess.run(argv, cwd=cwd, env=env, text=True, capture_output=True, timeout=120)
    commands.append({"argv": argv, "cwd": cwd, "seconds": time.time() - start,
                     "stdout": p.stdout, "stderr": p.stderr, "exit": p.returncode})
    return p
def prior(label):
    return json.loads((root / (label + ".json")).read_text(encoding="utf-8"))
result = None
expected = 0
if step.startswith("candidate-"):
    mode = step.removeprefix("candidate-")
    attempt = prior("claim-" + mode)["result"]["attempt"]
    workspace = Path(attempt["workspace"])
    assert workspace.resolve().is_relative_to(Path(fixture["state"]).resolve() / "worktrees")
    if mode == "good":
        shutil.copyfile("/Users/luckye/Documents/Code/a2a/acceptance/reference/pager.py", workspace / "pager.py")
    else:
        (workspace / "candidate-note.txt").write_text("Known-bad starter retained for UI failure evidence.\n", encoding="utf-8")
    for args in (["config", "user.name", "T-038 fixture"], ["config", "user.email", "t038@example.invalid"],
                 ["config", "commit.gpgsign", "false"], ["add", "--", "pager.py", *(["candidate-note.txt"] if mode == "bad" else [])],
                 ["-c", "core.hooksPath=/dev/null", "commit", "-m", "T-038 " + mode + " pagination candidate"]):
        p = run(["git", "-C", str(workspace), *args])
        assert p.returncode == 0, p.stderr
    p = run(["git", "-C", str(workspace), "rev-parse", "HEAD"])
    result = {"commit": p.stdout.strip(), "attempt": attempt}
else:
    command = step.split("-")[0]
    argv = ["./a2a/scripts/bun", "packages/a2a-gates/src/cli.ts", "--state", fixture["state"], command, "--task", fixture["task"]]
    if step == "create":
        argv += ["--repo", fixture["repo"], "--base", fixture["base"], "--oracle", fixture["oracle"], "--instructions", fixture["instructions"]]
    elif command == "claim":
        argv += ["--owner", "t038-ui-fixture"]
    elif command == "submit":
        mode = step.split("-")[1]
        candidate = prior("candidate-" + mode)["result"]
        attempt = candidate["attempt"]
        argv += ["--attempt", attempt["attempt_id"], "--session", attempt["session_id"], "--fence", str(attempt["fence"]),
                 "--spec-rev", str(attempt["spec_rev"]), "--commit", candidate["commit"]]
    elif command in ("verify", "integrate"):
        mode = step.split("-")[1]
        attempt = prior("claim-" + mode)["result"]["attempt"]
        argv += ["--attempt", attempt["attempt_id"]]
    elif command == "revoke":
        argv += ["--reason", "Known-bad fixture rejected; retry with correct pagination"]
    if step == "verify-bad": expected = 1
    p = run(argv)
    result = json.loads(p.stdout)
record.write_text(json.dumps({"step": step, "fixture_file": str(fixture_file), "expected_exit": expected, "commands": commands, "result": result},
                             ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(record)
assert all(c["exit"] == 0 for c in commands[:-1])
assert commands[-1]["exit"] == expected, result
if step == "verify-bad": assert result["error"] == "oracle_failed", result
