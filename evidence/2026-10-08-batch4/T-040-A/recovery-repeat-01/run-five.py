"""Run the unchanged nine recovery cases five times; stop at the first failure."""
import datetime
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
FORK = ROOT.parent / "synara"

def timestamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def clock():
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)

def write(path, data):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def revision(repo):
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

def snapshot(directory, label):
    commands = [["top", "-l", "2", "-s", "1", "-n", "0"],
                ["ps", "-axo", "pid,ppid,pcpu,etime,comm"],
                ["df", "-h", str(ROOT), "/Volumes/WD-Elements"]]
    results = []
    for argv in commands:
        p = subprocess.run(argv, text=True, capture_output=True)
        results.append(dict(argv=argv, at=timestamp(), exit_code=p.returncode,
                            stdout=p.stdout, stderr=p.stderr))
    write(directory / (label + ".json"), results)
    idle = re.findall(r"([0-9.]+)% idle", results[0]["stdout"])
    heavy = []
    for line in results[1]["stdout"].splitlines()[1:]:
        values = line.strip().split(None, 4)
        if len(values) == 5 and float(values[2]) >= 100 and int(values[0]) != os.getpid():
            heavy.append(dict(pid=int(values[0]), CPU_percent=float(values[2]), comm=values[4]))
    return dict(interval_CPU_idle_percent=float(idle[-1]) if idle else None,
                heavy_processes=heavy,
                eligible=all(p["exit_code"] == 0 for p in results) and bool(idle)
                    and float(idle[-1]) >= 70 and not heavy)

