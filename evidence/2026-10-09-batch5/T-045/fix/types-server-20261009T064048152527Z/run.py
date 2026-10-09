"""Run bounded offline checks and preserve each run without overwriting evidence."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess


parser = argparse.ArgumentParser()
parser.add_argument("action", choices=["offline-red", "baseline", "boundary", "format", "lint", "counterfactual", "mutant", "shared", "format-write", "types-shared", "types-server"])
parser.add_argument("--fork", type=Path, default=Path.home() / "Documents/Code/synara-t045")
parser.add_argument("--bad-revision", default="28e2f1b4ca6634d4faba9bd921a55a51640407e4")
args = parser.parse_args()
repo = args.fork.resolve()
evidence = Path(__file__).resolve().parent
run = evidence / (args.action + "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
run.mkdir()
env = {**os.environ, "T045_SYNARA_ROOT": str(repo), "A2A_SYNARA_SLOT": "t045"}
if args.action in ["offline-red", "counterfactual"]:
    command = [str(repo / "a2a/scripts/bun"), "run", "node",
               str(repo / "node_modules/vitest/vitest.mjs"), "run",
               "--config", str(evidence / "offline.config.mjs"), "--reporter=verbose"]
elif args.action in ["boundary", "mutant"]:
    command = [str(repo / "a2a/scripts/bun"), "run", "--cwd", "apps/server", "test", "src/providerUsage/httpProxyFakeIp.test.ts"]
elif args.action in ["types-shared", "types-server"]:
    command = [str(repo / "a2a/scripts/bun"), "run", "--cwd", "packages/shared" if args.action == "types-shared" else "apps/server", "typecheck"]
elif args.action == "shared":
    command = [str(repo / "a2a/scripts/bun"), "run", "--cwd", "packages/shared", "test", "src/outboundHttpPolicy.test.ts"]
elif args.action in ["format", "lint", "format-write"]:
    command = [str(repo / "a2a/scripts/bun"), "run", "node", str(repo / "node_modules" / ("oxlint/bin/oxlint" if args.action == "lint" else "oxfmt/bin/oxfmt")),
               *(["--check"] if args.action == "format" else []),
               "packages/shared/src/outboundHttp.ts", "apps/server/src/providerUsage/http.ts", "apps/server/src/providerUsage/httpProxyFakeIp.test.ts"]
else:
    command = [str(repo / "a2a/scripts/bun"), "run", "--cwd", "apps/server", "test",
               "src/providerUsage/providers/codex.test.ts",
               "src/providerUsage/providers/claude.test.ts",
               "src/providerUsage/providers/cursor.test.ts",
               "src/providerUsage/parsers.test.ts",
               "src/providerUsage/http.test.ts",
               "src/providerUsage/rateLimitResilience.test.ts"]

record = {"action": args.action, "known_bad_revision": args.bad_revision if args.action == "counterfactual" else None, "cwd": str(repo), "argv": command,
          "environment_overrides": {key: env[key] for key in ["T045_SYNARA_ROOT", "A2A_SYNARA_SLOT", "T045_POLICY_MUTANT"] if key in env},
          "started_at": datetime.now(timezone.utc).isoformat(),
          "fork_worktree_status": subprocess.check_output(["git", "status", "--short"], cwd=repo, text=True),
          "fork_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()}
(run / "command.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(str(run), flush=True)
# Preserve the candidate and fixture for reproducible checks, including the known-bad parent.
(run / "candidate.patch").write_text(subprocess.check_output(["git", "diff", "HEAD"], cwd=repo, text=True), encoding="utf-8")
for name in ["offline-usage.test.ts", "offline.config.mjs", "run.py"]:
    (run / name).write_bytes((evidence / name).read_bytes())
(run / "httpProxyFakeIp.test.ts").write_bytes((repo / "apps/server/src/providerUsage/httpProxyFakeIp.test.ts").read_bytes())
originals = {}
if args.action == "counterfactual":
    for name in ["apps/server/src/providerUsage/http.ts", "packages/shared/src/outboundHttp.ts"]:
        path = repo / name
        originals[path] = path.read_bytes()
        path.write_bytes(subprocess.check_output(["git", "show", f"{args.bad_revision}:{name}"], cwd=repo))
if args.action == "mutant":
    path = repo / "packages/shared/src/outboundHttp.ts"
    originals[path] = path.read_bytes()
    source = path.read_text(encoding="utf-8")
    assert "providerUsageProxyOrigins.has(url.origin) &&" in source
    path.write_text(source.replace("providerUsageProxyOrigins.has(url.origin) &&", ""), encoding="utf-8")
try:
  with (run / "output.log").open("x", encoding="utf-8") as output:
    completed = subprocess.run(command, cwd=repo, env=env, stdout=output, stderr=subprocess.STDOUT,
                               start_new_session=True)
finally:
    for path, content in originals.items():
        path.write_bytes(content)
record.update({"finished_at": datetime.now(timezone.utc).isoformat(), "exit_code": completed.returncode})
(run / "result.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"exit_code": completed.returncode, "output": str(run / "output.log")}))
raise SystemExit(completed.returncode)
