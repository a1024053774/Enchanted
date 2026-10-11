#!/bin/bash
# T-079 red/green probe. Run from the executor's Herdr pane, outside Codex's sandbox.
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
CANDIDATE = "8ab5177d09dcb25f57a50ad2166dc0006ea99ce3"
EVIDENCE = REPO / "evidence/2026-10-11-batch13/T-079"
if len(sys.argv) != 2 or sys.argv[1] not in ("red", "green"):
    raise SystemExit("用法：bash evidence/2026-10-11-batch13/T-079/outside-sandbox.sh red|green")
stage = sys.argv[1]
run_id = stage + "-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
artifacts = EVIDENCE / run_id
artifacts.mkdir()
shutil.copyfile(EVIDENCE / "outside-sandbox.sh", artifacts / "runner.sh")
env = {k: v for k, v in os.environ.items() if not k.startswith(("A2A_", "GIT_CONFIG_"))}
env.update(PYTHONDONTWRITEBYTECODE="1", GIT_AUTHOR_NAME="T-079 fixture",
           GIT_AUTHOR_EMAIL="t079@example.invalid", GIT_COMMITTER_NAME="T-079 fixture",
           GIT_COMMITTER_EMAIL="t079@example.invalid")
commands = artifacts / "commands.jsonl"


