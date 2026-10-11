"""Fixture regression: retain literal SQLite rows after shutdown and root move.

Failure modes: reading a closed WAL database can fail; the original temporary
root can disappear before collection. Exercise the adapter's stop ordering and
the runner's collection without a daemon, socket, Git repository, or model.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sqlite3
import sys
import tempfile
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "workbench/tests"))
import daemon_acceptance_adapter as adapter
import run_daemon_acceptance as runner


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    if Path(args.label).name != args.label or args.label in (".", ".."):
        parser.error("label must be one new directory name")
    out = BASE / args.label
    out.mkdir(exist_ok=False)
    readbacks = out / "readbacks"
    readbacks.mkdir()
    os.environ["COOP_E2E_READBACK_ROOT"] = str(readbacks.resolve())
    root = Path(tempfile.mkdtemp(prefix="a5-readback-", dir="/tmp"))
    state = root / "isolated state"
    state.mkdir()
    database = state / "state.sqlite3"
    source = """import { DatabaseSync } from 'node:sqlite';
const db = new DatabaseSync(process.argv[2]);
db.exec("PRAGMA journal_mode=WAL; CREATE TABLE independent_values(id INTEGER,value TEXT); INSERT INTO independent_values VALUES(7,'snapshot survives cleanup');");
process.stdout.write('ready\\n');
process.stdin.once('data', () => { db.close(); process.exit(0); });
"""
    writer = out / "writer.mjs"
    writer.write_text(source, encoding="utf-8")
    process = subprocess.Popen(["node", str(writer.resolve()), str(database.resolve())],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True)
    (out / "writer-launch.json").write_text(json.dumps({"pid": process.pid,
        "argv": process.args, "database": str(database)}, indent=2) + "\n", encoding="utf-8")
    if process.stdout.readline() != "ready\n":
        raise RuntimeError("Isolated SQLite writer did not become ready")
    artifact = {"test": "readback-timing-fixture", "root": str(root), "state": str(state)}
    lifecycle = []

    def inspect_owned(record):
        if process.poll() is not None:
            raise RuntimeError("Writer closed before the adapter stop operation")

    def stop(command):
        if command != "daemon_stop":
            raise RuntimeError("Unexpected fixture lifecycle command: " + command)
        process.stdin.write("close\n")
        process.stdin.flush()
        process.wait(timeout=5)
        if process.returncode != 0:
            raise RuntimeError("Isolated writer failed to close")

    def wait_exit(record):
        record["process_exit"] = process.wait(timeout=5)

    fixture = SimpleNamespace(root=root, state=state, artifact=artifact,
                              active_daemon={"pid": process.pid, "generation": 1},
                              inspect_owned=inspect_owned, daemon_command=stop, wait_exit=wait_exit,
                              lifecycle=lambda event, **value: lifecycle.append({"event": event, **value}))
    fixture.capture_state = lambda record: adapter.DaemonLifecycle.capture_state(fixture, record)
    # The adapter's real stop method decides when the snapshot is taken.
    adapter.DaemonLifecycle.stop_daemon(fixture)
    failures = []
    observations = []
    expected = [{"id": 7, "value": "snapshot survives cleanup"}]
    for phase in ("after-close", "after-root-move"):
        if phase == "after-root-move":
            retained = root.with_name(root.name + "-retained")
            root.rename(retained)
        try:
            observed = runner.read_state([artifact])
            rows = observed[0].get("tables", {}).get("independent_values")
            if rows != expected:
                raise AssertionError({"expected": expected, "observed": rows})
            observations.append({"phase": phase, "status": "PASS", "readback": observed})
        except (AssertionError, OSError, RuntimeError, sqlite3.Error) as exc:
            failures.append({"phase": phase, "type": type(exc).__name__, "message": str(exc)})
    record = {"task": "T-075-5", "status": "PASS" if not failures else "INCOMPLETE",
              "classification": "fixture-readback-regression", "argv": sys.argv,
              "expected_rows": expected, "observations": observations, "failures": failures,
              "artifact": artifact, "retained_root": str(retained), "lifecycle": lifecycle,
              "writer_exit": process.returncode, "writer_stderr": process.stderr.read(),
              "real_daemon_run": False, "real_codex_turns": 0}
    with (out / "run.json").open("x", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
