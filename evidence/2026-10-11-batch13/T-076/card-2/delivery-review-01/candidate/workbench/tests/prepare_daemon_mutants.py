"""Freeze one candidate and three single-site gate mutants for the daemon host."""
import argparse
import difflib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "evidence/2026-10-10-batch12/T-075/card-5"


def prepare(out):
    out.mkdir(exist_ok=False)
    root = Path(tempfile.mkdtemp(prefix="a5-mutants-", dir="/tmp")).resolve()
    candidate = root / "candidate/workbench"
    shutil.copytree(ROOT / "workbench/src", candidate / "src")
    for name in ("package.json", "package-lock.json", "LICENSE.synara"):
        shutil.copyfile(ROOT / "workbench" / name, candidate / name)
    core = (candidate / "src/gates/core.ts").read_text(encoding="utf-8")
    changes = {
        "fence": ('        requireGate(args.fence === attempt.fence, "stale_fence");',
                  '        // MUTANT: omit the submit fence check.'),
        "cas": ('${intent.M} ${intent.G}\\nprepare\\n', '${intent.M}\\nprepare\\n'),
        "lock": ('      lock.exec("BEGIN IMMEDIATE");\n      return lock;',
                 '      // MUTANT: omit the operation-lock transaction.\n      return lock;'),
    }
    records = {}
    for name, (before, after) in changes.items():
        if core.count(before) != 1:
            raise RuntimeError("Mutation does not have exactly one candidate site: " + name)
        target = root / name / "workbench"
        shutil.copytree(candidate, target)
        # This link exists only in a disposable source fixture, never dist or a
        # shared build output. No build/cleanup command follows this link.
        os.symlink(ROOT / "workbench/node_modules", target / "node_modules", target_is_directory=True)
        changed = core.replace(before, after, 1)
        (target / "src/gates/core.ts").write_text(changed, encoding="utf-8")
        patch = "".join(difflib.unified_diff(core.splitlines(True), changed.splitlines(True),
                      fromfile="candidate/core.ts", tofile=name + "/core.ts"))
        (out / (name + ".patch")).write_text(patch, encoding="utf-8")
        records[name] = {"core": str(target / "src/gates/core.ts"), "patch": name + ".patch"}
    with tarfile.open(out / "sources.tar.gz", "x:gz") as archive:
        archive.add(root, arcname=root.name)
    record = {"task": "T-075-5", "root": str(root), "candidate": str(candidate), "mutants": records,
              "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "dependency_link": str(ROOT / "workbench/node_modules"),
              "scope": "Each gate differs at one site; the final CLI and daemon listener are unchanged."}
    with (out / "manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return out / "manifest.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    if Path(args.label).name != args.label or args.label in (".", ".."):
        parser.error("label must be one new directory name")
    print(prepare(BASE / args.label))


if __name__ == "__main__":
    main()
