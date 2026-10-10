#!/usr/bin/env python3
"""Session Git hooks: add provenance, then run the repository's original hook."""
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from launch_records import find_launch
from record_io import append_record, locked, read_records, utc_now


def trailers():
    logfile = Path(os.environ["A2A_LAUNCHES"])
    if not logfile.is_absolute():
        raise ValueError("启动记录路径必须为绝对路径")
    with locked(logfile.parent / ".launches.lock"):
        row = find_launch(read_records(logfile), os.environ["A2A_LAUNCH"])
        for key in ("project", "task", "attempt", "session", "role"):
            if os.environ["A2A_" + key.upper()] != row[key]:
                raise ValueError("会话环境与启动记录不符：" + key)
        native = os.environ["CODEX_THREAD_ID"]
        if not native or "\n" in native:
            raise ValueError("原生会话身份为空或损坏")
        if row["native_session"] != "unknown" and row["native_session"] != native:
            raise ValueError("原生会话已被替换；需要新启动记录")
        if row["native_session"] == "unknown":
            row = dict(row, phase="native-session", native_session=native, observed_at=utc_now())
            append_record(logfile, row)
    return {"A2A-Task": row["task"], "A2A-Attempt": row["attempt"], "A2A-Session": row["session"],
            "A2A-Role": row["role"], "A2A-Tool": row["cli_version"],
            "A2A-Model": row["model"], "A2A-Effort": row["effort"],
            "A2A-Native-Session": native, "A2A-Launch": row["launch_id"]}


def main():
    name = Path(sys.argv[0]).name
    if name == "prepare-commit-msg":
        values = trailers()
        message = Path(sys.argv[1])
        # Git owns trailer parsing and replacement, including amend/rebase messages.
        argv = ["git", "-c", "trailer.ifexists=replace", "-c", "trailer.ifmissing=add",
                "interpret-trailers", "--in-place"]
        for key, value in values.items():
            argv.extend(["--trailer", key + ": " + value])
        argv.append(str(message))
        subprocess.run(argv, check=True)
    # Removing our process-only override reveals each current repository's own
    # hooksPath (or .git/hooks). Other Git config channels remain intact.
    env = dict(os.environ)
    if env.get("GIT_CONFIG_COUNT") != "1" or env.get("GIT_CONFIG_KEY_0") != "core.hooksPath":
        raise ValueError("会话 Git 配置已改变")
    for key in ("GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0"):
        env.pop(key, None)
    original = Path(subprocess.check_output(["git", "rev-parse", "--git-path", "hooks/" + name],
                                           env=env, text=True).strip())
    if original.resolve() == Path(sys.argv[0]).resolve():
        raise ValueError("项目原钩子指回 a2a 钩子目录")
    if original.is_file() and os.access(original, os.X_OK):
        result = subprocess.run([str(original.resolve()), *sys.argv[1:]], env=os.environ)
        return 128 - result.returncode if result.returncode < 0 else result.returncode
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print("a2a Git 钩子拒绝：" + str(exc), file=sys.stderr)
        sys.exit(1)
