#!/usr/bin/env python3
"""Completion 4: score a clearly labeled fixture using the real append-only entry."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parent
label = sys.argv[1]
directory = EVIDENCE / label
directory.mkdir()
green_label = sys.argv[2] if len(sys.argv) > 2 else "green02"
green = json.loads((EVIDENCE / green_label / "state.json").read_text())
failed = [json.loads(line) for line in (EVIDENCE / "green01/launch-records.jsonl").read_text().splitlines()][-1]
logfile = ROOT / "records/scores.jsonl"
before = logfile.read_bytes() if logfile.exists() else b""
base = [str(ROOT / "scripts/score"), "--launch", green["launch_id"], "--facts", str(EVIDENCE / "score-facts.json"),
        "--result", "通过", "--boundary-discipline", "3", "--boundary-reason", "夹具：允许路径内",
        "--engineering-taste", "2", "--engineering-reason", "夹具：可直接使用"]


def run(argv):
    r = subprocess.run(argv, text=True, capture_output=True)
    with (directory / "commands.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(dict(argv=argv, exit_code=r.returncode, stdout=r.stdout, stderr=r.stderr), ensure_ascii=False)+"\n")
    return r


missing = run(base)  # Required notes omitted; even empty notes must be explicit.
assert missing.returncode != 0
assert (logfile.read_bytes() if logfile.exists() else b"") == before
good = run([*base, "--notes", "独立打分夹具，计数来自 score-facts.json；并非本票最终验收"])
assert good.returncode == 0, good.stderr
row = json.loads(good.stdout)
required = {"schema", "score_id", "created_at", "source", "launch_id", "project", "task", "attempt", "cli", "model", "effort", "data", "facts"}
assert set(row) == required
assert row["task"] == "T-073-1" and row["attempt"] == "fixture-"+green_label and row["project"] == "t073-fixture"
assert row["cli"] == "codex-cli 0.162.1" and row["model"] == "gpt-6.1-sol" and row["effort"] == "xhigh"
assert row["facts"] == json.loads((EVIDENCE / "score-facts.json").read_text(encoding="utf-8"))
assert set(row["data"]) == {"result", "boundary_discipline", "boundary_reason", "engineering_taste", "engineering_reason", "notes"}
after = logfile.read_bytes()
assert json.loads(after.splitlines()[-1]) == row
missing_again = run(base)
assert missing_again.returncode != 0 and logfile.read_bytes() == after
existing_abandon = [json.loads(line) for line in logfile.read_bytes().splitlines()
                    if json.loads(line)["launch_id"] == failed["launch_id"]]
if not existing_abandon:
    abandoned = run([str(ROOT / "scripts/score"), "--launch", failed["launch_id"], "--result", "放弃",
                     "--reason", "夹具启动阶段未启动 CLI，保留故障现场后以新 attempt 验证"])
    assert abandoned.returncode == 0, abandoned.stderr
    abandon_row = json.loads(abandoned.stdout)
else:
    # Final scores are immutable: verify the previous fixture, do not append twice.
    abandon_row = existing_abandon[0]
assert set(abandon_row["data"]) == {"result", "reason"} and abandon_row["data"]["result"] == "放弃"
assert "facts" not in abandon_row
(directory / "scores-readback.jsonl").write_bytes(logfile.read_bytes())
(directory / "verification.json").write_text(json.dumps(dict(status="PASS", missing_fields_exit=missing.returncode,
    missing_fields_file_unchanged=True, full_score_id=row["score_id"], abandon_only_result_reason=True,
    abandon_record_reused=bool(existing_abandon)), indent=2)+"\n", encoding="utf-8")
print("score verification PASS")
