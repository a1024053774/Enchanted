#!/usr/bin/env python3
"""Replay T-151's domain check and its duplicate-Stop counterexample."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


parser = argparse.ArgumentParser()
parser.add_argument("--summary", required=True, type=Path)
parser.add_argument("--mutant", choices=["duplicate-stop-idle"])
args = parser.parse_args()
if args.summary.exists():
    parser.error("summary path already exists; choose a new path")
repo = Path(__file__).resolve().parents[3]
workbench = repo / "workbench"
fixture = Path(tempfile.mkdtemp(prefix="t151-check-"))
snapshot = fixture / "workbench"
shutil.copytree(workbench / "src", snapshot / "src")
(snapshot / "tests").mkdir()
(snapshot / "node_modules").symlink_to(workbench / "node_modules", target_is_directory=True)
test_name = "test_t078_claude_signals.ts"
shutil.copy2(workbench / "tests" / test_name, snapshot / "tests" / test_name)

if args.mutant:
    source = snapshot / "src" / "panes.ts"
    original = source.read_text(encoding="utf-8")
    anchor = ('const matched = current && value.stop_hook_active === false;\n'
              '        if (!matched) { this.store.event("stop_not_matched", value, pane.record); return; }\n'
              '        check(currentTurnTrust')
    if original.count(anchor) != 1:
        raise RuntimeError("Claude unmatched-Stop mutation anchor is not unique")
    replacement = ('const matched = current && value.stop_hook_active === false;\n'
                   '        if (!matched) { this.store.event("pane_idle", { stop: value }, pane.record); '
                   'this.store.event("stop_not_matched", value, pane.record); return; }\n'
                   '        check(currentTurnTrust')
    source.write_text(original.replace(anchor, replacement), encoding="utf-8")

command = ["node", str(snapshot / "tests" / test_name), str(fixture / "output")]
run = subprocess.run(command, cwd=repo, capture_output=True, text=True, timeout=30)
result_file = fixture / "output" / "results.json"
result = json.loads(result_file.read_text(encoding="utf-8")) if result_file.exists() else None
failed = [c for c in result["checks"] if c["status"] != "PASS"] if result else []
events_file = fixture / "output" / "events.json"
events = json.loads(events_file.read_text(encoding="utf-8")) if events_file.exists() else []
idle_count = sum(event["type"] == "pane_idle" for event in events)
if args.mutant:
    passed = (run.returncode == 1 and result is not None and result["status"] == "INCOMPLETE"
              and len(failed) == 1
              and failed[0]["name"] == "real_hook_shape_matches_one_registered_submission"
              and "AssertionError" in failed[0].get("error", "")
              and "2 !== 1" in failed[0]["error"] and idle_count == 2)
else:
    passed = (run.returncode == 0 and result is not None and result["status"] == "PASS"
              and len(result["checks"]) == 3 and idle_count == 1)
summary = {
    "status": "PASS" if passed else "INCOMPLETE",
    "claim": "mutant rejected by preserved duplicate-Stop check" if args.mutant else "current source passes migrated domain check",
    "mutant": args.mutant,
    "base_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
    "expected_source": ".project-map/tickets/T-151-migrate-t078-claude-signals.md Acceptance and What to build",
    "command": command, "exit_code": run.returncode,
    "stdout": run.stdout, "stderr": run.stderr, "result": result,
    "pane_idle_count": idle_count, "raw_artifacts": str(fixture),
    "scope": "Panes.signal and real SQLite store; synthetic hooks/transcript; no CLI, socket, API, PTY or model",
}
args.summary.parent.mkdir(parents=True, exist_ok=True)
with args.summary.open("x", encoding="utf-8") as output:
    json.dump(summary, output, ensure_ascii=False, indent=2)
    output.write("\n")
print(json.dumps({"status": summary["status"], "summary": str(args.summary), "exit_code": run.returncode,
                  "pane_idle_count": idle_count}))
raise SystemExit(0 if passed else 1)
