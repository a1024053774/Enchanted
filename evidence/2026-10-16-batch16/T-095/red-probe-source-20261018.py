#!/usr/bin/env python3
# 真实模型预算：单次最多 1 个根提示回合；红、绿各一次合计最多 2 个根回合。
# 不自动回答、不重投、不 resume。根回合限额不是 API 请求数或费用硬限额。
# 只有执行主控核对后，才能在沙箱外加 --approve-one-root-turn 运行。
# 启动会占用 1 个 Codex 名额；主控须确认启动后并行总数不超过 3。
# 默认只打印计划：不复制凭据、不创建 pane、不调用模型。
# 操作顺序：脚本提示 COLLAPSED 时，在自建 pane 用 Shift+→ 折叠；
# 收到 CAPTURED collapsed 后，在自建 pane 用 Shift+← 展开；
# 收到 CAPTURED expanded 后，手动取消问题，不按 Enter 提交答案。
# 操作完每一步，都回脚本终端输入对应确认词；脚本不代按方向键。
"""T-095 真实面板采集草案；只准备探针，不实现状态判定。"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import uuid

EXPECTED_CODEX = "codex-cli 0.163.0"
ARCHIVE = Path("/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-095")
PROMPT = """这是 T-095 提问面板的受控复现，不是开发任务。
不要运行命令，不要读取或修改文件，不要联网，不要创建子 agent。
只调用一次 request_user_input_async，提出固定问题：
“T-095 面板复现：请选择 A 或 B。”选项固定为“A”和“B”。
调用后等待操作者回答，不自行回答，不关闭问题，不再提出第二个问题。
如果没有 request_user_input_async 工具，只回复 PANEL_TOOL_UNAVAILABLE 并结束。
操作者会采集面板的折叠和展开画面，然后取消并关闭本测试。
"""


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def native_args(workspace):
    config = {
        "model_reasoning_effort": "xhigh", "service_tier": "fast",
        "check_for_update_on_startup": False, "web_search": "disabled",
        "features.shell_tool": False, "features.shell_snapshot": False,
        "features.code_mode": False, "features.code_mode_host": False,
        "features.apps": False, "features.plugins": False,
        "features.multi_agent": False, "features.computer_use": False,
        "features.browser_use": False, "features.browser_use_external": False,
        "features.image_generation": False, "features.hooks": False,
        "features.default_mode_request_user_input": True,
        "project_doc_max_bytes": 0,
        f"projects.{json.dumps(str(workspace))}.trust_level": "trusted",
    }
    argv = ["--no-daemon", "-m", "gpt-6.1-sol",
            "--sandbox", "read-only", "--ask-for-approval", "never", "-C", str(workspace)]
    for key, value in config.items():
        argv.extend(["-c", key + "=" + json.dumps(value)])
    return argv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approve-one-root-turn", action="store_true")
    parser.add_argument("--phase", choices=("red", "green"), default="red")
    parser.add_argument("--auth-json", type=Path, default=Path.home() / ".codex/auth.json")
    args = parser.parse_args()
    plan = dict(status="INCOMPLETE", root_turn_limit=1, automatic_answers=0,
                retries=0, expected_codex=EXPECTED_CODEX, prompt=PROMPT,
                argv=["codex", *native_args(Path("/tmp/<new-fixture>"))],
                archive=str(ARCHIVE), wall_seconds=240)
    if not args.approve_one_root_turn:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    if os.environ.get("HERDR_ENV") != "1":
        raise RuntimeError("必须从执行主控的 Herdr shell 运行")
    if not os.isatty(0):
        raise RuntimeError("需要操作者在终端逐步核对，不支持无人值守")
    if not Path("/Volumes/WD-Elements").is_mount():
        raise RuntimeError("外置盘未挂载，不回退到内置盘")
    if not args.auth_json.is_file():
        raise RuntimeError("auth.json 不存在；不尝试登录")
    os.umask(0o077)
    run_id = args.phase + "-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    output = ARCHIVE / run_id
    output.mkdir(parents=True, exist_ok=False)
    manifest = dict(plan, run_id=run_id, phase=args.phase, started_at=now(),
                    probe_launch="launch-t095-probe-" + uuid.uuid4().hex,
                    parent_worker="s16-t095", task="T-095", attempt="a1",
                    parent_launch="launch-4b1abba18e87460da9cbacec04905c78",
                    pane=None, submitted_prompts=0, code_revision=None)
    pane, isolated, workspace = None, None, None
    sequence = 0

    def save():
        (output / "run.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def call(argv, *, timeout=15):
        nonlocal sequence
        sequence += 1
        prefix = output / f"command-{sequence:03d}"
        prefix.with_suffix(".argv.json").write_text(json.dumps(dict(at=now(), argv=argv), ensure_ascii=False) + "\n", encoding="utf-8")
        try:
            result = subprocess.run(argv, capture_output=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            prefix.with_suffix(".stdout").write_bytes(exc.stdout or b"")
            prefix.with_suffix(".stderr").write_bytes(exc.stderr or b"")
            prefix.with_suffix(".exit").write_text("timeout; effect unknown\n", encoding="utf-8")
            raise
        prefix.with_suffix(".stdout").write_bytes(result.stdout)
        prefix.with_suffix(".stderr").write_bytes(result.stderr)
        prefix.with_suffix(".exit").write_text(str(result.returncode) + "\n", encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"命令失败，保留原件：{prefix}；不自动重试")
        return result.stdout

    def capture(label):
        print(f"CAPTURING {label}：正在只读采集 {pane}，此时请不要在该 pane 输入或切换形态。", flush=True)
        first = sequence + 1
        for argv in (
            ["herdr", "agent", "get", pane],
            ["herdr", "agent", "read", pane, "--source", "visible", "--format", "text"],
            ["herdr", "agent", "read", pane, "--source", "visible", "--format", "ansi"],
            ["herdr", "agent", "read", pane, "--source", "detection", "--format", "text"],
            ["herdr", "pane", "process-info", "--pane", pane],
            ["herdr", "agent", "get", pane],
        ):
            call(argv)
        manifest.setdefault("captures", []).append(dict(label=label, first=first, last=sequence, at=now(),
                                                       layout_source="operator_declaration"))
        save()
        print(f"CAPTURED {label}：{pane} 采集完成；下一步以脚本提示为准。", flush=True)

    def confirm(token, instruction):
        print(instruction, flush=True)
        if input(f"输入 {token} 继续，其他输入终止：").strip() != token:
            raise RuntimeError("操作者终止；不再发送提示")

    def expire(_signum, _frame):
        raise TimeoutError("达到 240 秒探针期限，停止并关闭自建 pane")

    signal.signal(signal.SIGALRM, expire)
    signal.alarm(240)
    save()
    try:
        manifest["herdr_status"] = call(["herdr", "status"]).decode("utf-8")
        repository = Path(__file__).resolve().parents[3]
        manifest["code_revision"] = call(["git", "-C", str(repository), "rev-parse", "HEAD"]).decode("ascii").strip()
        scratch = Path(tempfile.mkdtemp(prefix="t095-panel-", dir="/tmp"))
        isolated, workspace = scratch / "codex-home", scratch / "fixture"
        isolated.mkdir(mode=0o700)
        workspace.mkdir(mode=0o700)
        env = dict(os.environ, CODEX_HOME=str(isolated))
        version = subprocess.run(["codex", "--version"], env=env, capture_output=True, check=False)
        (output / "version.stdout").write_bytes(version.stdout)
        (output / "version.stderr").write_bytes(version.stderr)
        if version.returncode or version.stdout.decode("utf-8").strip() != EXPECTED_CODEX:
            raise RuntimeError("Codex 版本不符，未复制凭据或启动 agent")
        shutil.copyfile(args.auth_json, isolated / "auth.json")
        os.chmod(isolated / "auth.json", 0o600)
        split = json.loads(call(["herdr", "pane", "split", "--current", "--direction", "down",
                                 "--cwd", str(workspace), "--no-focus", "--env", "CODEX_HOME=" + str(isolated)]))
        pane = split["result"]["pane"]["pane_id"]
        manifest.update(pane=pane, isolated_home=str(isolated), fixture=str(workspace))
        save()
        screen = call(["herdr", "pane", "read", pane, "--source", "visible"]).decode("utf-8")
        print(screen, flush=True)
        confirm("SHELL_READY", f"只检查新建 {pane}：确认真实 shell 命令提示符已就绪，且没有初始化/更新提问。主控另核对并行 Codex 启动后不超过 3。")
        agent = "t095-probe-" + uuid.uuid4().hex[:10]
        argv = ["herdr", "agent", "start", agent, "--kind", "codex", "--pane", pane,
                "--timeout", "30000", "--", *native_args(workspace)]
        manifest.update(worker=agent, herdr_start_argv=argv)
        save()
        call(argv, timeout=35)
        capture("startup")
        confirm("CODEX_IDLE", f"检查 {pane} 是 Codex 0.163.0 的空闲输入框；如出现登录、信任或更新阻断，终止，不能按 Enter 放行。")
        current = json.loads(call(["herdr", "agent", "get", pane]))["result"]["agent"]
        if current.get("name") != agent or current.get("pane_id") != pane or current.get("agent_status") not in ("idle", "done"):
            raise RuntimeError("启动身份或空闲状态不符，不发送提示")
        manifest["submitted_prompts"] = 1  # 写入前记意图；调用结果未知也不重投。
        save()
        call(["herdr", "agent", "prompt", pane, PROMPT])
        capture("after-submit")
        confirm("COLLAPSED", f"步骤 1：提示已经提交。现在切到自建 {pane}，等提问面板出现；若当前展开，按 Shift+→ 折叠，若已折叠则保持。不要输入答案，也不要按 Enter。确认是同一待答问题后，回到运行本脚本的终端输入 COLLAPSED，脚本才会采集折叠画面。若工具不可用或没有同类面板，输入其他内容终止，不重投。")
        capture("collapsed")
        confirm("EXPANDED", f"步骤 2：已输出 CAPTURED collapsed。现在切回自建 {pane}，按 Shift+← 展开，核对同一个问题内容。不要输入答案。完成后回到脚本终端输入 EXPANDED，脚本才会采集展开画面。")
        capture("expanded")
        confirm("CANCELLED", f"步骤 3：已输出 CAPTURED expanded。现在只在自建 {pane} 使用 CLI 的取消/关闭操作结束这条待答问题；仅当界面明确以 Esc 取消时才按 Esc。Shift+→ 只折叠，不能当作取消。不要按 Enter 提交答案。确认问题不再待答后，回脚本终端输入 CANCELLED，脚本采集退出后的画面，然后关闭自建 pane 并清理隔离 CODEX_HOME。若无法取消，输入其他内容终止，脚本仍会关闭自建 pane。")
        capture("cancelled")
        manifest["collection_complete"] = True
        # 采集完成不等于红态、绿态或验收通过；由独立检查核对原件。
    except (OSError, ValueError, KeyError, RuntimeError, TimeoutError, subprocess.TimeoutExpired, KeyboardInterrupt, EOFError) as exc:
        manifest["error"] = str(exc)
    finally:
        signal.alarm(0)
        if pane is not None:
            try:
                call(["herdr", "pane", "close", pane])
                manifest["pane_closed"] = True
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
                manifest["cleanup_error"] = str(exc)
                manifest["pane_closed"] = False
        if isolated is not None:
            try:
                sessions = isolated / "sessions"
                if sessions.exists():
                    shutil.copytree(sessions, output / "native-sessions")
            except OSError as exc:
                manifest["native_archive_error"] = str(exc)
            finally:
                shutil.rmtree(isolated)
                manifest["isolated_home_deleted"] = not isolated.exists()
        if workspace is not None:
            manifest["fixture_entries_after"] = sorted(str(p.relative_to(workspace)) for p in workspace.rglob("*"))
            if manifest["fixture_entries_after"]:
                manifest["status"] = "NO_GO"
                manifest["fixture_preserved"] = str(workspace)
        manifest["ended_at"] = now()
        save()
    print(json.dumps(dict(status=manifest["status"], evidence=str(output), pane_closed=manifest.get("pane_closed"),
                          isolated_home_deleted=manifest.get("isolated_home_deleted")), ensure_ascii=False))
    return 0 if (manifest.get("collection_complete") and manifest.get("pane_closed")
                 and manifest.get("isolated_home_deleted") and not manifest.get("fixture_entries_after")
                 and not manifest.get("native_archive_error")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