def run(argv, *, cwd=REPO, check=True, timeout=95):
    started = time.monotonic()
    try:
        result = subprocess.run([str(v) for v in argv], cwd=cwd, env=env,
                                text=True, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        with commands.open("a", encoding="utf-8") as out:
            out.write(json.dumps(dict(argv=[str(v) for v in argv], cwd=str(cwd),
                                      timeout=timeout, error=str(exc),
                                      stdout=exc.stdout.decode("utf-8", errors="backslashreplace") if isinstance(exc.stdout, bytes) else exc.stdout,
                                      stderr=exc.stderr.decode("utf-8", errors="backslashreplace") if isinstance(exc.stderr, bytes) else exc.stderr),
                                 ensure_ascii=False) + "\n")
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
    if server.get("version") != "0.9.3" or server.get("compatible") is not True:
        raise RuntimeError("server 版本或协议与已核对的红态环境不同；停止，不修改 server")
    run(["herdr", "--version"])
    version = run(["codex", "--version"]).stdout.strip()
    if version != "codex-cli 0.162.1":
        raise RuntimeError("CLI 版本与开工记录不同，停止；不处理更新提示")
    # Clone metadata is private. Detach its HEAD and materialize only launcher dependencies.
    revision = run(["git", "rev-parse", BASE if stage == "red" else CANDIDATE]).stdout.strip()
    frozen = Path(tempfile.mkdtemp(prefix="a2a-t079-"+stage+"-source-", dir="/tmp")) / "repo"
    run(["git", "clone", "--quiet", "--shared", "--no-checkout", REPO, frozen])
    run(["git", "update-ref", "--no-deref", "HEAD", revision], cwd=frozen)
    run(["git", "restore", "--source", revision, "--worktree", "scripts", ".project-map/roles/worker.md"], cwd=frozen)
    baseline = frozen / "scripts/launch-worker"
    shutil.copyfile(baseline, artifacts / (stage+"-launch-worker.py"))
    fixture = Path(tempfile.mkdtemp(prefix="a2a-t079-fixture-", dir="/tmp")).resolve()
    roles = fixture / ".project-map/roles"
    roles.mkdir(parents=True)
    (roles / "worker.md").write_text("T-079 无模型回合启动夹具。不得发送任务。\n", encoding="utf-8")
    run(["git", "init", "-q", "-b", "fixture"], cwd=fixture)
    run(["git", "add", ".project-map/roles/worker.md"], cwd=fixture)
    run(["git", "-c", "core.hooksPath=/dev/null", "commit", "-qm", "T-079 fixture seed"], cwd=fixture)
    project_commit = run(["git", "rev-parse", "HEAD"], cwd=fixture).stdout.strip()
    home = Path(tempfile.mkdtemp(prefix="a2a-t079-codex-home-", dir="/tmp")).resolve()
    shutil.copyfile(Path.home() / ".codex/auth.json", home / "auth.json")
    (home / "auth.json").chmod(0o600)
    (home / "config.toml").write_text("[projects."+json.dumps(str(fixture))+"]\ntrust_level = \"trusted\"\n", encoding="utf-8")
    rules = home / "rules"
    rules.mkdir()
    (rules / "default.rules").write_text('prefix_rule(pattern=["git", "add"], decision="allow")\n'
                                         'prefix_rule(pattern=["git", "commit"], decision="allow")\n', encoding="utf-8")
    (artifacts / "context.json").write_text(json.dumps(dict(baseline=BASE, revision=revision, frozen=str(frozen),
                fixture=str(fixture), repetitions=10, no_prompts=True,
                command="bash evidence/2026-10-11-batch13/T-079/outside-sandbox.sh "+stage), indent=2)+"\n", encoding="utf-8")
    for index in range(1, 11):
        case = artifacts / f"launch-{index:02d}"
        case.mkdir()
        name = "t079-" + stage + "-" + uuid.uuid4().hex[:10]
        attempt, session = run_id+f"-{index:02d}", "session-"+uuid.uuid4().hex
        logfile = fixture / "records/launches.jsonl"
        before = logfile.read_bytes() if logfile.exists() else b""
        launched = run([baseline, "--root", fixture, "--cwd", fixture, "--agent", name,
                        "--project", "t079-fixture", "--task", "T-079-1",
                        "--attempt", attempt, "--session", session,
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
                if stage == "green":
                    expected_argv = ["codex", "-m", "gpt-6.1-sol", "-c", 'model_reasoning_effort="xhigh"',
                                     "-c", 'service_tier="fast"', "-c", "check_for_update_on_startup=false",
                                     "--sandbox", "workspace-write", "--ask-for-approval", "on-request"]
                    expected = dict(schema=1, project="t079-fixture", task="T-079-1", attempt=attempt,
                                    session=session, role="worker", cli="codex", cli_version=version,
                                    model="gpt-6.1-sol", effort="xhigh", service_tier_requested="fast",
                                    argv=expected_argv, cwd=str(fixture), project_commit=project_commit,
                                    launcher_commit=revision, role_card=str(roles / "worker.md"),
                                    role_card_version=project_commit, native_session="unknown")
                    for row in new_rows:
                        if any(row.get(key) != value for key, value in expected.items()):
                            raise RuntimeError("启动记录与独立输入不符；停止")
                        if not row.get("launch_id") or not row.get("created_at"):
                            raise RuntimeError("启动记录身份或时间缺失；停止")
                    if new_rows[0]["launch_id"] != last["launch_id"] or last["phase"] != "started":
                        raise RuntimeError("启动记录身份或阶段改变；停止")
                    if last.get("agent") != name or last.get("herdr_start_argv") != [
                            "herdr", "agent", "start", name, "--kind", "codex", "--pane", pane, "--", *expected_argv[1:]]:
                        raise RuntimeError("Herdr 启动 argv 或 agent 身份不符；停止")
                    if not last.get("herdr_result") or not last.get("observed_at"):
                        raise RuntimeError("Herdr 启动结果或观察时间缺失；停止")
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
                if stage == "green":
                    raise RuntimeError("绿态仍出现 agent_pane_busy；停止，不重试，交执行主控判断")
                code = "agent_pane_busy"
            results.append(dict(index=index, agent=name, pane=pane, exit_code=launched.returncode,
                                outcome=code, launch_id=last["launch_id"]))
        finally:
            # This pane was created by this exact launcher invocation; no task was sent.
            run(["herdr", "pane", "close", pane])
        print(json.dumps(results[-1], ensure_ascii=False), flush=True)
    summary = dict(status="PASS" if stage == "green" else "INCOMPLETE", stage=stage, repetitions=len(results),
                   busy=sum(v["outcome"] == "agent_pane_busy" for v in results), results=results,
                   next="结果交 worker 核对；总任务交付结论不由本探针宣布")
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
