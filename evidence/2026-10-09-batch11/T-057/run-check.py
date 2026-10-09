import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys

out = Path(__file__).resolve().parent
label, *args = sys.argv[1:]
argv = ["./a2a/scripts/bun", *args]
env = {**os.environ, "A2A_SYNARA_SLOT": "t057-checks"}
record = {"argv": argv, "cwd": "/Users/luckye/Documents/Code/synara",
          "started_at": dt.datetime.now(dt.timezone.utc).isoformat()}
with (out / (label + ".log")).open("x", encoding="utf-8") as log:
    result = subprocess.run(argv, cwd=record["cwd"], env=env, stdout=log, stderr=subprocess.STDOUT)
record.update(exit=result.returncode, ended_at=dt.datetime.now(dt.timezone.utc).isoformat())
with (out / (label + ".command.json")).open("x", encoding="utf-8") as file:
    json.dump(record, file, ensure_ascii=False, indent=2)
    file.write("\n")
print(label, result.returncode)
sys.exit(result.returncode)
