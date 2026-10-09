"""Independent T-048 oracle: execute the real launcher's record writer under
different locales, without Electron, then read through workbench status.
T-046's synthetic legacy records now test refusal of noncanonical identities:
the controller stops with old code before integrating T-048 and restarting.
Expected answers come from T-048, not from production identity helpers.

Usage: python3 workbench_identity_oracle.py CANDIDATE_ROOT
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import signal
import time

LOCALES = ["zh_CN.UTF-8", "en_US.UTF-8", "C", "zh_CN.GB2312"]
ENVIRONMENTS = [{"LC_ALL": name, "LANG": name} for name in LOCALES] + [
    {"LANG": "zh_CN.UTF-8", "LC_TIME": "zh_CN.UTF-8", "LC_CTYPE": "en_US.UTF-8"},
    {"LANG": "en_US.UTF-8", "LC_TIME": "C", "LC_CTYPE": "zh_CN.UTF-8"},
]


def locale_environment(settings):
    env = {k: v for k, v in os.environ.items() if not k.startswith("LC_")}
    return {**env, **settings}


def ps_identity(pid, locale):
    env = locale_environment({"LC_ALL": locale, "LANG": locale})
    out = subprocess.run(["ps", "-p", str(pid), "-o", "lstart=", "-o", "command="],
                         capture_output=True, encoding="utf-8", errors="replace", check=True, env=env)
    return out.stdout.strip()


def status(root, data, settings):
    env = locale_environment(settings)
    env.update(A2A_WORKBENCH_DATA_DIR=str(data))
    p = subprocess.run([sys.executable, "-B", str(root / "a2a/scripts/workbench"), "status"],
                       capture_output=True, encoding="utf-8", errors="replace", env=env, timeout=30)
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
    child = subprocess.Popen(["/bin/sleep", "600"], start_new_session=True)
    try:
        with tempfile.TemporaryDirectory(prefix="t048-oracle-") as tmp:
            data = Path(tmp)
            # Substitute only executable resolution. The launcher's spawn, ps,
            # JSON write, file permissions and status reader remain production code.
            preload = data / "electron-substitute.cjs"
            preload.write_text(
                'const Module = require("node:module");\n'
                'const original = Module._load;\n'
                'Module._load = function(request, ...args) {\n'
                '  if (request === "electron") return process.env.T048_EXECUTABLE;\n'
                '  return original.call(this, request, ...args);\n'
                '};\n', encoding="utf-8")
            executable = data / "受控进程.sh"
            executable.write_text("#!/bin/sh\nwhile :; do /bin/sleep 1; done\n", encoding="utf-8")
            executable.chmod(0o700)
            for written in ENVIRONMENTS:
                record = data / "workbench-process.json"
                record.unlink(missing_ok=True)
                env = locale_environment(written)
                env.update(A2A_WORKBENCH_DATA_DIR=str(data), T048_EXECUTABLE=str(executable),
                           A2A_SYNARA_SLOT="t048")
                writer = subprocess.Popen(
                    [str(root / "a2a/scripts/bun"), "run", "node", "--require", str(preload),
                     str(root / "a2a/scripts/launch-workbench.mjs")],
                    cwd=root, env=env, start_new_session=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                owner = None
                try:
                    deadline = time.monotonic() + 15
                    while not record.exists() and time.monotonic() < deadline and writer.poll() is None:
                        time.sleep(0.05)
                    if record.exists():
                        owner = json.loads(record.read_text(encoding="utf-8"))
                        canonical = ps_identity(owner["pid"], "C")
                        results.append({"case": f"writer-canonical {written}",
                                        "expected": canonical, "actual": owner,
                                        "pass": owner["identity"] == canonical and
                                        record.stat().st_mode & 0o777 == 0o600})
                        for reading in ENVIRONMENTS:
                            r = status(root, data, reading)
                            ok = (r["exit"] == 0 and isinstance(r["json"], dict)
                                  and r["json"].get("running") is True
                                  and r["json"].get("pid") == owner["pid"])
                            results.append({"case": f"writer-reader written={written} read={reading}",
                                            "expected": {"running": True, "pid": owner["pid"]},
                                            "actual": r, "pass": ok})
                    else:
                        results.append({"case": f"writer-record {written}",
                                        "expected": "record within 15 seconds", "pass": False})
                finally:
                    if owner:
                        os.killpg(owner["pid"], signal.SIGTERM)
                    else:
                        # If setup failed, do not leave this oracle's launcher alive.
                        os.killpg(writer.pid, signal.SIGTERM)
                    try:
                        _, stderr = writer.communicate(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(writer.pid, signal.SIGKILL)
                        _, stderr = writer.communicate(timeout=5)
                    results.append({"case": f"writer-exit {written}",
                                    "exit": writer.returncode,
                                    "stderr": stderr.decode("utf-8", errors="replace"),
                                    "pass": writer.returncode == 0})
            # Noncanonical legacy records are deliberately refused after T-048;
            # English records identical to C are already canonical and stay valid.
            legacy = ps_identity(child.pid, "zh_CN.UTF-8")
            write_record(data, child.pid, legacy)
            for reading in ENVIRONMENTS:
                r = status(root, data, reading)
                results.append({"case": f"legacy-noncanonical read={reading}",
                                "expected": "non-zero exit, not running", "actual": r,
                                "pass": legacy != ps_identity(child.pid, "C") and r["exit"] != 0
                                and not (r["json"] and r["json"].get("running") is True)})
            # A record naming the live PID but another process must be refused, not accepted.
            write_record(data, child.pid, "Thu Jan  1 00:00:00 1970     /bin/not-the-workbench")
            for reading in ENVIRONMENTS:
                r = status(root, data, reading)
                ok = r["exit"] != 0 and not (isinstance(r["json"], dict) and r["json"].get("running") is True)
                results.append({"case": f"foreign-identity read={reading}",
                                "expected": "non-zero exit, not running", "actual": r, "pass": ok})
            # A record whose PID no longer exists means not running.
            dead = subprocess.Popen(["/usr/bin/true"], start_new_session=True)
            dead.wait()
            write_record(data, dead.pid, "irrelevant")
            r = status(root, data, {"LC_ALL": "en_US.UTF-8", "LANG": "en_US.UTF-8"})
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
