"""Save a new command record and its unmodified output; never reuse a label."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

out = Path(__file__).resolve().parent
label, *argv = sys.argv[1:]
record = {"argv": argv, "cwd": "/Users/luckye/Documents/Code/synara",
          "start": datetime.datetime.now(datetime.timezone.utc).isoformat()}
env = os.environ.copy()
env["A2A_SYNARA_SLOT"] = "t062-rev2-checks"
with (out / (label + ".log")).open("x", encoding="utf-8") as log:
    result = subprocess.run(argv, cwd=record["cwd"], env=env, stdout=log,
                            stderr=subprocess.STDOUT)
record.update(exit=result.returncode, end=datetime.datetime.now(datetime.timezone.utc).isoformat())
with (out / (label + "-command.json")).open("x", encoding="utf-8") as file:
    json.dump(record, file, ensure_ascii=False, indent=2)
    file.write("\n")
print(json.dumps(record, ensure_ascii=False))
raise SystemExit(result.returncode)
