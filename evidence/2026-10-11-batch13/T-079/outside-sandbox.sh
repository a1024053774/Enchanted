#!/bin/bash
# T-079 red baseline probe. Run from the executor's Herdr pane, outside Codex's sandbox.
# No agent prompt, raw terminal input, server restart, or global configuration write.
set -euo pipefail
cd "$(dirname "$0")/../../.."
test "${HERDR_ENV:-}" = 1
exec python3 -B - "$@" <<'PY'
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid

REPO = Path.cwd().resolve()
BASE = "ffe7ecb85e9e224d5917183b48754f15ac0c5ba6"
EVIDENCE = REPO / "evidence/2026-10-11-batch13/T-079"
if len(sys.argv) != 2 or sys.argv[1] != "red":
    raise SystemExit("用法：bash evidence/2026-10-11-batch13/T-079/outside-sandbox.sh red")
run_id = "red-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
artifacts = EVIDENCE / run_id
artifacts.mkdir()
shutil.copyfile(EVIDENCE / "outside-sandbox.sh", artifacts / "runner.sh")
env = {k: v for k, v in os.environ.items() if not k.startswith(("A2A_", "GIT_CONFIG_"))}
env.update(PYTHONDONTWRITEBYTECODE="1", GIT_AUTHOR_NAME="T-079 fixture",
           GIT_AUTHOR_EMAIL="t079@example.invalid", GIT_COMMITTER_NAME="T-079 fixture",
           GIT_COMMITTER_EMAIL="t079@example.invalid")
commands = artifacts / "commands.jsonl"


