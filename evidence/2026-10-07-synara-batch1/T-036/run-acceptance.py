"""Record an unchanged acceptance suite within this ticket's evidence scope."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

destination = Path(__file__).resolve().parent
root = destination.parents[2]
label, suite = sys.argv[1:]
run = destination / label
run.mkdir()
artifacts = Path(tempfile.mkdtemp(prefix="a2a-t036-" + label + "-"))
trace = run / "trace.json"
env = dict(os.environ, A2A_SYNARA_SLOT="t036", COOP_SCRIPT=os.environ.get("COOP_SCRIPT", str(root / "acceptance/entry/a2a_gates.py")),
           COOP_E2E_ARTIFACT_ROOT=str(artifacts), COOP_E2E_TRACE=str(trace))
argv = [sys.executable, "-B", str(root / "acceptance" / suite), "--run-suite"]
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
p = subprocess.run(argv, cwd=root, env=env, text=True, capture_output=True)
record = dict(argv=argv, cwd=str(root), started=started, finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr, artifacts=str(artifacts),
              environment={k: env[k] for k in ("A2A_SYNARA_SLOT", "COOP_SCRIPT", "COOP_E2E_ARTIFACT_ROOT", "COOP_E2E_TRACE", "PYTHONPATH", "COOP_NATIVE_ENTRY", "A2A_MUTANT_ENTRY") if k in env})
with (run / "command.json").open("x", encoding="utf-8") as out:
    json.dump(record, out, ensure_ascii=False, indent=2)
    out.write("\n")
print(json.dumps({"label": label, "exit_code": p.returncode, "record": str(run / "command.json")}))
print(p.stderr[:2400])
sys.exit(p.returncode)
