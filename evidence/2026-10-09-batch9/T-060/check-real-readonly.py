"""Record real list runs and compare Git state and map bytes directly."""
import argparse
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
out = parser.parse_args().output


def capture():
    status = subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"],
                                     cwd=ROOT, text=True)
    files = {str(p.relative_to(ROOT)): p.read_bytes()
             for p in (ROOT / ".project-map").rglob("*") if p.is_file()}
    return status, files


before_status, before = capture()
commands = []
for role in ("ideation", "executor", "user"):
    argv = [str(ROOT / "scripts/inbox"), "list", "--role", role]
    p = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=20)
    ack_ids = [line.split()[1] for line in p.stdout.splitlines()
               if line.startswith("ENTRY ") and line.split()[2] == "ack"]
    commands.append(dict(argv=argv, cwd=str(ROOT), exit_code=p.returncode,
                         stdout=p.stdout, stderr=p.stderr, ack_entry_ids=ack_ids))
after_status, after = capture()
record = dict(commands=commands, before_status=before_status, after_status=after_status,
              before_files=sorted(before), after_files=sorted(after),
              status_identical=before_status == after_status, map_bytes_identical=before == after,
              changed_existing=sorted(name for name in before.keys() & after.keys() if before[name] != after[name]),
              added=sorted(after.keys() - before.keys()), removed=sorted(before.keys() - after.keys()))
with out.open("x", encoding="utf-8") as file:
    json.dump(record, file, ensure_ascii=False, indent=2)
    file.write("\n")
passed = (record["status_identical"] and record["map_bytes_identical"] and
          all(p["exit_code"] == 0 and not p["ack_entry_ids"] for p in commands))
print(json.dumps(dict(status="PASS" if passed else "INCOMPLETE", status_identical=record["status_identical"],
                      map_bytes_identical=record["map_bytes_identical"],
                      exits=[p["exit_code"] for p in commands], ack_entry_ids=[p["ack_entry_ids"] for p in commands])))
raise SystemExit(0 if passed else 1)
