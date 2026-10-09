"""Run bounded offline checks and preserve each run without overwriting evidence."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess


parser = argparse.ArgumentParser()
parser.add_argument("action", choices=["raw-boundary", "raw-mutant", "offline-red", "baseline"])
parser.add_argument("--fork", type=Path, default=Path.home() / "Documents/Code/synara-t045")
args = parser.parse_args()
repo = args.fork.resolve()
evidence = Path(__file__).resolve().parent
run = evidence / (args.action + "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
run.mkdir()
env = {**os.environ, "T045_SYNARA_ROOT": str(repo), "A2A_SYNARA_SLOT": "t045"}
if args.action in ["raw-boundary", "raw-mutant"]:
    if args.action == "raw-mutant":
        env["T045_POLICY_MUTANT"] = "allow-benchmark-subnet"
    command = [str(repo / "a2a/scripts/bun"), "run", "node", str(evidence / "raw-boundary.mjs")]
elif args.action == "offline-red":
    command = [str(repo / "a2a/scripts/bun"), "run", "node",
               str(repo / "node_modules/vitest/vitest.mjs"), "run",
               "--config", str(evidence / "offline.config.mjs"), "--reporter=verbose"]
else:
    command = [str(repo / "a2a/scripts/bun"), "run", "--cwd", "apps/server", "test",
               "src/providerUsage/providers/codex.test.ts",
               "src/providerUsage/providers/claude.test.ts",
               "src/providerUsage/providers/cursor.test.ts",
               "src/providerUsage/parsers.test.ts",
               "src/providerUsage/http.test.ts",
               "src/providerUsage/rateLimitResilience.test.ts"]

record = {"action": args.action, "cwd": str(repo), "argv": command,
          "environment_overrides": {key: env[key] for key in ["T045_SYNARA_ROOT", "A2A_SYNARA_SLOT", "T045_POLICY_MUTANT"] if key in env},
          "started_at": datetime.now(timezone.utc).isoformat(),
          "fork_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()}
(run / "command.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(str(run), flush=True)
with (run / "output.log").open("x", encoding="utf-8") as output:
    completed = subprocess.run(command, cwd=repo, env=env, stdout=output, stderr=subprocess.STDOUT,
                               start_new_session=True)
record.update({"finished_at": datetime.now(timezone.utc).isoformat(), "exit_code": completed.returncode})
(run / "result.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"exit_code": completed.returncode, "output": str(run / "output.log")}))
raise SystemExit(completed.returncode)
