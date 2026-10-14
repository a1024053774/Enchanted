#!/usr/bin/env python3
"""在新证据目录中建立两份启动器变异副本，保留生产脚本。"""
import argparse
import difflib
from pathlib import Path
import shutil


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("label")
args = parser.parse_args()
evidence = Path(__file__).resolve().parent
scripts = evidence.parents[2] / "scripts"
target = evidence / args.label
target.mkdir()
source = (scripts / "launch-worker").read_text(encoding="utf-8")
mutations = {
    "fast": ('else \'service_tier="default"\'', 'else \'service_tier="fast"\''),
    "without-no-daemon": (', "--no-daemon",\n', ',\n'),
}
for name, (before, after) in mutations.items():
    assert source.count(before) == 1, name
    copy = target / name / "scripts"
    shutil.copytree(scripts, copy, symlinks=True, ignore=shutil.ignore_patterns("__pycache__"))
    changed = source.replace(before, after)
    (copy / "launch-worker").write_text(changed, encoding="utf-8")
    (copy.parent / "mutation.diff").write_text(
        "".join(difflib.unified_diff(source.splitlines(keepends=True), changed.splitlines(keepends=True),
                                     fromfile="scripts/launch-worker", tofile=name+"/scripts/launch-worker")),
        encoding="utf-8")
    print(copy)
