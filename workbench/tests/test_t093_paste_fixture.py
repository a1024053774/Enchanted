"""Check the actual native fixture parser; no vendor, auth, network or ps."""
import errno
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
import time

source = Path(__file__).resolve().parents[2]
output = Path(sys.argv[1])
if output.exists():
    raise SystemExit("preserve earlier evidence")
results = []
for revision in ("ff625c371", "current"):
    with tempfile.TemporaryDirectory(prefix="t093-paste-", dir="/private/tmp") as temporary:
        root = Path(temporary)
        code = (source / "workbench/tests/t093_fake_claude.c").read_bytes() if revision == "current" else subprocess.run(
            ["git", "show", revision + ":workbench/tests/t093_fake_claude.c"], cwd=source, capture_output=True, check=True).stdout
        (root / "peer.c").write_bytes(code)
        subprocess.run(["/usr/bin/clang", "-Wall", "-Werror", str(root / "peer.c"), "-o", str(root / "peer")], capture_output=True, check=True)
        (root / "fake-login-peer.py").write_text("""import json,sys
from pathlib import Path
if sys.argv[2] != '0':
    with (Path(__file__).parent/'received.jsonl').open('a') as stream:
        stream.write(json.dumps(sys.argv[1])+'\\n')
""")
        master, slave = os.openpty()
        child = subprocess.Popen([str(root / "peer"), "--settings", "{}"], stdin=slave, stdout=slave, stderr=slave, start_new_session=True)
        os.close(slave)
        raw = b""
        try:
            until = time.monotonic() + 5
            while b"fixture-ready" not in raw:
                if time.monotonic() > until:
                    raise RuntimeError("fixture ready deadline")
                if select.select([master], [], [], 0.05)[0]:
                    raw += os.read(master, 65536)
            payload = "独立第一行\n第二行与末行"
            os.write(master, b"\x1b[200~" + payload.encode() + b"\x1b[201~\r")
            expected_turns = 1 if revision == "current" else 2
            until = time.monotonic() + 5
            while ("fixture-turn-%d-complete" % expected_turns).encode() not in raw:
                if time.monotonic() > until:
                    raise RuntimeError("fixture submission deadline")
                if select.select([master], [], [], 0.05)[0]:
                    raw += os.read(master, 65536)
            calls = [json.loads(line) for line in (root / "received.jsonl").read_text().splitlines()]
            matches = calls == [payload]
            assert matches if revision == "current" else not matches
            results.append({"revision": revision, "calls": len(calls), "one_intact_submission": matches, "status": "PASS"})
        finally:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait(timeout=5); os.close(master)
output.write_text(json.dumps({"status": "PASS", "checks": results, "real_cli_starts": 0}, indent=2) + "\n")
print(json.dumps({"status": "PASS", "checks": len(results)}))
