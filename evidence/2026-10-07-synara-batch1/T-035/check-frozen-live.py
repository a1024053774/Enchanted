#!/usr/bin/env python3
"""对准确冻结运行的真实 CLI/Git 做独立核对，不 import 产品。"""
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
runtime = json.loads((HERE / "runtime.json").read_text(encoding="utf-8"))
commands = []
checks = []

def check(name, condition):
    checks.append({"case": name, "pass": bool(condition)})

def call(task):
    argv = ["./a2a/scripts/bun", "run", "packages/a2a-gates/src/cli.ts", runtime["endpoint"], json.dumps({"command": "status", "task": task})]
    env = dict(os.environ, A2A_SYNARA_SLOT="t035", A2A_GATE_BEARER=Path(runtime["root"], "bootstrap-token").read_text(encoding="utf-8"))
    p = subprocess.run(argv, cwd="/Users/luckye/Documents/Code/synara", env=env, capture_output=True, text=True, timeout=20)
    commands.append({"argv": argv, "stdout": p.stdout, "stderr": p.stderr, "exit": p.returncode})
    return json.loads(p.stdout)

primary = call("pagination-frozen")["task"]
negative = call("no-submit-frozen")["task"]
check("explicit-delivery-accepted", primary["state"] == "accepted")
check("worker-reclaimed", primary["current_attempt"]["reclaimed"])
check("no-delivery-remains-claimed", negative["state"] == "claimed" and negative["candidate_commit"] is None and negative["verification"] is None)
for name, expected in [("status-7.json", "submitted"), ("verify-3.json", "verified"), ("integrate-3.json", "accepted"), ("no-submit-status-3.json", "claimed")]:
    record = json.loads((HERE / name).read_text())
    check(name, json.loads(record["stdout"])["task"]["state"] == expected)
for name, error in [("no-submit-verify-3.json", "not_submitted"), ("no-submit-integrate-3.json", "not_verified")]:
    record = json.loads((HERE / name).read_text())
    check(name, record["exit"] == 1 and json.loads(record["stdout"])["error"] == error)
for name, expected in [("frozen-no-submit-native-observe-1.json", "ready"), ("frozen-primary-native-archived.json", "stopped")]:
    native = json.loads(json.loads((HERE / name).read_text())["result"]["content"][0]["text"])
    check(name, native["latestTurnState"] == "completed" and native["sessionStatus"] == expected and (expected != "stopped" or native["archived"]))
v = primary["verification"]
result = json.loads(v["result"]["stdout"])
check("frozen-independent-oracle-twelve-cases", result["status"] == "PASS" and len(result["cases"]) == 12 and all(c["pass"] for c in result["cases"]))
check("oracle-bytes-unchanged", Path(v["oracle"]).read_bytes() == (HERE.parents[2] / "acceptance/pagination_oracle.py").read_bytes())
check("verification-worktree-independent", v["workspace"] != primary["current_attempt"]["workspace"])
p = subprocess.run(["git", "-C", runtime["repo_3"], "rev-parse", "refs/a2a/integration"], capture_output=True, text=True)
commands.append({"argv": p.args, "stdout": p.stdout, "stderr": p.stderr, "exit": p.returncode})
head = subprocess.check_output(["git", "-C", primary["current_attempt"]["workspace"], "rev-parse", "HEAD"], text=True).strip()
check("authoritative-ref-and-worker-head-match-verified-candidate", p.returncode == 0 and p.stdout.strip() == head == v["C"] == v["M"])
events = json.loads(json.loads((HERE / "frozen-events-before-integrate.json").read_text())["stdout"])["events"]
check("wrong-session-rejected-before-submission", any(e["type"] == "rejected" and e["details"].get("error") == "stale_session" for e in events))
binding = json.loads((HERE / "frozen-runtime-binding.json").read_text())
check("loaded-artifact-equals-frozen-source-rebuild", binding["full_bytes_equal"] and binding["candidate"] == "7cb0ac0a3d5232e90ab2db1fb7eb9ee696d1af73")
print(json.dumps({"status": "PASS" if all(c["pass"] for c in checks) else "FAIL", "checks": checks, "commands": commands}, ensure_ascii=False, indent=2))
sys.exit(0 if all(c["pass"] for c in checks) else 1)
