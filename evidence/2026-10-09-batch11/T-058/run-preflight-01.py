"""Preserve one credential/catalog probe without starting a service or provider."""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess

evidence = Path(__file__).resolve().parent
fork = Path("/Users/luckye/Documents/Code/synara")
argv = ["./a2a/scripts/bun", str(evidence / "capability-preflight-01.ts")]
env = os.environ.copy()
env["A2A_SYNARA_SLOT"] = "s11-t058-preflight"
result = subprocess.run(argv, cwd=fork, env=env, capture_output=True, text=True)
record = {
    "argv": argv,
    "cwd": str(fork),
    "env_override": {"A2A_SYNARA_SLOT": "s11-t058-preflight"},
    "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    "fork_revision": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=fork, text=True).strip(),
    "fork_status": subprocess.check_output(
        ["git", "status", "--short"], cwd=fork, text=True),
    "returncode": result.returncode,
    "stdout": result.stdout,
    "stderr": result.stderr,
}
with (evidence / "capability-preflight-01.json").open("x", encoding="utf-8") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps(record, ensure_ascii=False, indent=2))
