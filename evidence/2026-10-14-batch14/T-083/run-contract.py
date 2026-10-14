#!/usr/bin/env python3
"""保存 T-083 的 T-073 测试命令、原始输出和退出码；不覆盖旧运行。"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("label")
parser.add_argument("--scripts-root", type=Path)
args = parser.parse_args()
evidence = Path(__file__).resolve().parent
repo = evidence.parents[2]
run = evidence / args.label
run.mkdir()
argv = [sys.executable, "-B", "acceptance/test_herdr_traceability_e2e.py",
        "--artifacts", str(run / "artifacts")]
if args.scripts_root:
    argv.extend(["--scripts-root", str(args.scripts_root.resolve())])
record = dict(argv=argv, cwd=str(repo), started_at=datetime.now(timezone.utc).isoformat(),
              commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
              main=subprocess.check_output(["git", "rev-parse", "main"], cwd=repo, text=True).strip(),
              python=sys.version,
              identity={key: value for key, value in os.environ.items()
                        if key in {"A2A_PROJECT", "A2A_TASK", "A2A_ATTEMPT", "A2A_SESSION",
                                   "A2A_ROLE", "A2A_LAUNCH", "CODEX_THREAD_ID"}})
(run / "command.json").write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
with (run / "stdout.txt").open("wb") as stdout, (run / "stderr.txt").open("wb") as stderr:
    result = subprocess.run(argv, cwd=repo, stdout=stdout, stderr=stderr)
(run / "exit-code.txt").write_text(str(result.returncode)+"\n", encoding="utf-8")
print((run / "stderr.txt").read_text(encoding="utf-8"), end="")
print("exit_code="+str(result.returncode))
sys.exit(result.returncode)
