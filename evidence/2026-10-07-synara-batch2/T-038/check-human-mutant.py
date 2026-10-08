#!/usr/bin/env python3
"""Prove the protocol assertions reject an always-empty reader, then restore owned bytes."""
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
source = Path("/Users/luckye/Documents/Code/synara-t038/apps/web/src/a2a/humanIntervention.ts")
record = root / ((sys.argv[1] if len(sys.argv) > 1 else "human-reader-mutant-01") + ".json")
assert not record.exists()
original = source.read_bytes()
text = original.decode("utf-8")
needle = "  const seen = new Set<string>();"
assert text.count(needle) == 1
mutant = text.replace(needle, "  return []; // Known-bad test mutant: ignores every intervention.\n" + needle)
(root / (record.stem + "-original.ts.txt")).write_bytes(original)
(root / (record.stem + "-mutant.ts.txt")).write_text(mutant, encoding="utf-8")
env = os.environ.copy()
env["A2A_SYNARA_SLOT"] = "t038"
argv = ["./a2a/scripts/bun", "run", "--cwd", "apps/web", "test", "src/a2a/humanIntervention.test.ts"]
try:
    source.write_text(mutant, encoding="utf-8")
    p = subprocess.run(argv, cwd="/Users/luckye/Documents/Code/synara-t038", env=env, text=True, capture_output=True, timeout=90)
finally:
    source.write_bytes(original)
record.write_text(json.dumps({"argv": argv, "exit": p.returncode, "stdout": p.stdout, "stderr": p.stderr,
    "restored_bytes_equal": source.read_bytes() == original}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(record)
assert p.returncode != 0 and "human intervention protocol fixtures" in p.stdout + p.stderr
