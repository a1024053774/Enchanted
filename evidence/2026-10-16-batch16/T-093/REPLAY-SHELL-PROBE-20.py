#!/usr/bin/env python3
"""重放审查者的给定边界探针；仅迁移输出目录和可选源码版本。"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--revision")
args = parser.parse_args()
repository = Path(__file__).resolve().parents[3]
output = args.output.resolve()
command_output = output.with_name(output.name + ".command.json")
if output.exists() or command_output.exists():
    parser.error("输出必须是全新路径")
revision = None
if args.revision:
    if not re.fullmatch(r"[0-9a-f]{7,40}", args.revision):
        parser.error("版本必须是 Git 对象 ID")
    revision = subprocess.check_output(
        ["git", "-C", str(repository), "rev-parse", args.revision + "^{commit}"], text=True
    ).strip()
scratch = Path(tempfile.mkdtemp(prefix="t093-shell-replay20-", dir="/private/tmp"))
source = Path(__file__).with_name("REVIEWER-SHELL-PROBE-20.mjs").read_text()
old_output = "const OUTPUT = '/private/tmp/t093-shell-recheck-joPlVg';"
assert source.count(old_output) == 1
source = source.replace(old_output, "const OUTPUT = " + json.dumps(str(scratch)) + ";")
old_repository = "const REPO = '/Users/luckye/Documents/Code/a2a-wt-t093';"
assert source.count(old_repository) == 1
source = source.replace(old_repository, "const REPO = " + json.dumps(str(repository)) + ";")
if revision:
    with (scratch / "panes-base.ts").open("xb") as stream:
        stream.write(subprocess.check_output([
            "git", "-C", str(repository), "show", revision + ":workbench/src/panes.ts"
        ]))
script = scratch / "probe.mjs"
script.write_text(source)
command = ["node", str(script), "base" if revision else "candidate"]
completed = subprocess.run(command, cwd=repository, text=True, capture_output=True, start_new_session=True)
results = list(scratch.glob("*/result.json"))
if len(results) != 1:
    raise RuntimeError("审查探针未生成唯一结果；现场保留在 " + str(scratch))
with output.open("xb") as stream:
    stream.write(results[0].read_bytes())
with command_output.open("x") as stream:
    json.dump({
        "scope": "worker replay of unchanged independent oracle; supplied boundaries only",
        "command": command, "cwd": str(repository), "revision_override": revision,
        "source_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip(),
        "working_tree": subprocess.check_output(["git", "diff", "--name-only"], cwd=repository, text=True).splitlines(),
        "exit_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr,
        "result": str(results[0]), "scratch": str(scratch),
        "changes_to_oracle": "none; only repository/output directory constants changed"
    }, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
result = json.loads(output.read_text())
print(json.dumps({"status": result["status"], "cases": result["count"], "passed": result["passed"], "output": str(output)}))
raise SystemExit(completed.returncode)
