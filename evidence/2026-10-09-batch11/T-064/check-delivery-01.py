"""Check only this approval-gate handoff and preserve the actual outputs."""
import ast
import datetime as dt
import json
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[3]
evidence = Path(__file__).resolve().parent
ticket = root / ".project-map/tickets/T-064-role-permission-settings.md"
inbox = root / ".project-map/inbox/20261010T064912Z-worker:t064-issue-001.md"
checks = []


def command(argv, cwd=root):
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
    checks.append({"argv": argv, "cwd": str(cwd), "returncode": result.returncode,
                   "stdout": result.stdout, "stderr": result.stderr})
    return result


for path in [*sorted(evidence.iterdir()), ticket, inbox]:
    if not path.is_file():
        continue
    data = path.read_bytes()
    text = data.decode("utf-8", errors="strict")
    if data.startswith(b"\xef\xbb\xbf") or "\ufffd" in text or b"\r\n" in data:
        raise ValueError("Unexpected encoding/newline in " + str(path))
    if path.suffix == ".py":
        ast.parse(text, filename=str(path))
    if path.suffix == ".md":
        for relative in re.findall(r"\]\(([^)]+)\)", text):
            if relative.startswith(("https:", "http:", "#")):
                continue
            target = relative.split("#", 1)[0]
            if not (path.parent / target).is_file():
                raise FileNotFoundError(str(path) + " -> " + target)
    checks.append({"path": str(path.relative_to(root)), "utf8_no_bom_lf": True,
                   "python_syntax_checked": path.suffix == ".py"})

status = command(["python3", "/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py",
                  "status", "--root", "."])
diff = command(["git", "diff", "--check"])
command(["git", "status", "--short"])
command(["git", "status", "--short"], Path("/Users/luckye/Documents/Code/synara"))
revision = command(["git", "rev-parse", "HEAD"], Path("/Users/luckye/Documents/Code/synara"))
if revision.stdout.strip() != "7a3a13249e562bf2d7f9ff4cb024f39b13d62434":
    raise RuntimeError("Fork HEAD changed; approval references need rechecking")
record = {"created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
          "status": "BLOCKED", "checks": checks,
          "replay": "python3 evidence/2026-10-09-batch11/T-064/check-delivery-01.py (archive this output before rerunning)",
          "product_checks": "not run; product unchanged and upstream approval pending"}
with (evidence / "delivery-checks-01.json").open("x", encoding="utf-8") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"map_returncode": status.returncode, "diff_returncode": diff.returncode,
                  "checked_files": len(checks), "status": "BLOCKED"}, ensure_ascii=False))
raise SystemExit(max(status.returncode, diff.returncode))
