"""Controller entry: detached no-model native PTY chain. Never requests escalation."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
source = Path(__file__).resolve().parents[2]
output = args.output.resolve()
home_output = output.with_name(output.stem + ".host-home.json")
if output.exists() or home_output.exists():
    parser.error("output exists; preserve earlier evidence and select a new path")
real_home = Path.home().resolve()


def inventory():
    completed = subprocess.run(["/usr/bin/python3", "-B", str(source / "workbench/src/claudeLoginFiles.py")],
        input=json.dumps({"operation": "inventory", "home": str(real_home)}), capture_output=True, text=True, timeout=30)
    if completed.returncode:
        raise SystemExit("INCOMPLETE: host HOME metadata inventory unavailable")
    return json.loads(completed.stdout)


# The daemon deliberately uses a synthetic source HOME. Separately observe the
# controller's actual HOME before/after, without reading any auth contents.
before = inventory()
child = subprocess.Popen(["/opt/homebrew/bin/node", str(source / "workbench/tests/test_t093_login_chain.ts"), str(output)],
                         cwd=source, start_new_session=True)
try:
    code = child.wait(timeout=150)
except (subprocess.TimeoutExpired, KeyboardInterrupt):
    os.killpg(child.pid, signal.SIGTERM)
    try:
        child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
    print("INCOMPLETE: detached fixture interrupted; cleanup must be checked", file=sys.stderr)
    code = 2
after = inventory()
changed = [path for path in sorted(set(before) | set(after)) if before.get(path) != after.get(path)]
report = {"status": "PASS" if code == 0 and not changed else "INCOMPLETE", "child_exit": code,
          "scope": [".claude", ".claude.json", ".claude.json.backup", "Library/Keychains"],
          "excludes": ["atime", "contents", "symlink targets", "other HOME paths"],
          "before_entries": len(before), "after_entries": len(after), "changed": changed,
          "differences": [{"path": path, "before": before.get(path), "after": after.get(path)} for path in changed],
          "attribution": "No causal attribution; concurrent sessions may change these paths."}
fd = os.open(home_output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
with os.fdopen(fd, "w") as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"status": report["status"], "child_exit": code, "host_home_differences": len(changed)}))
if changed:
    code = 2
raise SystemExit(code)
