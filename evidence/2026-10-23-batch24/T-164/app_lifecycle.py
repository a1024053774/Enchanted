"""T-164 isolated application lifecycle (from T-155, plus one isolated Codex home); no business-flow automation."""
import argparse
import json
import re
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
import uuid


SOURCE = Path(__file__).resolve().parents[3]
BASELINE = "aacc1bb81ad81d2e0c4769029ce64f3559d6f5c0"  # T-164-4: main after T-170 (T-164-3 used e3b14d27b, T-164-2 5380ebb28, T-164-1 7d7cb8342)


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def identity(pid):
    result = subprocess.run(
        ["/bin/ps", "-ww", "-p", str(pid), "-o", "pid=,lstart=,command="],
        capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}, check=False)
    if result.returncode == 1 and not result.stdout.strip() and not result.stderr.strip():
        return None
    if result.returncode or result.stderr.strip() or not result.stdout.strip():
        raise RuntimeError("Cannot verify process ownership; preserve the instance")
    return result.stdout.strip()


def prepare():
    root = Path(tempfile.mkdtemp(prefix="t164-dogfood-", dir="/private/tmp"))
    repo = root / "demo-repo"
    repo.mkdir()
    for name in ["state", "user-data", "logs"]:
        (root / name).mkdir(mode=0o700)
    (repo / "README.md").write_text(
        "# 食材清单\n\n这是 Enchanted 真实使用测试的一次性仓库，无 remote。\n"
        "pantry.json 记录食材、类别与库存数量。单位均为件，数量为零表示需要补货。\n",
        encoding="utf-8")
    write_json(repo / "pantry.json", [
        {"name": "苹果", "category": "水果", "quantity": 3},
        {"name": "香蕉", "category": "水果", "quantity": 0},
        {"name": "大米", "category": "主食", "quantity": 2},
        {"name": "面条", "category": "主食", "quantity": 0},
        {"name": "牛奶", "category": "乳品", "quantity": 1}])
    # Do not inherit the worker's gate identity or Git trailer hooks into the fixture.
    git_env = {k: v for k, v in os.environ.items()
               if not k.startswith(("A2A_", "GIT_"))}
    git_env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    commands = [
        ["init", "-b", "main"], ["config", "user.name", "T164 Demo"],
        ["config", "user.email", "t164@example.invalid"],
        ["add", "README.md", "pantry.json"], ["commit", "-m", "初始化一次性食材清单"]]
    for command in commands:
        subprocess.run(["git", "-C", str(repo), "-c", "core.hooksPath=/dev/null",
                        "-c", "commit.gpgsign=false", *command], env=git_env, check=True)
    config = {"schema": 1, "source": str(SOURCE), "product_baseline": BASELINE,
              "root": str(root), "repo": str(repo), "state": str(root / "state"),
              "user_data": str(root / "user-data"), "socket": str(root / "state/control.sock"),
              "credential": str(root / "operator.json"),
              "node": str(Path(shutil.which("node")).resolve()),
              "build_slot": "t164-" + uuid.uuid4().hex[:12]}
    write_json(root / "instance.json", config)
    claude = shutil.which("claude")
    if not claude:
        raise RuntimeError("Claude is absent from PATH; preserve the prepared instance")
    codex = shutil.which("codex")
    if not codex:
        raise RuntimeError("Codex is absent from PATH; preserve the prepared instance")
    # AGENTS.md real-Codex rule: isolated CODEX_HOME under this instance, only auth.json
    # copied (never logged or archived; deleted with the home after the run), only the
    # fixture repo trusted, only the git add / git commit allow rules. Worker worktrees
    # inherit the repo trust; per-session hooks are passed by the product with the
    # hook authorization below.
    home = root / "codex-home"
    (home / "rules").mkdir(parents=True, mode=0o700)
    shutil.copyfile(Path.home() / ".codex/auth.json", home / "auth.json")
    (home / "auth.json").chmod(0o600)
    # T-164-3: Codex workers use the user's zcode/GLM route. Copy only the
    # openai_base_url line from the user's config (read, never written), so the
    # isolated home reaches the same local proxy; refuse to guess it.
    route = re.findall(r'^openai_base_url\s*=\s*"[^"\n]+"$', (Path.home() / ".codex/config.toml").read_text(encoding="utf-8"), re.M)
    if len(route) != 1:
        raise RuntimeError("Expected one openai_base_url in ~/.codex/config.toml")
    (home / "config.toml").write_text(route[0] + "\n[projects." + json.dumps(str(repo)) + "]\ntrust_level=\"trusted\"\n", encoding="utf-8")
    (home / "rules/default.rules").write_text('prefix_rule(pattern=["git", "add"], decision="allow")\n'
                                             'prefix_rule(pattern=["git", "commit"], decision="allow")\n', encoding="utf-8")
    # Same launch fields as desktop.mjs; Codex points at the isolated home above.
    launch_config = {
        "claude_bin": str(Path(claude).resolve(strict=True)),
        "codex_bin": str(Path(codex).resolve(strict=True)), "codex_home": str(home),
        "role_card": str(SOURCE / "workbench/roles/worker.md"),
        "role_card_revision": BASELINE,
        "reviewer_role_card": str(SOURCE / "workbench/roles/reviewer.md"),
        "reviewer_role_card_revision": BASELINE,
        "monitor_role_card": str(SOURCE / "workbench/roles/monitor.md"),
        "monitor_role_card_revision": BASELINE,
        "code_revision": BASELINE, "source_snapshot": str(SOURCE), "turn_limit": 6,
        "hook_authorization": str(Path(__file__).parent / "card-4.md") +
                              " — T-164 real managed workers; per-session Claude hooks and Codex worker hooks (isolated CODEX_HOME) approved by executor",
        "turn_authorization": str(Path(__file__).parent / "card-4.md") + " — real-turn budget: Claude 40 in app; one Codex worker zcode/GLM-5.3-Flash max, at most 2 in-app Codex sessions at once; stop when usage nears its limit",
    }
    write_json(root / "launch-config.json", launch_config)
    print("INSTANCE=" + str(root), flush=True)
    return root, config