def main():
    label = sys.argv[1]
    destination = OUT / label
    destination.mkdir()
    fork_revision = revision(FORK)
    assert fork_revision == "28e2f1b4ca6634d4faba9bd921a55a51640407e4"
    sources = {}
    for base, names in [(ROOT, ["acceptance/test_coop_e2e.py", "acceptance/test_recovery_e2e.py",
            "acceptance/entry/a2a_gates.py", "acceptance/pagination_oracle.py", "acceptance/reference/pager.py",
            "fixtures/pagination/pager.py", "fixtures/pagination/CONTRACT.md", ".project-map/specs/recovery-2026-10-06.md"]),
        (FORK, ["packages/a2a-gates/src/core.ts", "packages/a2a-gates/src/cli.ts", "a2a/scripts/bun",
            "packages/contracts/src/a2aGates.ts", "packages/contracts/src/index.ts", "bun.lock"])]:
        for name in names:
            sources[base / name] = (base / name).read_bytes()
    def unchanged():
        return revision(FORK) == fork_revision and all(path.read_bytes() == data for path, data in sources.items())
    write(destination / "run-input.json", dict(command=[sys.executable, "-B", str(Path(__file__)), label],
          cwd=str(ROOT), started=timestamp(), a2a=revision(ROOT), fork=fork_revision,
          code_candidate="1279adb73c06308fc71eebf35002628730f320d5", planned_rounds=5,
          suite="acceptance/test_recovery_e2e.py", tests_per_round=9,
          failure_policy="Stop immediately; preserve the failed round; do not retry",
          instrumentation="none; original 2-second assertions remain", python=sys.version))
    rows = []
    for index in range(1, 6):
        assert unchanged(), "Candidate changed before round"
        run = destination / f"round-{index:02d}"
        run.mkdir()
        before = snapshot(run, "machine-before")
        write(run / "workload-before-qualification.json", before)
        if not before["eligible"]:
            write(destination / "summary.json", dict(status="INCOMPLETE", completed_rounds=len(rows),
                rounds=rows, stopped_before_round=index, reason="other heavy workload; do not start another test",
                workload=before))
            return 1
        artifacts = Path(tempfile.mkdtemp(prefix=f"a2a-t040a-recovery-{label}-{index:02d}-", dir="/tmp"))
        env = dict(os.environ, A2A_SYNARA_SLOT="t040a", COOP_SCRIPT=str(ROOT / "acceptance/entry/a2a_gates.py"),
                   COOP_NATIVE_ENTRY=str(FORK / "packages/a2a-gates/src/cli.ts"),
                   COOP_E2E_ARTIFACT_ROOT=str(artifacts), COOP_E2E_TRACE=str(run / "trace.json"),
                   PYTHONPATH=str(ROOT / "acceptance"))
        removed = []
        for key in ("A2A_TIMING_ENABLE", "A2A_TIMING_MARKS", "A2A_TIMING_PY_ENTRY", "A2A_TIMING_PY_LAUNCHER",
                    "BUN_OPTIONS", "NODE_OPTIONS", "A2A_MUTANT_CORE", "A2A_MUTANT_CLI", "A2A_TEST_THREAD_CONTROL"):
            if key in env:
                removed.append(key)
                env.pop(key)
        argv = [sys.executable, "-B", str(ROOT / "acceptance/test_recovery_e2e.py"), "--run-suite"]
        print(f"START round {index}/5", flush=True)
        started = timestamp()
        start_ns = clock()
        p = subprocess.run(argv, cwd=ROOT, env=env, text=True, capture_output=True)
        end_ns = clock()
        finished = timestamp()
        record = dict(argv=argv, cwd=str(ROOT), started=started, finished=finished,
              external_start_ns=start_ns, external_end_ns=end_ns, elapsed_seconds=(end_ns-start_ns)/1e9,
              versions=dict(a2a=revision(ROOT), fork=revision(FORK)), candidate_unchanged=unchanged(),
              environment={key:env[key] for key in ("A2A_SYNARA_SLOT", "COOP_SCRIPT", "COOP_NATIVE_ENTRY",
                  "COOP_E2E_ARTIFACT_ROOT", "COOP_E2E_TRACE", "PYTHONPATH")},
              removed_observer_and_mutant_variables=removed, exit_code=p.returncode,
              stdout=p.stdout, stderr=p.stderr, artifacts=str(artifacts))
        write(run / "command.json", record)
        (run / "stdout.log").write_text(p.stdout, encoding="utf-8")
        (run / "stderr.log").write_text(p.stderr, encoding="utf-8")
        after = snapshot(run, "machine-after")
        write(run / "workload-after-qualification.json", after)
        with tarfile.open(run / "retained-fixtures.tar.gz", "w:gz", dereference=False) as archive:
            archive.add(artifacts, arcname="fixtures")
        write(run / "retained-fixtures.json", dict(original_path=str(artifacts), original_preserved=True,
                                                  archive="retained-fixtures.tar.gz", nested_git_not_staged=True))
        trace = json.loads((run / "trace.json").read_text(encoding="utf-8")) if (run / "trace.json").exists() else None
        business_passed = (p.returncode == 0 and record["candidate_unchanged"] and trace is not None
                  and trace["tests_run"] == 9 and trace["failures"] == 0 and trace["errors"] == 0
                  and len(trace["results"]) == 9 and all(item["status"] == "PASS" for item in trace["results"]))
        passed = business_passed and after["eligible"]
        row = dict(round=index, passed=passed, exit_code=p.returncode,
                   tests_run=trace["tests_run"] if trace else None,
                   failures=trace["failures"] if trace else None, errors=trace["errors"] if trace else None,
                   business_passed=business_passed, workload_eligible=after["eligible"],
                   elapsed_seconds=record["elapsed_seconds"], command=str(run / "command.json"),
                   fork=record["versions"]["fork"], candidate_unchanged=record["candidate_unchanged"])
        rows.append(row)
        with (destination / "round-results.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(p.stderr, flush=True)
        print(f"END round {index}: " + ("PASS" if passed else "INCOMPLETE"), flush=True)
        if not passed:
            write(destination / "summary.json", dict(status="INCOMPLETE", completed_rounds=len(rows),
                failed_round=index, rounds=rows, decision="stop and return to controller", prior_failure_unchanged=True))
            return 1
    write(destination / "summary.json", dict(status="PASS", completed_rounds=5, passed_tests=45,
        rounds=rows, fork=fork_revision, candidate_unchanged=unchanged(),
        acceptance_basis="controller-decision-02.md section 2: accept with known unreproduced timeout",
        prior_failure_unchanged=True, prior_independent_review_unchanged=True, root_cause="unknown"))
    print("FIVE ROUNDS PASS: " + str(destination), flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
