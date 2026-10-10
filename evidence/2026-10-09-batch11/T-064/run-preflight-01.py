"""Save the expected-red navigation contract without changing product code."""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys

evidence = Path(__file__).resolve().parent
fork = Path("/Users/luckye/Documents/Code/synara")
label = sys.argv[1]
if not label or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in label):
    raise ValueError("Use a new lowercase evidence label")
destination = evidence / ("navigation-" + label + ".json")
if destination.exists():
    raise FileExistsError(destination)
argv = ["./a2a/scripts/bun", "run", str(evidence / "settings-navigation-probe-01.ts")]
env = {k: v for k, v in os.environ.items() if k in ("PATH", "SHELL", "LANG", "LC_ALL")}
env["A2A_SYNARA_SLOT"] = "s11-t064-preflight"
revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=fork, text=True).strip()
result = subprocess.run(argv, cwd=fork, env=env, capture_output=True, text=True, timeout=55)
record = {
    "argv": argv,
    "cwd": str(fork),
    "env_override": {"A2A_SYNARA_SLOT": "s11-t064-preflight"},
    "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    "fork_revision": revision,
    "fork_status": subprocess.check_output(["git", "status", "--short"], cwd=fork, text=True),
    "expected": "Navigation contains the role permissions page specified by T-064",
    "returncode": result.returncode,
    "stdout": result.stdout,
    "stderr": result.stderr,
}
with destination.open("x", encoding="utf-8") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps(record, ensure_ascii=False, indent=2))
raise SystemExit(result.returncode)
