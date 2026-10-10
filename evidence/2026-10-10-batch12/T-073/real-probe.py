#!/usr/bin/env python3
"""T-073 的真实交互 Codex 探针；只操作本探针创建的 pane 和 /tmp home。"""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("prepare", "start-red", "prompt", "inspect", "finish"))
    p.add_argument("label")
    args = p.parse_args()
    directory = EVIDENCE / args.label
    if args.action == "prepare":
        directory.mkdir()
        fixture = Path(tempfile.mkdtemp(prefix="a2a-t073-", dir="/tmp")).resolve()
        home = Path(tempfile.mkdtemp(prefix="a2a-t073-codex-", dir="/tmp")).resolve()
        shutil.copyfile(Path.home() / ".codex/auth.json", home / "auth.json")
        (home / "auth.json").chmod(0o600)
        (home / "rules").mkdir()
        (home / "rules/default.rules").write_text(
            'prefix_rule(pattern=["git", "add"], decision="allow")\n'
            'prefix_rule(pattern=["git", "commit"], decision="allow")\n', encoding="utf-8")
        (home / "config.toml").write_text(
            '[projects.' + json.dumps(str(fixture)) + ']\ntrust_level = "trusted"\n', encoding="utf-8")
        # All identity is process-local. Do not write fixture or user git config.
        env = dict(os.environ, GIT_AUTHOR_NAME="T073 fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
                   GIT_COMMITTER_NAME="T073 fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid")
        subprocess.run(["git", "init", "-q", str(fixture)], env=env, check=True)
        state = dict(fixture=str(fixture), codex_home=str(home), label=args.label)
        (directory / "state.json").write_text(json.dumps(state, indent=2)+"\n", encoding="utf-8")
        print(json.dumps(state))
        return
    state = json.loads((directory / "state.json").read_text(encoding="utf-8"))

    def run(argv):
        result = subprocess.run(argv, text=True, capture_output=True)
        row = dict(argv=argv, exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
        with (directory / "commands.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps(row, ensure_ascii=False)+"\n")
        print(result.stdout, end="")
        print(result.stderr, end="")
        if result.returncode:
            raise SystemExit(result.returncode)
        return result.stdout

    if args.action == "start-red":
        reply = json.loads(run(["herdr", "pane", "split", "--current", "--direction", "down",
                                "--cwd", state["fixture"], "--no-focus"]))
        state["pane"] = reply["result"]["pane"]["pane_id"]
        (directory / "state.json").write_text(json.dumps(state, indent=2)+"\n", encoding="utf-8")
        exports = dict(CODEX_HOME=state["codex_home"], GIT_AUTHOR_NAME="T073 fixture",
                       GIT_AUTHOR_EMAIL="fixture@example.invalid", GIT_COMMITTER_NAME="T073 fixture",
                       GIT_COMMITTER_EMAIL="fixture@example.invalid", T073_PROBE_KEY="harmless-sentinel")
        run(["herdr", "pane", "run", state["pane"], "export " + " ".join(
            key+"="+shlex.quote(value) for key,value in exports.items())])
        state["agent"] = "t073-" + args.label
        (directory / "state.json").write_text(json.dumps(state, indent=2)+"\n", encoding="utf-8")
        argv = ["herdr", "agent", "start", state["agent"], "--kind", "codex", "--pane", state["pane"],
                "--", "-m", "gpt-6.1-sol", "-c", 'model_reasoning_effort="xhigh"',
                "-c", 'service_tier="fast"', "-c", "check_for_update_on_startup=false",
                "--sandbox", "workspace-write", "--ask-for-approval", "on-request"]
        run(argv)
    elif args.action == "prompt":
        run([str(ROOT / "scripts/dispatch"), "--batch", "2026-10-10-batch12",
             "--agent", state["agent"], "--role", "worker", "--body-file", str(directory / "prompt.txt")])
    elif args.action == "inspect":
        run(["herdr", "agent", "get", state["agent"]])
        run(["herdr", "agent", "read", state["agent"], "--source", "visible", "--lines", "40"])
    elif args.action == "finish":
        reply = json.loads(run(["herdr", "agent", "get", state["agent"]]))
        # Never close a working agent. Keep the entire fixture, native raw records
        # (except credentials), and hook evidence before removing isolated home.
        pane = reply["result"]["agent"]
        if pane["agent_status"] not in ("idle", "done"):
            raise SystemExit("agent 未 idle；保留现场")
        home = Path(state["codex_home"])
        sessions = directory / "sessions"
        if (home / "sessions").exists():
            shutil.copytree(home / "sessions", sessions)
        run(["herdr", "pane", "close", state["pane"]])
        shutil.rmtree(home)
        with (directory / "commands.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps(dict(cleaned_codex_home=str(home), exists=home.exists()))+"\n")


if __name__ == "__main__":
    main()
