"""Run the unchanged suite against a retained, isolated gate mutant."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

out = Path(__file__).resolve().parent
name, suite, *suffix = sys.argv[1:]
fork = out.parents[2].parent / "synara"
live = Path(tempfile.mkdtemp(prefix="a2a-t036-" + name + "-", dir="/tmp"))
for source in (out / "mutants" / name).glob("*.ts"):
    shutil.copyfile(source, live / source.name)
(live / "node_modules").symlink_to(fork / "packages/a2a-gates/node_modules", target_is_directory=True)
env = dict(os.environ, COOP_SCRIPT=str(out / "mutant-entry.py"), A2A_MUTANT_ENTRY=str(live / "cli.ts"))
label = "mutant-" + name + "-" + suite.removesuffix(".py") + ("-" + suffix[0] if suffix else "")
with (out / (label + "-runtime.json")).open("x", encoding="utf-8") as f:
    json.dump(dict(runtime=str(live), environment={k: env[k] for k in ("COOP_SCRIPT", "A2A_MUTANT_ENTRY")}), f, indent=2)
    f.write("\n")
sys.exit(subprocess.call([sys.executable, "-B", str(out / "run-acceptance.py"), label, suite], env=env))
