#!/usr/bin/env python3
"""由执行主控运行：真实启动只到首屏，每个自建 pane 都在 finally 中关闭。"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--label", required=True)
    p.add_argument("--count", type=int, default=5, choices=range(1, 11))
    p.add_argument("--launcher", type=Path, default=Path(__file__).with_name("launch-worker.parent"))
    p.add_argument("--cwd", type=Path, required=True)
    p.add_argument("--unregistered", action="store_true", help="反例：只在自建 pane 启动未命名 Codex")
    p.add_argument("--expect-diagnostics", action="store_true", help="核对失败记录包含错误身份与 pane")
    args = p.parse_args()
    if os.environ.get("HERDR_ENV") != "1":
        p.error("必须由 Herdr 内的执行主控运行")
    disk = Path("/Volumes/WD-Elements")
    if not disk.is_mount():
        p.error("外置盘未挂载")
    launcher = args.launcher.resolve(strict=True)
    cwd = args.cwd.resolve(strict=True)
    repo = Path(__file__).resolve().parents[3]
    out = disk / "a2a-evidence/2026-10-16-batch16/T-094" / args.label
    out.mkdir(parents=True, exist_ok=False)
    real_herdr = shutil.which("herdr")
    env = {k: v for k, v in os.environ.items() if not k.startswith(("A2A_", "GIT_CONFIG_"))}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(repo / "scripts")
    env.update(GIT_AUTHOR_NAME="T094 probe", GIT_AUTHOR_EMAIL="probe@example.invalid",
               GIT_COMMITTER_NAME="T094 probe", GIT_COMMITTER_EMAIL="probe@example.invalid")

    def run(argv):
        started = time.monotonic()
        r = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=85)
        return dict(argv=argv, returncode=r.returncode, stdout=r.stdout, stderr=r.stderr,
                    seconds=time.monotonic() - started)

    summary = dict(label=args.label, cwd=str(cwd), launcher=str(launcher), planned=args.count,
                   model_turns=0, unregistered_counterexample=args.unregistered, attempts=[], versions={})
    for tool in ("herdr", "codex"):
        summary["versions"][tool] = run([tool, "--version"])
    summary["versions"]["server"] = run([real_herdr, "status", "--json"])
    summary["commit"] = run(["git", "-C", str(repo), "rev-parse", "HEAD"])["stdout"].strip()
    # 身份夹具与 CODEX_HOME 分开；只复制登录凭据，结束必删整个 home。
    with tempfile.TemporaryDirectory(prefix="t094-home-", dir="/tmp") as home_name:
        home = Path(home_name)
        shutil.copyfile(Path.home() / ".codex/auth.json", home / "auth.json")
        (home / "config.toml").write_text(
            "check_for_update_on_startup = false\n[projects." + json.dumps(str(cwd)) +
            "]\ntrust_level = \"trusted\"\n", encoding="utf-8")
        rules = home / "rules"
        rules.mkdir()
        (rules / "default.rules").write_text(
            'prefix_rule(pattern=["git", "add"], decision="allow")\n'
            'prefix_rule(pattern=["git", "commit"], decision="allow")\n', encoding="utf-8")
        for index in range(args.count):
            case = out / ("attempt-%02d" % (index + 1))
            case.mkdir()
            identity = case / "identity"
            role = identity / ".project-map/roles/worker.md"
            role.parent.mkdir(parents=True)
            shutil.copyfile(repo / ".project-map/roles/worker.md", role)
            for git_args in (["init", "-q"], ["add", ".project-map"], ["commit", "-qm", "probe identity"]):
                result = run(["git", "-C", str(identity), *git_args])
                if result["returncode"]:
                    raise RuntimeError(result)
            proxy = case / "bin"
            proxy.mkdir()
            (proxy / "herdr").write_text("#!" + sys.executable + "\n" + '''
import json, os, shlex, subprocess, sys, time
from pathlib import Path
started = time.monotonic()
real = os.environ['T094_REAL_HERDR']
args = sys.argv[1:]
def call(a):
 r = subprocess.run([real, *a], capture_output=True, text=True, timeout=5)
 with Path(os.environ['T094_TRACE']).open('a', encoding='utf-8') as f:
  f.write(json.dumps(dict(argv=a, returncode=r.returncode, stdout=r.stdout,
                         stderr=r.stderr, injected=True)) + '\\n')
 return r
if os.environ['T094_UNREGISTERED'] == '1' and args[:2] == ['agent', 'start']:
 # 故障注入：真实 Codex 进程已经存在，但从未注册名称。只发 shell 启动命令。
 pane = args[args.index('--pane') + 1]
 r = call(['pane', 'run', pane, shlex.join(['codex', *args[args.index('--')+1:]])])
 if r.returncode == 0:
  deadline = time.monotonic() + 30
  while time.monotonic() < deadline:
   proc = call(['pane', 'process-info', '--pane', pane])
   agent = call(['agent', 'get', pane])
   if proc.returncode == 0 and agent.returncode == 0:
    info = json.loads(proc.stdout)['result']['process_info']
    named = json.loads(agent.stdout)['result']['agent']
    if (any(p['name'] == 'codex' for p in info.get('foreground_processes', []))
        and named.get('agent') == 'codex' and named.get('name') is None):
     r = subprocess.CompletedProcess(args, 1, '', json.dumps({'error': {
       'code': 'agent_name_not_found', 'message': 'T-094 反例：真实 Codex 已起，名称未注册'}}) + '\\n')
     break
   time.sleep(0.1)
  else:
   r = subprocess.CompletedProcess(args, 1, '', json.dumps({'error': {
     'code': 'counterexample_not_established', 'message': '未观察到真实未命名 Codex，反例不能算通过'}}) + '\\n')
else:
 r = subprocess.run([real, *args], capture_output=True, text=True)
with Path(os.environ['T094_TRACE']).open('a', encoding='utf-8') as f:
 f.write(json.dumps(dict(argv=sys.argv[1:], returncode=r.returncode, stdout=r.stdout,
                         stderr=r.stderr, seconds=time.monotonic()-started)) + '\\n')
sys.stdout.write(r.stdout)
sys.stderr.write(r.stderr)
sys.exit(r.returncode)
''', encoding="utf-8")
            (proxy / "herdr").chmod(0o755)
            original_path = env["PATH"]
            env.update(PATH=str(proxy) + os.pathsep + original_path, T094_REAL_HERDR=real_herdr,
                       T094_TRACE=str(case / "herdr.jsonl"), T094_UNREGISTERED="1" if args.unregistered else "0")
            attempt = dict(number=index + 1, pane_ids=[], observations=[], cleanup=[])
            summary["attempts"].append(attempt)
            save(out / "run.json", summary)
            try:
                attempt["launch"] = run([sys.executable, str(launcher), "--root", str(identity),
                    "--cwd", str(cwd), "--agent", "t094-" + uuid.uuid4().hex[:16],
                    "--project", "t094-probe", "--task", "T-094", "--attempt", "probe-" + str(index + 1),
                    "--session", str(uuid.uuid4()), "--codex-home", str(home)])
            finally:
                env["PATH"] = original_path
                trace = case / "herdr.jsonl"
                calls = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()] if trace.exists() else []
                attempt["start_calls"] = sum(c["argv"][:2] == ["agent", "start"] for c in calls)
                attempt["real_agent_start_calls"] = 0 if args.unregistered else attempt["start_calls"]
                attempt["unmanaged_codex_start_calls"] = sum(c["argv"][:2] == ["pane", "run"] for c in calls)
                records = identity / "records/launches.jsonl"
                if records.exists():
                    attempt["launch_record"] = json.loads(records.read_text(encoding="utf-8").splitlines()[-1])
                for call in calls:
                    if call["argv"][:2] == ["pane", "split"] and call["returncode"] == 0:
                        pane = json.loads(call["stdout"])["result"]["pane"]["pane_id"]
                        attempt["pane_ids"].append(pane)
                # 只读取、关闭该次 split 返回的 ID，从不依赖焦点或猜测 ID。
                for pane in attempt["pane_ids"]:
                    try:
                        for argv in ([real_herdr, "pane", "process-info", "--pane", pane],
                                     [real_herdr, "agent", "get", pane],
                                     [real_herdr, "pane", "read", pane, "--source", "recent-unwrapped", "--lines", "60"]):
                            attempt["observations"].append(run(argv))
                    finally:
                        attempt["cleanup"].append(run([real_herdr, "pane", "close", pane]))
                save(out / "run.json", summary)
            if any(c["returncode"] != 0 and 'pane_not_found' not in c["stderr"] for c in attempt["cleanup"]):
                raise RuntimeError("自建 pane 清理失败，停止后续启动；见 run.json")
    summary["start_calls"] = sum(a["start_calls"] for a in summary["attempts"])
    violations = []
    for a in summary["attempts"]:
        row = a.get("launch_record", {})
        if a["start_calls"] != 1:
            violations.append("启动次数不为 1：" + str(a["number"]))
        if args.expect_diagnostics and a["launch"]["returncode"] != 0:
            if not (row.get("error_code") and row.get("herdr_stderr") and row.get("pane") == a["pane_ids"][0]
                    and row.get("pane_disposition") == "retained_for_controller"):
                violations.append("失败诊断不完整：" + str(a["number"]))
        if args.unregistered and not (row.get("outcome") == "started_unregistered"
                                     and row.get("error_code") == "agent_name_not_found"
                                     and a["launch"]["returncode"] != 0):
            violations.append("半成功反例未成立：" + str(a["number"]))
    summary["violations"] = violations
    save(out / "run.json", summary)
    if violations:
        raise RuntimeError(violations)
    print(json.dumps(dict(archive=str(out), attempts=len(summary["attempts"]),
                          start_calls=summary["start_calls"], model_turns=0), ensure_ascii=False))


if __name__ == "__main__":
    main()
