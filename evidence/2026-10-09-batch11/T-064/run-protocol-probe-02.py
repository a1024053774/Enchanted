import datetime as dt
import json
import os
from pathlib import Path
import subprocess

evidence = Path(__file__).resolve().parent
fork = Path("/Users/luckye/Documents/Code/synara")
root = Path("/Volumes/WD-Elements/dev-cache/synara/instances/s11-t064-protocol02")
root.mkdir(mode=0o700)
for name in ("os-home", "claude-empty"):
    (root / name).mkdir(mode=0o700)
env = {k: v for k, v in os.environ.items() if k in ("PATH", "SHELL", "LANG", "LC_ALL")}
env.update(HOME=str(root / "os-home"), CLAUDE_CONFIG_DIR=str(root / "claude-empty"),
           A2A_SYNARA_SLOT="s11-t064-protocol02", T064_PROBE_ROOT=str(root),
           DISABLE_AUTOUPDATER="1", CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
version = subprocess.run(["/Users/luckye/.local/bin/claude", "--version"], env=env,
                         capture_output=True, text=True, timeout=20)
argv = ["./a2a/scripts/bun", "run", str(evidence / "claude-protocol-probe-02.ts")]
result = subprocess.run(argv, cwd=fork, env=env, capture_output=True, text=True, timeout=35)
record = dict(argv=argv, cwd=str(fork), environment=env, root=str(root),
              created_at=dt.datetime.now(dt.timezone.utc).isoformat(),
              cli_version=dict(returncode=version.returncode, stdout=version.stdout, stderr=version.stderr),
              returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
with (evidence / "claude-protocol-probe-02.json").open("x", encoding="utf-8") as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps(record, ensure_ascii=False, indent=2))
raise SystemExit(result.returncode)
