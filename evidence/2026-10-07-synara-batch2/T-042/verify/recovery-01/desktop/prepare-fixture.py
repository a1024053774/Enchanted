#!/usr/bin/env python3
"""Create a new retained pagination fixture from the independent acceptance inputs."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid

project = Path("/Users/luckye/Documents/Code/a2a")
evidence = Path(__file__).resolve().parent
record = evidence / "fixture.json"
if record.exists():
    raise SystemExit("Fixture already exists; keep its evidence")
parent = Path("/Volumes/WD-Elements/dev-cache/synara/instances/t042-verify-recovery-01/fixtures")
parent.mkdir(parents=True, exist_ok=True)
root = Path(tempfile.mkdtemp(prefix="ui-", dir=str(parent)))
repo = root / "pagination repo"
repo.mkdir()
env = os.environ.copy()
for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_CONFIG_COUNT"):
    env.pop(key, None)
env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_TERMINAL_PROMPT": "0"})
commands = []
def git(*args):
    argv = ["git", "-C", str(repo), *args]
    p = subprocess.run(argv, env=env, text=True, capture_output=True)
    commands.append({"argv": argv, "stdout": p.stdout, "stderr": p.stderr, "exit": p.returncode})
    if p.returncode:
        raise RuntimeError(p.stderr)
    return p.stdout.strip()
git("init")
git("config", "user.name", "T-038 isolated fixture")
git("config", "user.email", "t038@example.invalid")
git("config", "commit.gpgsign", "false")
git("config", "core.logAllRefUpdates", "always")
shutil.copyfile(project / "fixtures/pagination/pager.py", repo / "pager.py")
shutil.copyfile(project / "fixtures/pagination/CONTRACT.md", repo / "CONTRACT.md")
git("add", "--", "pager.py", "CONTRACT.md")
git("commit", "-m", "Independent faulty pagination starter")
base = git("rev-parse", "HEAD")
shutil.copyfile(project / "acceptance/pagination_oracle.py", root / "oracle.py")
shutil.copyfile(project / "fixtures/pagination/CONTRACT.md", root / "instructions.txt")
task = "t042-" + uuid.uuid4().hex[:12]
result = {"root": str(root), "repo": str(repo), "task": task, "project": task,
          "unmanaged_task": task + "-review-notes", "base": base,
          "worker": task + "-worker", "reviewer": task + "-reviewer",
          "oracle": str(root / "oracle.py"), "instructions": str(root / "instructions.txt"),
          "state": "/Volumes/WD-Elements/dev-cache/synara/instances/t042-verify-recovery-01/desktop-home/dev/a2a-gates",
          "commands": commands}
record.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(record.read_text(encoding="utf-8"))
