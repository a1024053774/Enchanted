#!/usr/bin/env python3
"""从真实 CLI、Git 与已保存的原生观察核对 T-035；不 import 产品。"""
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
runtime = json.loads((HERE / "runtime.json").read_text(encoding="utf-8"))
endpoint = sys.argv[1] if len(sys.argv) > 1 else runtime["endpoint"]
checks = []
commands = []

def call(task):
    argv = ["./a2a/scripts/bun", "run", "packages/a2a-gates/src/cli.ts", endpoint, json.dumps({"command": "status", "task": task})]
    env = dict(os.environ, A2A_SYNARA_SLOT="t035", A2A_GATE_BEARER=Path(runtime["root"], "bootstrap-token").read_text(encoding="utf-8"))
    p = subprocess.run(argv, cwd="/Users/luckye/Documents/Code/synara", env=env, capture_output=True, text=True, timeout=20)
    commands.append({"argv": argv, "stdout": p.stdout, "stderr": p.stderr, "exit": p.returncode})
    return json.loads(p.stdout)

def check(name, condition):
    checks.append({"case": name, "pass": bool(condition)})

primary = call("pagination")
check("explicitly-delivered-task-accepted-and-reclaimed", primary.get("ok") and primary["task"]["state"] == "accepted" and primary["task"]["current_attempt"]["reclaimed"])
negative = call("no-submit")
check("completed-without-delivery-not-accepted", negative.get("ok") and negative["task"]["state"] != "accepted" and negative["task"]["candidate_commit"] is None and negative["task"]["verification"] is None)
for file, expected in [("status-4.json", "submitted"), ("verify-2.json", "verified"), ("integrate-2.json", "accepted"), ("no-submit-status-1.json", "claimed")]:
    record = json.loads((HERE / file).read_text(encoding="utf-8"))
    check(file, json.loads(record["stdout"])["task"]["state"] == expected)
for file, expected in [("no-submit-verify-idle.json", "not_submitted"), ("no-submit-integrate-idle.json", "not_verified")]:
    record = json.loads((HERE / file).read_text(encoding="utf-8"))
    check(file, record["exit"] == 1 and json.loads(record["stdout"])["error"] == expected)
idle = json.loads(json.loads((HERE / "no-submit-native-idle.json").read_text())["result"]["content"][0]["text"])
check("native-turn-completed-and-idle", idle["latestTurnState"] == "completed" and idle["status"] == "idle")
archived = json.loads(json.loads((HERE / "primary-native-archived.json").read_text())["result"]["content"][0]["text"])
check("native-worker-stopped-and-archived", archived["archived"] and archived["sessionStatus"] == "stopped")
verification = primary["task"]["verification"]
oracle = json.loads(verification["result"]["stdout"])
check("independent-oracle-twelve-cases", oracle["status"] == "PASS" and len(oracle["cases"]) == 12 and all(case["pass"] for case in oracle["cases"]))
check("detached-verification-not-worker-worktree", verification["workspace"] != primary["task"]["current_attempt"]["workspace"])
frozen = Path(verification["oracle"])
original = HERE.parents[2] / "acceptance" / "pagination_oracle.py"
check("oracle-snapshot-byte-identical", frozen.read_bytes() == original.read_bytes())
p = subprocess.run(["git", "-C", runtime["repo"], "rev-parse", "refs/a2a/integration"], capture_output=True, text=True)
commands.append({"argv": p.args, "stdout": p.stdout, "stderr": p.stderr, "exit": p.returncode})
check("authoritative-integration-ref-is-verified-commit", p.returncode == 0 and p.stdout.strip() == verification["M"])
known_bad = json.loads((HERE / "oracle-known-bad.json").read_text())
check("frozen-oracle-rejects-starter", known_bad["status"] == "FAIL" and any(not case["pass"] for case in known_bad["cases"]))
print(json.dumps({"status": "PASS" if all(c["pass"] for c in checks) else "FAIL", "checks": checks, "commands": commands}, ensure_ascii=False, indent=2))
sys.exit(0 if all(c["pass"] for c in checks) else 1)
