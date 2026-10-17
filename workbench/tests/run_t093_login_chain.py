"""Controller entry: detached no-model native PTY chain. Never requests escalation."""
import argparse
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
if output.exists():
    parser.error("output exists; preserve earlier evidence and select a new path")
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
raise SystemExit(code)