def run(argv, *, cwd=REPO, check=True, timeout=50):
    started = time.monotonic()
    try:
        result = subprocess.run([str(v) for v in argv], cwd=cwd, env=env,
                                text=True, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        with commands.open("a", encoding="utf-8") as out:
            out.write(json.dumps(dict(argv=[str(v) for v in argv], cwd=str(cwd),
                                      timeout=timeout, error=str(exc)), ensure_ascii=False) + "\n")
        raise
    with commands.open("a", encoding="utf-8") as out:
        out.write(json.dumps(dict(argv=[str(v) for v in argv], cwd=str(cwd),
                                  exit_code=result.returncode, stdout=result.stdout,
                                  stderr=result.stderr, elapsed_seconds=time.monotonic()-started),
                             ensure_ascii=False) + "\n")
    if check and result.returncode:
        raise RuntimeError(f"命令失败：{argv!r}；见 {commands}")
    return result


def response(argv):
    return json.loads(run(argv).stdout)["result"]


results = []
home = None
fixture = None
try:
    server = json.loads(run(["herdr", "status", "server", "--json"]).stdout)
    (artifacts / "server.json").write_text(json.dumps(server, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    run(["herdr", "--version"])
    version = run(["codex", "--version"]).stdout.strip()
    if version != "codex-cli 0.162.1":
        raise RuntimeError("CLI 版本与开工记录不同，停止；不处理更新提示")
    # Clone metadata is private. Detach its HEAD and materialize only launcher dependencies.
    frozen = Path(tempfile.mkdtemp(prefix="a2a-t079-baseline-", dir="/tmp")) / "repo"
    run(["git", "clone", "--quiet", "--shared", "--no-checkout", REPO, frozen])
    run(["git", "update-ref", "--no-deref", "HEAD", BASE], cwd=frozen)
    run(["git", "restore", "--source", BASE, "--worktree", "scripts", ".project-map/roles/worker.md"], cwd=frozen)
    baseline = frozen / "scripts/launch-worker"
    shutil.copyfile(baseline, artifacts / "baseline-launch-worker.py")
    fixture = Path(tempfile.mkdtemp(prefix="a2a-t079-fixture-", dir="/tmp")).resolve()
    roles = fixture / ".project-map/roles"
    roles.mkdir(parents=True)
    (roles / "worker.md").write_text("T-079 无模型回合启动夹具。不得发送任务。\n", encoding="utf-8")
    run(["git", "init", "-q", "-b", "fixture"], cwd=fixture)
    run(["git", "add", ".project-map/roles/worker.md"], cwd=fixture)
    run(["git", "-c", "core.hooksPath=/dev/null", "commit", "-qm", "T-079 fixture seed"], cwd=fixture)
    home = Path(tempfile.mkdtemp(prefix="a2a-t079-codex-home-", dir="/tmp")).resolve()
    shutil.copyfile(Path.home() / ".codex/auth.json", home / "auth.json")
    (home / "auth.json").chmod(0o600)
    (home / "config.toml").write_text("[projects."+json.dumps(str(fixture))+"]\ntrust_level = \"trusted\"\n", encoding="utf-8")
    rules = home / "rules"
    rules.mkdir()
    (rules / "default.rules").write_text('prefix_rule(pattern=["git", "add"], decision="allow")\n'
                                         'prefix_rule(pattern=["git", "commit"], decision="allow")\n', encoding="utf-8")
    (artifacts / "context.json").write_text(json.dumps(dict(baseline=BASE, frozen=str(frozen),
                fixture=str(fixture), repetitions=10, no_prompts=True,
                command="bash evidence/2026-10-11-batch13/T-079/outside-sandbox.sh red"), indent=2)+"\n", encoding="utf-8")
    for index in range(1, 11):
        case = artifacts / f"launch-{index:02d}"
        case.mkdir()
        name = "t079-red-" + uuid.uuid4().hex[:10]
        logfile = fixture / "records/launches.jsonl"
        before = logfile.read_bytes() if logfile.exists() else b""
        launched = run([baseline, "--root", fixture, "--cwd", fixture, "--agent", name,
                        "--project", "t079-fixture", "--task", "T-079-1",
                        "--attempt", run_id+f"-{index:02d}", "--session", "session-"+uuid.uuid4().hex,
                        "--codex-home", home], check=False)
        (case / "stdout.txt").write_text(launched.stdout, encoding="utf-8")
        (case / "stderr.txt").write_text(launched.stderr, encoding="utf-8")
        after = logfile.read_bytes()
        if not after.startswith(before):
            raise RuntimeError("启动记录并非追加；停止并保留现场")
        new_rows = [json.loads(line) for line in after[len(before):].splitlines()]
        (case / "launches.jsonl").write_bytes(after[len(before):])
        if len(new_rows) != 2 or new_rows[0]["phase"] != "prepared":
            raise RuntimeError("启动记录数量或阶段异常，停止")
        last = new_rows[-1]
        pane = last.get("pane")
        if not pane:
            raise RuntimeError("启动没有记录自己的 pane；停止，不猜测或关闭其他 pane")
        try:
            pane_info = response(["herdr", "pane", "get", pane])
            processes = response(["herdr", "pane", "process-info", "--pane", pane])
            (case / "pane.json").write_text(json.dumps(pane_info, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
            (case / "processes.json").write_text(json.dumps(processes, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
            if launched.returncode == 0:
                agent = response(["herdr", "agent", "get", name])["agent"]
                if agent.get("agent_status") not in ("idle", "done") or agent.get("pane_id") != pane:
                    raise RuntimeError("启动后 agent 非空闲或身份不符；停止，不发送输入")
                code = "started"
            else:
                # Herdr serializes protocol errors as one JSON object on stderr.
                codes = []
                for line in launched.stderr.splitlines():
                    try:
                        value = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(value, dict) and isinstance(value.get("error"), dict):
                        codes.append(value["error"].get("code"))
                if codes != ["agent_pane_busy"] or last["phase"] != "failed":
                    raise RuntimeError("出现非预期启动失败；停止，交执行主控判断")
                code = "agent_pane_busy"
            results.append(dict(index=index, agent=name, pane=pane, exit_code=launched.returncode,
                                outcome=code, launch_id=last["launch_id"]))
        finally:
            # This pane was created by this exact launcher invocation; no task was sent.
            run(["herdr", "pane", "close", pane])
        print(json.dumps(results[-1], ensure_ascii=False), flush=True)
    summary = dict(status="INCOMPLETE", stage="red", repetitions=len(results),
                   busy=sum(v["outcome"] == "agent_pane_busy" for v in results), results=results,
                   next="红态结果交 worker；修复与同次数绿态尚未运行")
    (artifacts / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    status = run(["python3", "/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py",
                  "status", "--root", REPO])
    (artifacts / "project-map-status.txt").write_text(status.stdout+status.stderr, encoding="utf-8")
    print(str(artifacts), flush=True)
finally:
    if fixture is not None:
        with tarfile.open(artifacts / "fixture.tar.gz", "w:gz") as archive:
            archive.add(fixture, arcname="fixture")
    if home is not None:
        shutil.rmtree(home)
        (artifacts / "isolated-home-removed.txt").write_text("本探针创建的隔离 CODEX_HOME 已删除；未归档凭据。\n", encoding="utf-8")
PY
