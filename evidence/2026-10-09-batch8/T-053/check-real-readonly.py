"""Read-only check of real map. Compare bytes directly, never hashes."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "real-readonly.json")
OUT = parser.parse_args().output

def capture():
    status = subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT,
                            text=True, capture_output=True, check=True).stdout
    files = {str(path.relative_to(ROOT)): path.read_bytes() for path in (ROOT / ".project-map").rglob("*") if path.is_file()}
    return status, files

before_status, before = capture()
commands = []
for command in (["ready"], ["list", "--role", "executor"], ["list", "--role", "ideation"], ["list", "--role", "user"]):
    argv = [str(ROOT / "scripts/inbox"), *command]
    result = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=20)
    commands.append(dict(argv=argv, exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr))
after_status, after = capture()
changed = [name for name in before.keys() & after.keys() if before[name] != after[name]]
record = dict(commands=commands, before_status=before_status, after_status=after_status,
              before_files=sorted(before), after_files=sorted(after), changed_existing=changed,
              removed=sorted(before.keys() - after.keys()), added=sorted(after.keys() - before.keys()),
              status_identical=before_status == after_status, map_bytes_identical=before == after)
with OUT.open("x", encoding="utf-8") as file:
    json.dump(record, file, ensure_ascii=False, indent=2)
    file.write("\n")
print(json.dumps({key: record[key] for key in ("status_identical", "map_bytes_identical", "changed_existing", "removed", "added")}, ensure_ascii=False))
raise SystemExit(0 if before_status == after_status and before == after else 1)
