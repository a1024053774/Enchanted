#!/usr/bin/env python3
"""回放起点版本红态的只读采集；不启动 Herdr、Codex 或真实模型。"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
BASE = "3c9016d0230223945f0e16543b230a047c2ad032"
SOURCE = Path("/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-095/red-20261018T110936Z-f4d263d1")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        raise ValueError("报告已存在；不覆盖原件")
    original = json.loads((SOURCE / "run.json").read_text(encoding="utf-8"))
    assert original["code_revision"] == BASE
    tree = subprocess.run(["git", "-C", str(REPO), "ls-tree", "-r", "--name-only", BASE, "scripts"],
                          capture_output=True, text=True, check=True).stdout.splitlines()
    assert "scripts/agent-status" not in tree
    scan_argv = ["git", "-C", str(REPO), "grep", "-n", "-F", "-e", "waiting_controller_answer", "-e", "等待主控回答", BASE, "--", "scripts"]
    scan = subprocess.run(scan_argv, capture_output=True, text=True, check=False)
    assert scan.returncode == 1 and not scan.stdout and not scan.stderr
    source = HERE / "red-probe-source-20261018.py"
    spec = importlib.util.spec_from_file_location("before_status_probe", source)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    directory = Path(tempfile.mkdtemp(prefix="before-status-", dir=args.report.parent.parent))
    (directory / "auth.json").write_text('{"test_only":"T095_BEFORE_AUTH_CANARY"}\n', encoding="utf-8")
    (directory / "baseline-scripts.txt").write_text("\n".join(tree) + "\n", encoding="utf-8")
    probe.ARCHIVE = directory / "replay"
    tokens = iter(("SHELL_READY", "CODEX_IDLE", "COLLAPSED", "EXPANDED", "CANCELLED"))
    first = json.loads((SOURCE / "command-005.argv.json").read_text(encoding="utf-8"))["argv"]
    agent = first[3]
    identifiers = iter((uuid.UUID(original["run_id"].rsplit("-", 1)[1].ljust(32, "0")),
                        uuid.UUID(original["probe_launch"].removeprefix("launch-t095-probe-")),
                        uuid.UUID(agent.removeprefix("t095-probe-").ljust(32, "0"))))
    sequence = 0
    calls = []

    def archived_call(argv, **kwargs):
        nonlocal sequence
        if argv == ["codex", "--version"]:
            calls.append(dict(argv=argv, source="version.stdout"))
            return subprocess.CompletedProcess(argv, 0, (SOURCE / "version.stdout").read_bytes(), b"")
        sequence += 1
        prefix = SOURCE / f"command-{sequence:03d}"
        expected = json.loads(prefix.with_suffix(".argv.json").read_text(encoding="utf-8"))["argv"]
        # 隔离路径与采集器所在路径由本次临时目录决定；其他命令身份和顺序沿用原件。
        assert argv[:3] == expected[:3], (argv, expected)
        if argv[:2] == ["herdr", "agent"] and argv[2] in ("get", "read", "prompt"):
            assert argv == expected, (argv, expected)
        calls.append(dict(argv=argv, archived_argv=expected, source=str(prefix)))
        return subprocess.CompletedProcess(argv, int(prefix.with_suffix(".exit").read_text()),
                                           prefix.with_suffix(".stdout").read_bytes(), prefix.with_suffix(".stderr").read_bytes())

    real_mkdtemp = tempfile.mkdtemp

    def scratch(**kwargs):
        return real_mkdtemp(prefix=kwargs["prefix"], dir=directory)

    with patch.dict(os.environ, {"HERDR_ENV": "1"}), patch.object(os, "isatty", return_value=True), \
            patch.object(Path, "is_mount", return_value=True), patch("builtins.input", side_effect=lambda _: next(tokens)), \
            patch.object(probe.subprocess, "run", side_effect=archived_call), \
            patch.object(probe.uuid, "uuid4", side_effect=lambda: next(identifiers)), \
            patch.object(probe.tempfile, "mkdtemp", side_effect=scratch), \
            patch.object(sys, "argv", [str(source), "--approve-one-root-turn", "--phase", "red", "--auth-json", str(directory / "auth.json")]):
        code = probe.main()
    replay = next((directory / "replay").glob("*/run.json"))
    run = json.loads(replay.read_text(encoding="utf-8"))
    assert code == 0 and run["collection_complete"] and sequence == 38
    panels = []
    for capture in run["captures"]:
        if capture["label"] not in ("collapsed", "expanded"):
            continue
        states = []
        for index in range(capture["first"], capture["last"] + 1):
            name = f"command-{index:03d}"
            assert (replay.parent / (name + ".stdout")).read_bytes() == (SOURCE / (name + ".stdout")).read_bytes()
            argv = json.loads((replay.parent / (name + ".argv.json")).read_text(encoding="utf-8"))["argv"]
            if argv[1:3] == ["agent", "get"]:
                states.append(json.loads((replay.parent / (name + ".stdout")).read_text())["result"]["agent"]["agent_status"])
        assert states == ["blocked", "blocked"]
        panels.append(dict(label=capture["label"],raw_states=states,waiting_state_present=False,original_bytes_preserved=True))
    assert len(panels) == 2 and not run.get("projections")
    assert all(b"T095_BEFORE_AUTH_CANARY" not in p.read_bytes() for p in (directory / "replay").rglob("*") if p.is_file())
    (directory / "auth.json").unlink()  # 仅本次生成的假凭据夹具，不归档凭据来源。
    report = dict(status="PASS", claim="修前没有独立等待状态；不是修前两形态 working", baseline=BASE,
                  baseline_agent_status_entry_present=False, baseline_script_label_scan=dict(argv=scan_argv,returncode=scan.returncode,stdout=scan.stdout),
                  source_archive=str(SOURCE),source_collector=str(source),panels=panels,collector_returncode=code,
                  original_collector_unchanged=True,real_model_turns=0,fixture=str(directory),calls=calls,
                  adaptations=["版本检查与 Herdr 子进程均返回保存的原始回复；没有连接 server。", "只替换临时路径和假凭据来源；读屏、原状态、命令身份及顺序保留。"],
                  limitation="基线不存在新的 agent-status 入口；回放其原有 Herdr 读取采集器，不虚构修前的状态转换器。")
    with args.report.open("x",encoding="utf-8") as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2);stream.write("\n")
    print(json.dumps(dict(status=report["status"],baseline=BASE,panels=panels,real_model_turns=0),ensure_ascii=False))


if __name__ == "__main__":
    main()
