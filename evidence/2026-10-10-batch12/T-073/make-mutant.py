#!/usr/bin/env python3
"""Copy the candidate into an isolated Git fixture; omit one required trailer."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

repo = Path(__file__).resolve().parents[3]
target = Path(sys.argv[1]).resolve()
target.mkdir()
shutil.copytree(repo / "scripts", target / "scripts", symlinks=True)
hook = target / "scripts/git-hooks/hook.py"
text = hook.read_text(encoding="utf-8")
assert '"A2A-Effort": row["effort"],' in text
hook.write_text(text.replace('"A2A-Effort": row["effort"],', ''), encoding="utf-8")
env = dict(os.environ, GIT_AUTHOR_NAME="mutant", GIT_AUTHOR_EMAIL="mutant@example.invalid",
           GIT_COMMITTER_NAME="mutant", GIT_COMMITTER_EMAIL="mutant@example.invalid")
for argv in (["git", "init", "-q", str(target)], ["git", "-C", str(target), "add", "scripts"],
             ["git", "-C", str(target), "commit", "-qm", "explicit missing-effort mutant"]):
    subprocess.run(argv, env=env, check=True)
print(json.dumps(dict(mutant=str(target), mutation="omit A2A-Effort", source=str(repo))))
