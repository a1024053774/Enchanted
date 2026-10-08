#!/usr/bin/env python3
"""Launch only the isolated T-038 runner in its own process group."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
label = sys.argv[1]
record = root / (label + ".json")
log = root / (label + ".log")
if record.exists() or log.exists():
    raise SystemExit("Evidence label already exists")
mode = sys.argv[2] if len(sys.argv) > 2 else "dev"
assert mode in ("dev", "dev:web")
argv = ["./a2a/scripts/bun", "run", mode]
env = os.environ.copy()
env["A2A_SYNARA_SLOT"] = "t038"
env["SYNARA_PORT_OFFSET"] = "2038"
cwd = "/Users/luckye/Documents/Code/synara-t038"
with log.open("x", encoding="utf-8") as stream:
    child = subprocess.Popen(argv, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT,
                             stdin=subprocess.DEVNULL, start_new_session=True)
record.write_text(json.dumps({"argv": argv, "cwd": cwd, "pid": child.pid, "pgid": child.pid,
    "slot": "t038", "port_offset": 2038, "started": time.time()}, indent=2) + "\n", encoding="utf-8")
print(record.read_text(encoding="utf-8"))
