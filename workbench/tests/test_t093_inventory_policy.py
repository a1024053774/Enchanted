"""L1 classification contract from decision A; no child process or HOME read."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

output = Path(sys.argv[1])
if output.exists():
    raise SystemExit("preserve earlier evidence")
script = Path(__file__).with_name("run_t093_login_chain.py").resolve()
candidate = script.read_text()
legacy = subprocess.run(["git", "show", "7fbc5d9ef:workbench/tests/run_t093_login_chain.py"],
                        capture_output=True, text=True, check=True).stdout
before = {".claude/concurrent.jsonl": {"bytes": 1, "mtime_ns": 1}}
different = {".claude/concurrent.jsonl": {"bytes": 2, "mtime_ns": 2}}


def exercise(source, root, label, child_exit, after):
    path = root / (label + ".json")
    values = iter([before, after])
    child = SimpleNamespace(wait=lambda **kwargs: child_exit, pid=-1)
    with patch.object(sys, "argv", [str(script), "--output", str(path)]), \
         patch("subprocess.run", side_effect=lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=json.dumps(next(values)))), \
         patch("subprocess.Popen", return_value=child), contextlib.redirect_stdout(io.StringIO()):
        try:
            exec(compile(source, str(script), "exec"), {"__name__": "__main__", "__file__": str(script)})
        except SystemExit as result:
            code = result.code
    report = json.loads(path.with_name(path.stem + ".host-home.json").read_text())
    return code, report


checks = []
with tempfile.TemporaryDirectory(prefix="t093-inventory-policy-", dir="/private/tmp") as temporary:
    root = Path(temporary)
    for child_exit in (0, 2):
        for changed in (False, True):
            code, report = exercise(candidate, root, f"current-{child_exit}-{changed}", child_exit, different if changed else before)
            expected_status = "PASS" if child_exit == 0 else "INCOMPLETE"
            ok = code == child_exit and report["status"] == expected_status
            ok = ok and report["changed"] == ([".claude/concurrent.jsonl"] if changed else [])
            if changed:
                ok = ok and report["differences"][0]["before"] == before[".claude/concurrent.jsonl"]
                ok = ok and report["differences"][0]["after"] == different[".claude/concurrent.jsonl"]
            checks.append({"child_exit": child_exit, "inventory_changed": changed,
                           "exit_code": code, "reported_status": report["status"],
                           "status": "PASS" if ok else "INCOMPLETE"})
    code, report = exercise(legacy, root, "legacy-changed", 0, different)
    legacy_rejected = code == 2 and report["status"] == "INCOMPLETE" and report["changed"] == [".claude/concurrent.jsonl"]
value = {"status": "PASS" if all(row["status"] == "PASS" for row in checks) and legacy_rejected else "INCOMPLETE",
         "decision": "main c06a73179 T-093 decision A; inventory differences are informational",
         "checks": checks, "legacy_zero_difference_gate_rejected": legacy_rejected,
         "scope": "actual wrapper classification with supplied metadata and child exit; no real child/HOME/OS-sandbox evidence"}
with output.open("x") as stream:
    json.dump(value, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"status": value["status"], "checks": len(checks), "legacy_rejected": legacy_rejected}))
raise SystemExit(0 if value["status"] == "PASS" else 2)
