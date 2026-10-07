#!/usr/bin/env python3
"""Save one exact command, its output, timing, and exit status without a shell."""
import datetime
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parent
name, cwd, *argv = sys.argv[1:]
record = {"name": name, "cwd": cwd, "argv": argv,
          "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
with (root / f"{name}.log").open("x", encoding="utf-8") as output:
    start = time.monotonic()
    child = subprocess.Popen(argv, cwd=cwd, stdout=output, stderr=subprocess.STDOUT,
                             start_new_session=True)
    record["pid"] = child.pid
    record["exit_code"] = child.wait()
    record["elapsed_seconds"] = time.monotonic() - start
record["ended_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
with (root / f"{name}.json").open("x", encoding="utf-8") as output:
    json.dump(record, output, indent=2)
    output.write("\n")
with (root / "events.jsonl").open("a", encoding="utf-8") as output:
    output.write(json.dumps(record) + "\n")
print(json.dumps(record))
raise SystemExit(record["exit_code"])
