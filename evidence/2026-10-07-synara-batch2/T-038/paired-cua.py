#!/usr/bin/env python3
"""Alternate baseline and candidate under the same isolated temp/cache environment."""
import json
import os
from pathlib import Path
import subprocess
import time

root = Path(__file__).resolve().parent
argv = ["./a2a/scripts/bun", "run", "--cwd", "apps/desktop", "test",
        "src/cuaDriverHost.test.ts", "-t", "stays fail-closed when the crash cleanup is unconfirmed"]
env = os.environ.copy()
env["A2A_SYNARA_SLOT"] = "t038-cua-pair"
for iteration in range(1, 4):
    for variant, checkout in [("baseline", "synara-t038-baseline"), ("candidate", "synara-t038")]:
        label = f"paired-cua-{iteration}-{variant}"
        record, log = root / (label + ".json"), root / (label + ".log")
        assert not record.exists() and not log.exists(), label
        cwd = Path("/Users/luckye/Documents/Code") / checkout
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cwd, text=True).strip()
        load = subprocess.check_output(["uptime"], text=True).strip()
        started = time.time()
        with log.open("x", encoding="utf-8") as stream:
            result = subprocess.run(argv, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                    start_new_session=True, timeout=120)
        data = {"iteration": iteration, "variant": variant, "argv": argv, "cwd": str(cwd),
                "revision": revision, "slot": env["A2A_SYNARA_SLOT"], "load_before": load,
                "started": started, "seconds": time.time() - started, "exit": result.returncode,
                "git_status_after": subprocess.check_output(["git", "status", "--short"], cwd=cwd, text=True)}
        record.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"label": label, "exit": result.returncode, "seconds": data["seconds"]}), flush=True)
