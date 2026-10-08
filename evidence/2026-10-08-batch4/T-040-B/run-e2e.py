#!/usr/bin/env python3
"""Live acceptance derived from brief-T-040-B, with no provider calls."""
import argparse
import json
import os
from pathlib import Path
import socket
import stat
import subprocess
import tempfile
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError

parser = argparse.ArgumentParser()
parser.add_argument("--label", required=True)
args = parser.parse_args()
out = Path(__file__).resolve().parent / args.label
out.mkdir(exist_ok=False)
repo = Path("/Users/luckye/Documents/Code/synara")
default_data = Path.home() / "Library/Application Support/a2a-workbench"
root = Path(tempfile.mkdtemp(prefix="t040b-", dir="/Volumes/WD-Elements/dev-cache/synara/instances"))
data = root / "desktop-data"
env = {**os.environ, "A2A_WORKBENCH_DATA_DIR": str(data), "A2A_SYNARA_SLOT": root.name,
       "HOME": str(root / "isolated-user"), "CODEX_HOME": str(root / "empty-codex"),
       "CLAUDE_CONFIG_DIR": str(root / "empty-claude"), "XDG_CONFIG_HOME": str(root / "xdg/config"),
       "XDG_CACHE_HOME": str(root / "xdg/cache"), "XDG_DATA_HOME": str(root / "xdg/data")}
