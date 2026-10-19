#!/usr/bin/env python3
"""由主控在沙箱外运行，只读查本票合成 PTY 夹具；不终止进程。"""
import json
import re
import subprocess
import sys
from pathlib import PurePosixPath


def fixture_processes(snapshot):
    # 只认本票生成的临时夹具可执行路径，不按 Python/Claude 进程名匹配。
    fixture = re.compile(r"/[^\s]*/t093-route-(?:peer|exit)-[^/\s]+/(?:interactive-peer|exit-peer)")
    result = []
    for line in snapshot.splitlines():
        fields = line.split(None, 3)
        if len(fields) != 4:
            continue
        argv = fields[3].split(None, 2)
        candidate = argv[0]
        if re.fullmatch(r"python(?:[0-9]+(?:\.[0-9]+)*)?", PurePosixPath(candidate).name, re.IGNORECASE):
            candidate = argv[1] if len(argv) > 1 else ""
        if not fixture.fullmatch(candidate):
            continue
        pid, pgid, state, _ = fields
        if pid.isdigit() and pgid.isdigit() and re.fullmatch(r"[A-Za-z+<>-]{1,8}", state):
            result.append({"pid": int(pid), "pgid": int(pgid), "state": state})
    return result


def main():
    # 完整进程参数只在内存中用于筛选；不打印、写盘或传给日志。
    try:
        completed = subprocess.run(["/bin/ps", "-ww", "-A", "-o", "pid=,pgid=,stat=,args="],
                                   capture_output=True, text=True, timeout=5, check=True)
    except (OSError, subprocess.SubprocessError):
        return 2
    print(json.dumps(fixture_processes(completed.stdout)))
    return 0


def self_test():
    snapshot = "\n".join([
        "101 101 S /usr/bin/python3 /private/tmp/t093-route-peer-canary/interactive-peer --model synthetic",
        "202 202 Z /var/folders/a/t093-route-exit-canary/exit-peer",
        "303 303 S /usr/bin/python3 -c /private/tmp/t093-route-peer-not-a-program/interactive-peer credential-canary",
        "404 404 S /bin/grep /private/tmp/t093-route-peer-not-a-program/interactive-peer",
        "505 505 S /usr/bin/python3 /some/user-program.py credential-canary"])
    expected = [{"pid": 101, "pgid": 101, "state": "S"}, {"pid": 202, "pgid": 202, "state": "Z"}]
    passed = fixture_processes(snapshot) == expected
    print(json.dumps({"status": "PASS" if passed else "INCOMPLETE", "scope": "synthetic parser only", "ps_executed": False}))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(self_test() if sys.argv[1:] == ["--self-test"] else main() if not sys.argv[1:] else 2)
