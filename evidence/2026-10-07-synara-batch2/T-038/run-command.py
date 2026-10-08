#!/usr/bin/env python3
"""Save each local check to a new evidence pair; never replace an earlier run."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
label, *argv = sys.argv[1:]
record = root / (label + ".json")
log = root / (label + ".log")
if record.exists() or log.exists():
    raise SystemExit("Evidence label already exists")
cwd = Path("/Users/luckye/Documents/Code/synara-t038")
env = os.environ.copy()
env["A2A_SYNARA_SLOT"] = "t038"
before = subprocess.check_output(["du", "-sk", str(cwd)], text=True).strip()
started = time.time()
with log.open("x", encoding="utf-8") as stream:
    child = subprocess.run(argv, cwd=cwd, env=env, stdout=stream,
                           stderr=subprocess.STDOUT, start_new_session=True)
after = subprocess.check_output(["du", "-sk", str(cwd)], text=True).strip()
record.write_text(json.dumps({"argv": argv, "cwd": str(cwd),
    "slot": "t038", "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cwd, text=True).strip(),
    "tracked_diff_after": subprocess.check_output(["git", "diff", "--stat", "HEAD"], cwd=cwd, text=True), "started": started, "seconds": time.time() - started,
    "exit": child.returncode, "checkout_kib_before": before,
    "checkout_kib_after": after}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(record.read_text(encoding="utf-8"))
raise SystemExit(child.returncode)