for name in ("HOME", "CODEX_HOME", "CLAUDE_CONFIG_DIR", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME"):
    Path(env[name]).mkdir(parents=True)
report = {"status": "INCOMPLETE", "root": str(root), "default_data": str(default_data),
          "default_before_exists": default_data.exists(), "commands": [], "checks": {}}


def save():
    (out / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(name, argv, expected=0, command_env=env, cwd=repo):
    with (out / (name + ".log")).open("w", encoding="utf-8") as stream:
        result = subprocess.run(argv, env=command_env, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT, text=True)
    text = (out / (name + ".log")).read_text(encoding="utf-8")
    report["commands"].append({"name": name, "argv": [str(a) for a in argv], "cwd": str(cwd), "exit": result.returncode})
    save()
    assert result.returncode == expected, (name, result.returncode, expected)
    return text


def listener(port):
    checks = {}
    for address, family in (("127.0.0.1", socket.AF_INET), ("::1", socket.AF_INET6)):
        with socket.socket(family, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            checks[address] = sock.connect_ex((address, port)) == 0
    return checks


try:
    assert not default_data.exists(), "default directory already exists; requires controller decision"
    native_env = {k: v for k, v in os.environ.items() if k != "A2A_WORKBENCH_DATA_DIR"}
    default = json.loads(run("default-status", [str(repo / "a2a/scripts/workbench"), "status"], command_env=native_env))
    assert default == {"data_directory": str(default_data), "running": False, "pid": None}
    report["checks"]["default_directory"] = default
    # Provider settings are fixture input, independent of the new launcher.
    settings = json.loads((out.parent.parent.parent / "2026-10-07-synara-batch2/T-042/intervention/settings-disabled.json").read_text(encoding="utf-8"))
    assert all(not p["enabled"] for p in settings["settings"]["providers"].values())
    state = data / "userdata"
    state.mkdir(parents=True)
    (state / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    run("start", [str(repo / "a2a/scripts/workbench"), "start"])
    endpoint_path = data / "a2a-gates/endpoint.json"
    endpoint = json.loads(endpoint_path.read_text(encoding="utf-8"))
    with urlopen(endpoint["origin"] + "/health", timeout=5) as response:
        health = json.load(response)
    assert health["startupReady"] is True
    report["checks"]["startup_ready"] = True
    assert stat.S_IMODE(endpoint_path.stat().st_mode) == 0o600
    pid = endpoint["desktopPid"]
    assert os.getpgid(pid) == pid and pid != os.getpgid(0)
    assert endpoint["home"] == str(data)
    report["checks"]["endpoint"] = {key: endpoint[key] for key in ("version", "home", "origin", "desktopPid", "backendPid")}
    report["checks"]["endpoint"].update(mode="0600", detached=True)
    repeat = run("repeat", [str(repo / "a2a/scripts/workbench"), "start"])
    assert "已在运行" in repeat
    assert json.loads(endpoint_path.read_text(encoding="utf-8")) == endpoint
    report["checks"]["duplicate_start"] = "same PID and endpoint; no second instance"
    fixture = root / "fixture"
    fixture.mkdir()
    run("git-init", ["git", "init", "-b", "main", str(fixture)])
    (fixture / "note.txt").write_text("T-040-B independent fixture\n", encoding="utf-8")
    run("git-add", ["git", "-C", str(fixture), "add", "note.txt"])
    run("git-commit", ["git", "-C", str(fixture), "-c", "user.name=T040B", "-c", "user.email=t040b@example.invalid", "commit", "-m", "fixture"])
    base = subprocess.check_output(["git", "-C", str(fixture), "rev-parse", "HEAD"], text=True).strip()
    oracle = root / "oracle.py"
    oracle.write_text("#!/usr/bin/env python3\nraise SystemExit(0)\n", encoding="utf-8")
    oracle.chmod(0o755)
    instructions = root / "instructions.txt"
    instructions.write_text("Do not dispatch a provider. Launcher acceptance only.\n", encoding="utf-8")
    task = "probe-" + root.name
    request = {"command": "create", "task": task, "project": "project-" + root.name, "repo": str(fixture), "base": base, "oracle": str(oracle), "instructions": str(instructions)}
    run("create", [str(repo / "a2a/scripts/gate"), json.dumps(request)])
    status_text = run("gate-status", [str(repo / "a2a/scripts/gate"), "status", task])
    status = json.loads(status_text.splitlines()[-1])
    assert status["ok"] and status["task"]["task_id"] == task and status["task"]["state"] == "ready"
    report["checks"]["gate_status"] = {"task": task, "state": "ready", "http": True}
    missing = run("gate-missing", [str(repo / "a2a/scripts/gate"), "status", "missing-" + root.name], expected=1)
    assert json.loads(missing.splitlines()[-1])["ok"] is False
    endpoint_path.chmod(0o644)
    try:
        denied = run("insecure-endpoint", [str(repo / "a2a/scripts/gate"), "status", task], expected=2)
        assert "0600" in denied
    finally:
        endpoint_path.chmod(0o600)
    url = endpoint["origin"] + "/api/a2a?token=invalid-t040b"
    request = Request(url, data=json.dumps({"command": "status", "task": task}).encode(), headers={"Content-Type": "application/json", "Authorization": "Bearer invalid-t040b"})
    try:
        urlopen(request, timeout=5)
        raise AssertionError("incorrect token accepted")
    except HTTPError as error:
        assert error.code in (400, 401, 403)
        report["checks"]["wrong_token"] = {"http_status": error.code, "rejected": True}
    port = int(endpoint["origin"].rsplit(":", 1)[1])
    report["checks"]["listening_before_stop"] = listener(port)
    run("stop", [str(repo / "a2a/scripts/workbench"), "stop"])
    assert not any(listener(port).values())
    assert not endpoint_path.exists()
    report["checks"]["stopped"] = {"listeners": listener(port), "endpoint_removed": True}
    # A second run must publish a fresh credential and keep the same fixture data.
    run("restart", [str(repo / "a2a/scripts/workbench"), "start"])
    second = json.loads(endpoint_path.read_text(encoding="utf-8"))
    assert second["token"] != endpoint["token"] and second["desktopPid"] != pid
    run("restart-status", [str(repo / "a2a/scripts/gate"), "status", task])
    run("restart-stop", [str(repo / "a2a/scripts/workbench"), "stop"])
    assert not any(listener(int(second["origin"].rsplit(":", 1)[1])).values())
    report["checks"]["restart"] = {"token_rotated": True, "task_retained": True, "stopped": True}
    report["default_after_exists"] = default_data.exists()
    assert not default_data.exists()
    assert not list(root.rglob("auth.json")), "authentication must not be copied or created"
    report["checks"]["no_auth_json"] = True
    report["status"] = "PASS"
except BaseException as error:
    report["error"] = f"{type(error).__name__}: {error}"
    raise
finally:
    save()
