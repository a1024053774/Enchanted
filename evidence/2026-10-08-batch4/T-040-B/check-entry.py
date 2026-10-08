#!/usr/bin/env python3
"""Check the requested entry points before running the live desktop scenario."""
import json
import os
from pathlib import Path
import subprocess
import sys

repo = Path("/Users/luckye/Documents/Code/synara")
results = []
for name in ("workbench", "gate"):
    entry = repo / "a2a/scripts" / name
    item = {"entry": str(entry), "executable": os.access(entry, os.X_OK)}
    if item["executable"]:
        result = subprocess.run([str(entry), "--help"], capture_output=True, text=True)
        item.update(exit=result.returncode, stdout=result.stdout, stderr=result.stderr)
    results.append(item)
print(json.dumps(results, ensure_ascii=False, indent=2))
sys.exit(0 if all(r["executable"] and r.get("exit") == 0 for r in results) else 1)