def load(root):
    root = Path(root).resolve(strict=True)
    if root.parent != Path("/private/tmp") or not root.name.startswith("t164-dogfood-"):
        raise RuntimeError("Expected an owned /private/tmp/t164-dogfood-* instance")
    config = json.loads((root / "instance.json").read_text(encoding="utf-8"))
    if config["root"] != str(root) or config["source"] != str(SOURCE):
        raise RuntimeError("Instance ownership mismatch")
    for key, relative in [("repo", "demo-repo"), ("state", "state"),
                          ("user_data", "user-data"), ("socket", "state/control.sock"),
                          ("credential", "operator.json")]:
        if Path(config[key]).resolve() != root / relative:
            raise RuntimeError("Instance path mismatch: " + key)
    return root, config


def runtime_env(config):
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("A2A_", "GIT_CONFIG_")) and k != "ELECTRON_RUN_AS_NODE"}
    env["A2A_OPERATOR_CREDENTIAL"] = config["credential"]
    env.update(TMPDIR=config["root"], TMP=config["root"], TEMP=config["root"])
    return env


def gate(config, command):
    argv = [config["node"], str(SOURCE / "workbench/src/gates/cli.ts"),
            "--state", config["state"], command]
    if command == "daemon_start":
        launch_config = Path(config["root"]) / "launch-config.json"
        if not launch_config.is_file():
            raise RuntimeError("Worker launch configuration missing; preserve this instance and prepare a new one")
        argv += ["--launch-config", str(launch_config)]
    result = subprocess.run(argv, env=runtime_env(config), capture_output=True, text=True, timeout=130)
    log = Path(config["root"]) / "logs" / (command + "-" + uuid.uuid4().hex[:8] + ".json")
    write_json(log, {"argv": argv, "returncode": result.returncode,
                     "stdout": result.stdout, "stderr": result.stderr})
    if result.returncode:
        raise RuntimeError("Lifecycle command failed; inspect " + str(log))
    value = json.loads(result.stdout)
    if value.get("ok") is not True:
        raise RuntimeError("Lifecycle command refused; inspect " + str(log))
    return value


