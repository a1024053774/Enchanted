"""Probe safety/classification using synthetic paths only; not OS evidence."""
import contextlib
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

output = Path(sys.argv[1])
if output.exists():
    raise SystemExit("preserve earlier evidence")
probe = runpy.run_path(str(Path(__file__).with_name("probe_t093_parent_sandbox.py")), run_name="probe_safety")
with tempfile.TemporaryDirectory(prefix="t093-probe-safety-", dir="/private/tmp") as temporary:
    target = Path(temporary).resolve()
    created = probe["attempt"](target)
    assert created["exclusive_create"] and created["created"] and created["deleted"] and created["absent_after"]
    existing = target / ".a2a-t093-deny-existing"
    existing.write_text("independent preexisting file must survive")
    rejected = False
    with patch.object(probe["uuid"], "uuid4", return_value=SimpleNamespace(hex="existing")):
        try:
            probe["attempt"](target)
        except RuntimeError as error:
            rejected = str(error) == "unique_probe_path_already_exists"
    assert rejected and existing.read_text() == "independent preexisting file must survive"
    captured = io.StringIO()
    with patch.object(probe["pwd"], "getpwuid", return_value=SimpleNamespace(pw_dir=str(target))), contextlib.redirect_stdout(captured):
        code = probe["child"](target)
    child = json.loads(captured.getvalue())
    assert code == 2 and child["primary_failure"] == {"kind": "AssertionError", "message": "home_write_must_be_denied"}
    assert child["attempt"]["created"] and child["attempt"]["deleted"] and child["attempt"]["absent_after"]
value = {"status": "PASS", "exclusive_create_and_immediate_delete": created,
         "preexisting_file_refused_and_preserved": rejected, "unguarded_synthetic_write_business_rejected": child,
         "scope": "synthetic target and supplied account path; no real HOME, OS sandbox, child process, auth or model"}
with output.open("x") as stream:
    json.dump(value, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"status": "PASS", "checks": 3, "real_home_attempts": 0}))
