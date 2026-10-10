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
    p.add_argument("action", choices=("prepare", "start-red", "start-green", "prompt", "inspect", "collect", "plain", "finish"))
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
    elif args.action == "start-green":
        fixture = Path(state["fixture"])
        env = dict(os.environ, GIT_AUTHOR_NAME="T073 fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
                   GIT_COMMITTER_NAME="T073 fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid")
        seed = subprocess.run(["git", "-C", str(fixture), "commit", "--allow-empty", "-m", "plain seed"],
                              env=env, capture_output=True, text=True)
        with (directory / "commands.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps(dict(argv=seed.args, exit_code=seed.returncode, stdout=seed.stdout, stderr=seed.stderr))+"\n")
        if seed.returncode:
            raise SystemExit(seed.returncode)
        original = fixture / ".git/hooks/prepare-commit-msg"
        original.write_text("#!/bin/sh\necho original-prepare >> original-hook-trace.txt\n", encoding="utf-8")
        original.chmod(0o755)
        state["agent"] = "t073-" + args.label
        result = json.loads(run([str(ROOT / "scripts/launch-worker"), "--cwd", str(fixture), "--agent", state["agent"],
                                "--project", "t073-fixture", "--task", "T-073-1", "--attempt", "fixture-"+args.label,
                                "--session", "fixture-session-"+args.label, "--codex-home", state["codex_home"]]))
        state.update(pane=result["pane"], launch_id=result["launch_id"])
        (directory / "state.json").write_text(json.dumps(state, indent=2)+"\n", encoding="utf-8")
    elif args.action == "prompt":
        run([str(ROOT / "scripts/dispatch"), "--batch", "2026-10-10-batch12",
             "--agent", state["agent"], "--role", "worker", "--body-file", str(directory / "prompt.txt")])
    elif args.action == "inspect":
        run(["herdr", "agent", "get", state["agent"]])
        run(["herdr", "agent", "read", state["agent"], "--source", "visible", "--lines", "40"])
    elif args.action == "collect":
        fixture = Path(state["fixture"])
        rows = [json.loads(line) for line in (ROOT / "records/launches.jsonl").read_text(encoding="utf-8").splitlines()
                if json.loads(line)["launch_id"] == state["launch_id"]]
        (directory / "launch-records.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False)+"\n" for r in rows), encoding="utf-8")
        (directory / "env-probe.json").write_bytes((fixture / "env-probe.json").read_bytes())
        expected = {"A2A-Task": "T-073-1", "A2A-Attempt": "fixture-"+args.label,
                    "A2A-Session": "fixture-session-"+args.label, "A2A-Role": "worker",
                    "A2A-Tool": "codex-cli 0.162.1", "A2A-Model": "gpt-6.1-sol", "A2A-Effort": "xhigh",
                    "A2A-Native-Session": json.loads((fixture / "env-probe.json").read_text())["CODEX_THREAD_ID"],
                    "A2A-Launch": state["launch_id"]}
        for rev, name in (("HEAD~1", "normal"), ("HEAD", "no-verify")):
            text = run(["git", "-C", str(fixture), "log", "-1", rev, "--format=%B"])
            (directory / (name+"-message.txt")).write_text(text, encoding="utf-8")
            actual = [line for line in text.splitlines() if line.startswith("A2A-")]
            assert len(actual) == 9, actual
            assert dict(line.split(": ", 1) for line in actual) == expected
        assert rows[-1]["native_session"] == expected["A2A-Native-Session"]
        for field, trailer in (("task","A2A-Task"),("attempt","A2A-Attempt"),("session","A2A-Session"),
                               ("role","A2A-Role"),("cli_version","A2A-Tool"),("model","A2A-Model"),
                               ("effort","A2A-Effort"),("launch_id","A2A-Launch")):
            assert rows[-1][field] == expected[trailer]
        trace = (fixture / "original-hook-trace.txt").read_text(encoding="utf-8")
        (directory / "original-hook-trace.txt").write_text(trace, encoding="utf-8")
        assert trace.splitlines() == ["original-prepare", "original-prepare"]
        # The controller-specified exact count command, with pipefail to preserve errors.
        command = "set -o pipefail; git -C " + shlex.quote(str(fixture)) + " log -1 --format=%B | grep -E '^A2A-(Task|Attempt|Session|Role|Tool|Model|Effort|Native-Session|Launch):' | wc -l"
        count = subprocess.run(["/bin/zsh", "-c", command], text=True, capture_output=True)
        with (directory / "commands.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps(dict(argv=count.args, exit_code=count.returncode, stdout=count.stdout, stderr=count.stderr))+"\n")
        assert count.returncode == 0 and count.stdout.strip() == "9"
        (directory / "completion-count.txt").write_text(count.stdout, encoding="utf-8")
        import tarfile
        with tarfile.open(directory / "fixture.tar.gz", "w:gz") as archive:
            archive.add(fixture, arcname="fixture")
        (directory / "verification.json").write_text(json.dumps(dict(status="PASS", normal_trailers=9,
            no_verify_trailers=9, original_hook_calls=2, launch_id=state["launch_id"]), indent=2)+"\n", encoding="utf-8")
        print("real Codex verification PASS")
    elif args.action == "plain":
        env = {k:v for k,v in os.environ.items() if not k.startswith(("A2A_", "GIT_CONFIG_"))}
        env.update(GIT_AUTHOR_NAME="plain fixture", GIT_AUTHOR_EMAIL="plain@example.invalid",
                   GIT_COMMITTER_NAME="plain fixture", GIT_COMMITTER_EMAIL="plain@example.invalid")
        argv = ["git", "-C", state["fixture"], "commit", "--allow-empty", "-m", "plain terminal counterexample"]
        result = subprocess.run(argv, env=env, capture_output=True, text=True)
        with (directory / "commands.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps(dict(argv=argv, exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr))+"\n")
        assert result.returncode == 0, result.stderr
        message = run(["git", "-C", state["fixture"], "log", "-1", "--format=%B"])
        (directory / "plain-message.txt").write_text(message, encoding="utf-8")
        assert not any(line.startswith("A2A-") for line in message.splitlines())
        print("plain terminal counterexample PASS")
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
            usage = []
            for rollout in sessions.rglob("*.jsonl"):
                events = [json.loads(line) for line in rollout.read_text(encoding="utf-8").splitlines()]
                meta = [e["payload"] for e in events if e.get("type") == "session_meta"]
                counts = [e["payload"]["info"] for e in events if e.get("type") == "event_msg"
                          and e.get("payload", {}).get("type") == "token_count" and e["payload"].get("info")]
                turns = [e["payload"] for e in events if e.get("type") == "event_msg"
                         and e.get("payload", {}).get("type") in ("task_started", "task_complete")]
                usage.append(dict(native_session=meta[0].get("id") if meta else None,
                                  cli_version=meta[0].get("cli_version") if meta else None,
                                  turn_events=turns, usage=counts[-1] if counts else None))
            (directory / "usage.json").write_text(json.dumps(usage, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        run(["herdr", "pane", "close", state["pane"]])
        shutil.rmtree(home)
        with (directory / "commands.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps(dict(cleaned_codex_home=str(home), exists=home.exists()))+"\n")


if __name__ == "__main__":
    main()
