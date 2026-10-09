#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--repo", type=Path, required=True)
parser.add_argument("--candidate", required=True)
parser.add_argument("--parent", required=True)
parser.add_argument("--artifacts", type=Path, required=True)
a = parser.parse_args()
a.artifacts.mkdir(parents=True, exist_ok=False)
records = {
    "T-861": "---\nid: T-861\ntitle: 已结束闭合 sentinel 雪\ntype: task\nstatus: closed\nblocked_by: []\nclaimed_by:\nready_by: executor\n---\n",
    "T-862": "---\nid: T-862\ntitle: 已结束取代 sentinel 海\ntype: research\nstatus: superseded\nblocked_by: []\nclaimed_by:\nready: alien\nready_by: alien\nready_rev: invalid\n---\n",
    "T-863": "---\nid: T-863\ntitle: 已结束出范围 sentinel 山\ntype: build\nstatus: out-of-scope\nblocked_by: []\nclaimed_by:\n---\n",
    "T-877": "---\nid: T-877\ntitle: 尚未标记 sentinel café\ntype: task\nstatus: open\nblocked_by: []\nclaimed_by:\n---\n",
    "T-889": "---\nid: T-889\ntitle: 部分字段 sentinel 水\ntype: build\nstatus: open\nblocked_by: []\nclaimed_by:\nready_rev: 29\n---\n",
    "T-899": "---\nid: T-899\ntitle: 依赖已结束 sentinel Ω\ntype: research\nstatus: open\nblocked_by: [T-861, T-862]\nclaimed_by:\nready: yes\nready_by: executor\nready_rev: 23\n---\n",
}
expected = {
    "exit_code": 1,
    "unmarked": "未标就绪：T-877 尚未标记 sentinel café",
    "ready": "READY T-899 research rev=23 by=executor 依赖已结束 sentinel Ω",
    "diagnostics": ["不合规：T-889 缺少 ready, ready_by"],
    "ended_absent": ["T-861", "T-862", "T-863"],
}
(a.artifacts / "inputs.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(a.artifacts / "expected.json").write_text(json.dumps(expected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
results = {}
for name, rev in [("candidate", a.candidate), ("parent", a.parent)]:
    folder = a.artifacts / name
    tickets = folder / "fixture/.project-map/tickets"
    tickets.mkdir(parents=True)
    for ident, text in records.items():
        (tickets / (ident + "-sentinel.md")).write_text(text, encoding="utf-8")
    source = subprocess.check_output(["git", "show", rev + ":scripts/inbox"], cwd=a.repo)
    entry = folder / "inbox"
    entry.write_bytes(source)
    argv = [sys.executable, "-B", str(entry), "--root", str(folder / "fixture"), "ready"]
    p = subprocess.run(argv, cwd=folder / "fixture", text=True, encoding="utf-8", capture_output=True, timeout=20)
    raw = {"revision": rev, "argv": argv, "cwd": str(folder / "fixture"), "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    (folder / "raw.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (folder / "stdout.txt").write_text(p.stdout, encoding="utf-8")
    (folder / "stderr.txt").write_text(p.stderr, encoding="utf-8")
    stdout_lines = p.stdout.splitlines()
    checks = {
        "exit": p.returncode == expected["exit_code"],
        "unmarked": expected["unmarked"] in stdout_lines,
        "ready_dependency_preserved": expected["ready"] in stdout_lines,
        "only_partial_diagnostic": p.stderr.splitlines() == expected["diagnostics"],
        "ended_not_listed": all(ident not in p.stdout + p.stderr for ident in expected["ended_absent"]),
        "no_spurious_stdout": sorted(stdout_lines) == sorted([expected["unmarked"], expected["ready"]]),
        "input_files_unchanged": {path.stem.split("-sentinel")[0]: path.read_text(encoding="utf-8") for path in tickets.glob("*.md")} == records,
    }
    results[name] = {"checks": checks, "contract_pass": all(checks.values()), "raw": str(folder / "raw.json")}
(a.artifacts / "judgment.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"artifacts": str(a.artifacts), "results": results}, ensure_ascii=False, indent=2))
sys.exit(0 if results["candidate"]["contract_pass"] and not results["parent"]["contract_pass"] else 1)
