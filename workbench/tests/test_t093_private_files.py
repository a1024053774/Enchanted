"""No CLI/auth-source access: synthetic files exercise the private read boundary."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

helper = Path(__file__).resolve().parents[1] / "src/claudeLoginFiles.py"
output = Path(sys.argv[1])
if output.exists():
    raise SystemExit("preserve earlier evidence")
checks = []


def run(value):
    return subprocess.run(["/usr/bin/python3", "-B", str(helper)], input=json.dumps(value),
                          text=True, capture_output=True, timeout=5)


with tempfile.TemporaryDirectory(prefix="t093-private-files-", dir="/private/tmp") as temporary:
    home = Path(temporary)
    config = home / ".claude"
    config.mkdir(mode=0o700)
    credential = config / ".credentials.json"
    oauth = {"accessToken": "synthetic-private-file-only", "expiresAt": (time.time() + 300) * 1000}
    credential.write_text(json.dumps({"claudeAiOauth": oauth, "unrelated": "must not copy"}))
    command = {"operation": "auth", "home": str(home), "source": "file"}
    result = run(command)
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"claudeAiOauth": oauth}
    checks.append("only OAuth login object returned; unrelated source object omitted")
    before = json.loads(run({"operation": "inventory", "home": str(home)}).stdout)
    assert ".claude/.credentials.json" in before
    assert "accessToken" not in json.dumps(before)
    (config / "observed-change").write_text("metadata-only fixture")
    after = json.loads(run({"operation": "inventory", "home": str(home)}).stdout)
    assert ".claude/observed-change" in after and ".claude/observed-change" not in before
    checks.append("metadata inventory observes an independent new file without reading contents")
    credential.rename(config / "original")
    credential.symlink_to(config / "original")
    result = run(command)
    assert result.returncode == 2 and result.stdout == ""
    assert "synthetic-private-file-only" not in result.stderr
    checks.append("credential symlink rejected without source payload or raw exception")
    credential.unlink()
    (config / "original").rename(credential)
    config.rename(home / "renamed")
    config.symlink_to(home / "renamed", target_is_directory=True)
    result = run(command)
    assert result.returncode == 2 and result.stdout == ""
    checks.append("ancestor symlink rejected")
    config.unlink()
    (home / "renamed").rename(config)
    oauth["expiresAt"] = (time.time() - 1) * 1000
    credential.write_text(json.dumps({"claudeAiOauth": oauth}))
    result = run(command)
    assert result.returncode == 2 and result.stdout == ""
    checks.append("expired login rejected without exposing token")
output.write_text(json.dumps({"status": "PASS", "checks": checks, "real_credential_reads": 0}, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": "PASS", "checks": len(checks)}))
