"""Save one T-040-A acceptance invocation without changing historical evidence."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

destination = Path(__file__).resolve().parent
root = destination.parents[2]
fork = root.parent / "synara"
label, stage, suite_name = sys.argv[1:]
run = destination / label
run.mkdir()
artifacts = Path(tempfile.mkdtemp(prefix="a2a-t040a-" + label + "-", dir="/tmp"))
baseline = root / "evidence/2026-10-07-synara-batch2/T-037"
recovery = root / "evidence/2026-10-07-synara-batch1/T-036/native-acceptance"
if stage == "baseline":
    suites = {"delivery": root / "acceptance/test_coop_e2e.py",
              "recovery": recovery / "test_recovery_e2e.py",
              "run": baseline / "test_run_native_e2e.py"}
    entry = baseline / "native-entry.py" if suite_name == "run" else root / "acceptance/entry/a2a_gates.py"
else:
    suites = {"delivery": root / "acceptance/test_coop_e2e.py",
              "recovery": root / "acceptance/test_recovery_e2e.py",
              "run": root / "acceptance/test_run_e2e.py"}
    entry = root / "acceptance/entry/native-entry.py" if suite_name == "run" else root / "acceptance/entry/a2a_gates.py"
if stage == "deleted-entry":
    entry = root / "coop.py"
env = dict(os.environ, A2A_SYNARA_SLOT="t040a", COOP_SCRIPT=str(entry),
           COOP_NATIVE_ENTRY=str(fork / "packages/a2a-gates/src/cli.ts"),
           COOP_E2E_ARTIFACT_ROOT=str(artifacts), COOP_E2E_TRACE=str(run / "trace.json"),
           PYTHONPATH=str(root / "acceptance"))
for key in ("A2A_MUTANT_CORE", "A2A_MUTANT_CLI", "A2A_MUTANT_ENTRY", "A2A_TEST_THREAD_CONTROL"):
    env.pop(key, None)
argv = [sys.executable, "-B", str(suites[suite_name]), "--run-suite"]
def revision(path):
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()
versions = {"a2a": revision(root), "fork": revision(fork), "python": sys.version}
assert versions["fork"] == "d3b5bcc61cc212572f38e01139e1b9af2196b820", versions
sources = run / "sources"
sources.mkdir()
for source in {suites[suite_name], entry, root / "acceptance/test_coop_e2e.py",
               recovery / "test_recovery_e2e.py" if stage == "baseline" and suite_name != "delivery"
               else root / "acceptance/test_recovery_e2e.py"}:
    if source.is_file():
        (sources / source.name).write_bytes(source.read_bytes())
native_dir = baseline if stage == "baseline" else root / "acceptance/entry"
if suite_name == "run":
    for name in ("native-entry.py", "native-entry.ts", "native-runtime.ts", "thread-boundary.py"):
        source = native_dir / name
        (sources / name).write_bytes(source.read_bytes())
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
print("START " + label + " " + str(suites[suite_name]), flush=True)
p = subprocess.run(argv, cwd=root, env=env, text=True, capture_output=True)
record = dict(argv=argv, cwd=str(root), stage=stage, suite=suite_name, versions=versions,
              versions_after={"a2a": revision(root), "fork": revision(fork)},
              started=started, finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              environment={k: env[k] for k in ("A2A_SYNARA_SLOT", "COOP_SCRIPT", "COOP_NATIVE_ENTRY",
                  "COOP_E2E_ARTIFACT_ROOT", "COOP_E2E_TRACE", "PYTHONPATH")},
              exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr, artifacts=str(artifacts))
(run / "command.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(run / "stdout.log").write_text(p.stdout, encoding="utf-8")
(run / "stderr.log").write_text(p.stderr, encoding="utf-8")
print(p.stderr, flush=True)
print("RECORD " + str(run / "command.json"), flush=True)
raise SystemExit(p.returncode)
