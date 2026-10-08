#!/usr/bin/env python3
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
action, label = sys.argv[1:3]
record = root / (label + ".json")
if action == "start":
    variant = sys.argv[3]
    assert variant in ("baseline", "candidate")
    assert not record.exists() and not (root / (label + ".log")).exists()
    cwd = "/Users/luckye/Documents/Code/" + ("synara-t038-baseline" if variant == "baseline" else "synara-t038")
    argv = ["./a2a/scripts/bun", "run", "dev:web"]
    env = os.environ.copy()
    env["A2A_SYNARA_SLOT"] = "t038-baseline" if variant == "baseline" else "t038"
    env["SYNARA_PORT_OFFSET"] = "2038"
    with (root / (label + ".log")).open("x", encoding="utf-8") as stream:
        p = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL, start_new_session=True)
    record.write_text(json.dumps({"argv": argv, "cwd": cwd, "variant": variant, "slot": env["A2A_SYNARA_SLOT"],
                                 "pid": p.pid, "pgid": p.pid, "started": time.time()}, indent=2) + "\n", encoding="utf-8")
elif action == "stop":
    d = json.loads(record.read_text(encoding="utf-8"))
    assert d["cwd"] in ("/Users/luckye/Documents/Code/synara-t038-baseline", "/Users/luckye/Documents/Code/synara-t038")
    observed = subprocess.check_output(["ps", "-p", str(d["pid"]), "-o", "pgid=,command="], text=True)
    assert int(observed.split()[0]) == d["pgid"] and "bun run dev:web" in observed
    target = root / (label + "-stop.json"); assert not target.exists()
    os.killpg(d["pgid"], signal.SIGTERM)
    target.write_text(json.dumps({"source": str(record), "observed": observed, "signal": "SIGTERM"}, indent=2) + "\n", encoding="utf-8")
else:
    raise SystemExit("Expected start or stop")
print(label, action)
