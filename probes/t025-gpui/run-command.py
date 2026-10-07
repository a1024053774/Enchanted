"""Keep exact commands, elapsed time, output and exit status in a new directory."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

destination = Path(sys.argv[1])
destination.mkdir(parents=True, exist_ok=False)
command = sys.argv[2:]
started = time.time()
(destination / "command.json").write_text(json.dumps({
    "argv": command, "cwd": os.getcwd(), "started_unix": started,
    "build_slot": os.environ.get("MUSTER_BUILD_SLOT"),
}, indent=2) + "\n", encoding="utf-8")
with (destination / "stdout.txt").open("w", encoding="utf-8") as out, \
     (destination / "stderr.txt").open("w", encoding="utf-8") as err:
    result = subprocess.run(command, stdout=out, stderr=err)
elapsed = time.time() - started
record = {"exit_code": result.returncode, "elapsed_seconds": elapsed}
(destination / "result.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"directory": str(destination), **record}), flush=True)
sys.exit(result.returncode)
