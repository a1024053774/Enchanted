"""Independent oracle for T-046: the workbench launcher must recognise its own process
regardless of the caller's locale, and must still refuse a record that names another
process. Expected answers come from the T-046 ticket, not from the implementation.

Usage: python3 workbench_identity_oracle.py CANDIDATE_ROOT
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

LOCALES = ["zh_CN.UTF-8", "en_US.UTF-8", "C"]


def ps_identity(pid, locale):
    # The record format written by the launcher before T-046: `ps lstart` + command.
    env = dict(os.environ, LC_ALL=locale, LANG=locale)
    out = subprocess.run(["ps", "-p", str(pid), "-o", "lstart=", "-o", "command="],
                         capture_output=True, text=True, check=True, env=env)
    return out.stdout.strip()


def status(root, data, locale):
    env = {k: v for k, v in os.environ.items() if not k.startswith("LC_")}
    env.update(LC_ALL=locale, LANG=locale, A2A_WORKBENCH_DATA_DIR=str(data))
    p = subprocess.run([sys.executable, "-B", str(root / "a2a/scripts/workbench"), "status"],
                       capture_output=True, text=True, env=env, timeout=30)
    try:
        parsed = json.loads(p.stdout)
    except json.JSONDecodeError:
        parsed = None
    return {"exit": p.returncode, "stdout": p.stdout, "stderr": p.stderr, "json": parsed}


def write_record(data, pid, identity):
    record = {"pid": pid, "identity": identity, "executable": "/bin/sleep", "args": ["600"]}
    (data / "workbench-process.json").write_text(json.dumps(record), encoding="utf-8")


def main():
    root = Path(sys.argv[1]).resolve()
    results = []
    child = subprocess.Popen(["/bin/sleep", "600"])
    try:
        with tempfile.TemporaryDirectory(prefix="t046-oracle-") as tmp:
            data = Path(tmp)
            # Records written under each locale must be recognised under every locale.
            for written in LOCALES:
                write_record(data, child.pid, ps_identity(child.pid, written))
                for reading in LOCALES:
                    r = status(root, data, reading)
                    ok = (r["exit"] == 0 and isinstance(r["json"], dict)
                          and r["json"].get("running") is True and r["json"].get("pid") == child.pid)
                    results.append({"case": f"own-process written={written} read={reading}",
                                    "expected": {"running": True, "pid": child.pid}, "actual": r, "pass": ok})
            # A record naming the live PID but another process must be refused, not accepted.
            write_record(data, child.pid, "Thu Jan  1 00:00:00 1970     /bin/not-the-workbench")
            for reading in LOCALES:
                r = status(root, data, reading)
                ok = r["exit"] != 0 and not (isinstance(r["json"], dict) and r["json"].get("running") is True)
                results.append({"case": f"foreign-identity read={reading}",
                                "expected": "non-zero exit, not running", "actual": r, "pass": ok})
            # A record whose PID no longer exists means not running.
            dead = subprocess.Popen(["/usr/bin/true"])
            dead.wait()
            write_record(data, dead.pid, "irrelevant")
            r = status(root, data, "en_US.UTF-8")
            ok = r["exit"] == 0 and isinstance(r["json"], dict) and r["json"].get("running") is False
            results.append({"case": "dead-pid", "expected": {"running": False}, "actual": r, "pass": ok})
    finally:
        child.kill()
        child.wait()
    passed = all(r["pass"] for r in results)
    print(json.dumps({"status": "PASS" if passed else "FAIL", "candidate": str(root),
                      "cases": results}, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
