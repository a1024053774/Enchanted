#!/usr/bin/env python3
"""Stop only a process group created by this directory's start-dev.py."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

root = Path(__file__).resolve().parent
label = sys.argv[1]
source = root / (label + ".json")
target = root / (label + "-stop.json")
assert not target.exists()
start = json.loads(source.read_text(encoding="utf-8"))
assert start["cwd"] == "/Users/luckye/Documents/Code/synara-t038"
pid = start["pid"]
p = subprocess.run(["ps", "-p", str(pid), "-o", "pgid=,command="], text=True, capture_output=True)
assert p.returncode == 0 and int(p.stdout.split()[0]) == start["pgid"]
assert "bun run dev" in p.stdout, p.stdout
os.killpg(start["pgid"], signal.SIGTERM)
target.write_text(json.dumps({"start_record": str(source), "pid": pid, "pgid": start["pgid"],
                             "observed": p.stdout, "signal": "SIGTERM"}, indent=2) + "\n", encoding="utf-8")
print(target)
