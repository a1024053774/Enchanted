#!/usr/bin/env python3
"""Capture the T-102 baseline without starting an app, daemon, or model."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys


root = Path(__file__).resolve().parents[3]
output = Path(sys.argv[1]).resolve()


def run(argv, env=None):
    result = subprocess.run(argv, cwd=root, env=env, capture_output=True,
                            text=True, timeout=30)
    return {"argv": argv, "exit_code": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


mount_env = dict(os.environ, A2A_BUILD_VOLUME=str(root))
record = {
    "schema": 1,
    "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "task": "T-102", "attempt": "a1", "ready_rev": 1,
    "session": "b39683a9-f281-4941-aa23-d4479d9a917d",
    "launch": "launch-60574dbe21504c0594fc02ef9a2475e3",
    "fence": None,
    "root": str(root),
    "code": run(["git", "rev-parse", "HEAD"]),
    "node": run(["node", "--version"]),
    "installed_app": {"path": "/Applications/a2a.app",
                      "exists": os.path.lexists("/Applications/a2a.app")},
    "missing_task": run(["node", "workbench/app/start.mjs", "--build",
                         str(root / "T102-NO-BUILD-NEEDED")]),
    "ordinary_directory_mount": {
        "environment": {"A2A_BUILD_VOLUME": str(root)},
        **run(["node", "workbench/app/build.mjs", "--slot", "t102-mount-probe"], mount_env),
    },
    "project_map": run(["python3", "/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py",
                        "status", "--root", "."]),
}
with output.open("x", encoding="utf-8") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(output)