def start(root, config):
    subprocess.run(["git", "-C", str(SOURCE), "diff", "--quiet", BASELINE, "--", "workbench"], check=True)
    if not (root / "startup-started.json").exists():
        write_json(root / "startup-started.json", {"baseline": BASELINE})
        build_env = dict(os.environ, TMPDIR=str(root), TMP=str(root), TEMP=str(root))
        with (root / "logs/build.txt").open("x", encoding="utf-8") as log:
            subprocess.run([config["node"], "app/build.mjs", "--slot", config["build_slot"]],
                           cwd=SOURCE / "workbench", env=build_env,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        gate(config, "daemon_start")
        write_json(root / "daemon-ready.json", {"baseline": BASELINE})
    else:
        if not (root / "daemon-ready.json").exists():
            raise RuntimeError("Previous startup incomplete; preserve logs and report; no automatic retry")
        gate(config, "daemon_status")
    for previous in sorted((root / "logs").glob("electron-*.json")):
        owner = json.loads(previous.read_text(encoding="utf-8"))
        if identity(owner["pid"]) is not None:
            raise RuntimeError("Previous Electron still exists; no duplicate launch: " + str(previous))
    build = root / ("a2a-build-" + config["build_slot"]) / "dist/build.json"
    manifest = json.loads(build.read_text(encoding="utf-8"))
    electron_dir = SOURCE / "workbench/node_modules/electron"
    executable = (electron_dir / "dist" / (electron_dir / "path.txt").read_text().strip()).resolve(strict=True)
    if str(executable).startswith("/Volumes/"):
        raise RuntimeError("Electron must run from the internal disk")
    argv = [str(executable), manifest["main"], "--state", config["state"],
            "--user-data", config["user_data"]]
    tag = uuid.uuid4().hex[:8]
    with (root / ("logs/electron-" + tag + ".txt")).open("xb") as log:
        child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                 env=runtime_env(config), start_new_session=True)
    owner = identity(child.pid)
    write_json(root / ("logs/electron-" + tag + ".json"),
               {"pid": child.pid, "identity": owner, "argv": argv})
    if owner is None:
        raise RuntimeError("Electron exited during launch; inspect logs")
    print("ELECTRON_PID=" + str(child.pid))
    print("DAEMON_PID=" + (root / "state/daemon.pid").read_text().strip())
    for key in ["root", "repo", "state", "user_data", "socket"]:
        print(key.upper() + "=" + config[key])
    print("Launch requested. Confirm window readiness with Computer Use.")


def stop(root, config, all_processes):
    for record in sorted((root / "logs").glob("electron-*.json")):
        owner = json.loads(record.read_text(encoding="utf-8"))
        current = identity(owner["pid"])
        if current is None:
            continue
        if not owner["identity"] or current != owner["identity"]:
            raise RuntimeError("Electron owner changed; no signal sent")
        os.kill(owner["pid"], signal.SIGTERM)
        deadline = time.monotonic() + 15
        while identity(owner["pid"]) is not None:
            if time.monotonic() >= deadline:
                raise RuntimeError("Electron exit unconfirmed; preserve instance")
            time.sleep(0.2)
    if all_processes:
        pid = int((root / "state/daemon.pid").read_text())
        owner = identity(pid)
        if owner is None or config["state"] not in owner:
            raise RuntimeError("Daemon owner unconfirmed; preserve instance")
        gate(config, "daemon_stop")
        deadline = time.monotonic() + 30
        while identity(pid) is not None or Path(config["socket"]).exists():
            if time.monotonic() >= deadline:
                raise RuntimeError("Daemon exit unconfirmed; preserve instance")
            time.sleep(0.2)
    print("Stopped " + ("UI and daemon" if all_processes else "UI only; daemon retained"))
    print("Evidence preserved at " + str(root))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "start", "stop"])
    parser.add_argument("root", nargs="?")
    parser.add_argument("--all", action="store_true", help="Stop daemon as well as UI")
    args = parser.parse_args()
    if args.action == "stop" and not args.root:
        parser.error("stop requires an instance root")
    if args.action == "prepare" and args.root:
        parser.error("prepare always creates a new instance")
    if args.all and args.action != "stop":
        parser.error("--all is only valid with stop")
    new = args.root is None
    root, config = prepare() if new else load(args.root)
    if args.action == "start":
        start(root, config)
    elif args.action == "stop":
        stop(root, config, args.all)
