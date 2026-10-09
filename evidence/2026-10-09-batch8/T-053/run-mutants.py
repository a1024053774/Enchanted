"""Create isolated known-bad CLI snapshots and retain their raw failing runs."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--out", type=Path)
args = parser.parse_args()
if args.out is not None:
    EVIDENCE = args.out.resolve()
    EVIDENCE.mkdir(parents=True, exist_ok=False)
original = (ROOT / "scripts/inbox").read_text(encoding="utf-8")
mutants = [
    ("seconds-only", "InboxCLI.test_concurrent_twenty_and_clock_rollback", [
        ('''candidate = ident or f"{now.strftime('%Y%m%dT%H%M%SZ')}-{item['from']}-{item['kind']}-{sequence:03d}"''',
         '''candidate = ident or now.strftime('%Y%m%dT%H%M%SZ')'''),
        ("sequence += 1", 'raise InboxError("秒级文件名冲突")'),
    ]),
    ("ack-sender-ignored", "InboxCLI.test_recipient_ack_and_dangling_reply", [
        (' and item["from"] == role', ""),
    ]),
]
records = []
for name, test, changes in mutants:
    path = EVIDENCE / ("mutant-" + name + ".py")
    candidate = original
    for before, after in changes:
        if candidate.count(before) != 1:
            raise RuntimeError("mutation source must match exactly once: " + before)
        candidate = candidate.replace(before, after)
    with path.open("x", encoding="utf-8") as file:
        file.write(candidate)
    path.chmod(0o755)
    artifact = EVIDENCE / ("mutant-" + name + "-01")
    argv = [sys.executable, "-B", str(ROOT / "acceptance/test_inbox_e2e.py"), "--artifacts", str(artifact), test]
    env = dict(os.environ, INBOX_SCRIPT=str(path))
    result = subprocess.run(argv, cwd=ROOT, env=env, text=True, capture_output=True, timeout=45)
    records.append(dict(name=name, argv=argv, env={"INBOX_SCRIPT": str(path)}, exit_code=result.returncode,
                        stdout=result.stdout, stderr=result.stderr, changes=changes))
    print(name, "REJECTED" if result.returncode == 1 else "UNEXPECTED", result.returncode)
    print(result.stdout)
with (EVIDENCE / "mutants.json").open("x", encoding="utf-8") as file:
    json.dump(records, file, ensure_ascii=False, indent=2)
    file.write("\n")
sys.exit(0 if all(record["exit_code"] == 1 for record in records) else 1)
