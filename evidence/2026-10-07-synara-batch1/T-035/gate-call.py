#!/usr/bin/env python3
"""经 live Synara CLI 接缝调用；凭据只从本次 /tmp 根读取，不写入证据。"""
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
runtime = json.loads((HERE / "runtime.json").read_text(encoding="utf-8"))
label, raw = sys.argv[1:]
request = json.loads(raw)
argv = ["./a2a/scripts/bun", "run", "packages/a2a-gates/src/cli.ts", runtime.get("endpoint", "http://127.0.0.1:4835"), json.dumps(request)]
env = dict(os.environ, A2A_SYNARA_SLOT="t035", A2A_GATE_BEARER=Path(runtime["root"], "bootstrap-token").read_text(encoding="utf-8"))
p = subprocess.run(argv, cwd="/Users/luckye/Documents/Code/synara", env=env, capture_output=True, text=True, timeout=75)
record = {"time": datetime.now(timezone.utc).isoformat(), "argv": argv, "stdout": p.stdout, "stderr": p.stderr, "exit": p.returncode}
with (HERE / (label + ".json")).open("x", encoding="utf-8") as f:
    json.dump(record, f, ensure_ascii=False, indent=2)
print(p.stdout)
if p.stderr and p.returncode:
    print(p.stderr, file=sys.stderr)
sys.exit(p.returncode)
