"""Record an unchanged acceptance suite within this ticket's evidence scope."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil

destination = Path(__file__).resolve().parent
root = destination.parents[2]
label, suite = sys.argv[1:]
run = destination / label
run.mkdir()
artifacts = Path(tempfile.mkdtemp(prefix="a2a-t055-" + label + "-"))
trace = run / "trace.json"
env = dict(os.environ, A2A_SYNARA_SLOT="t055-checks", COOP_SCRIPT=os.environ.get("COOP_SCRIPT", str(root / "acceptance/entry/a2a_gates.py")),
           COOP_E2E_ARTIFACT_ROOT=str(artifacts), COOP_E2E_TRACE=str(trace))
argv = [sys.executable, "-B", str(Path(suite) if Path(suite).is_absolute() else root / "acceptance" / suite), "--run-suite"]
sources = run / "sources"
sources.mkdir()
fork = root.parent / "synara"
for source in (Path(argv[2]), Path(env["COOP_SCRIPT"]), fork / "packages/a2a-gates/src/core.ts",
               fork / "packages/a2a-gates/src/cli.ts", fork / "apps/server/src/a2a/service.ts",
               fork / "apps/server/src/a2a/orchestration.ts", fork / "apps/server/src/a2a/httpRoute.ts", fork / "packages/contracts/src/a2aGates.ts",
               root / "evidence/2026-10-07-synara-batch2/T-037/native-entry.ts", root / "evidence/2026-10-07-synara-batch2/T-037/native-runtime.ts", root / "evidence/2026-10-07-synara-batch2/T-037/thread-boundary.py"):
    shutil.copyfile(source, sources / source.name)
versions = {"fork": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=fork, text=True).strip(),
            "a2a": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()}

started = datetime.datetime.now(datetime.timezone.utc).isoformat()
p = subprocess.run(argv, cwd=root, env=env, text=True, capture_output=True)
record = dict(argv=argv, cwd=str(root), started=started, finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              versions=versions, exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr, artifacts=str(artifacts),
              environment={k: env[k] for k in ("A2A_SYNARA_SLOT", "COOP_SCRIPT", "COOP_E2E_ARTIFACT_ROOT", "COOP_E2E_TRACE", "PYTHONPATH", "COOP_NATIVE_ENTRY", "A2A_MUTANT_ENTRY", "A2A_MUTANT_CORE", "A2A_MUTANT_CLI") if k in env})
with (run / "command.json").open("x", encoding="utf-8") as out:
    json.dump(record, out, ensure_ascii=False, indent=2)
    out.write("\n")
print(json.dumps({"label": label, "exit_code": p.returncode, "record": str(run / "command.json")}))
print(p.stderr[:2400])
sys.exit(p.returncode)
