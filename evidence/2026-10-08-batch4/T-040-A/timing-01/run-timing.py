"""Bounded timing diagnosis through the unchanged gate entry and real lock owner."""
import datetime
import json
import os
from pathlib import Path
import signal
import statistics
import subprocess
import sys
import tarfile
import tempfile
import time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
FORK = ROOT.parent / "synara"
ENTRY = ROOT / "acceptance/entry/a2a_gates.py"

def now():
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)

def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

def revision(repo):
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

def machine(run, label):
    p = subprocess.run(["top", "-l", "2", "-s", "1", "-n", "0"], text=True, capture_output=True)
    save(run / (label + ".json"), dict(argv=["top", "-l", "2", "-s", "1", "-n", "0"],
                                     at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                     exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr))

def stages(events, start, end):
    points = {event["event"]: int(event["ns"]) for event in events}
    points["external_start"] = start
    points["external_end"] = end
    pairs = [
        ("python_start", "external_start", "python_entry_start"),
        ("python_entry", "python_entry_start", "entry_exec"),
        ("launcher_python_start", "entry_exec", "launcher_python_start"),
        ("launcher_checks", "launcher_python_start", "launcher_exec"),
        ("bun_boot_and_observer_load", "launcher_exec", "bun_preload_start"),
        ("observer_setup", "bun_preload_start", "bun_preload_end"),
        ("ts_module_load", "bun_preload_end", "parse_start"),
        ("parse_args", "parse_start", "parse_end"),
        ("request_and_state_prepare", "parse_end", "state_db_open_start"),
        ("state_db_open", "state_db_open_start", "state_db_open_end"),
        ("state_init_and_request_validation", "state_db_open_end", "lock_db_open_start"),
        ("lock_open_and_config", "lock_db_open_start", "lock_begin_start"),
        ("lock_busy_decision", "lock_begin_start", "lock_begin_end"),
        ("rejection_event_and_output_prepare", "lock_begin_end", "stdout_write"),
        ("stdout_and_gate_close", "stdout_write", "bun_exit"),
        ("process_exit_and_observer_flush", "bun_exit", "external_end"),
    ]
    durations = {}
    crossed = None
    for label, left, right in pairs:
        assert start <= points[left] <= points[right] <= end, (label, points)
        durations[label] = (points[right] - points[left]) / 1e6
        if points[left] <= start + 2_000_000_000 < points[right]:
            crossed = label
    durations["state_init_sql"] = (points["state_init_end"] - points["state_init_start"]) / 1e6
    assert abs(sum(durations[k] for k, _, _ in pairs) - (end - start) / 1e6) < 0.000001
    busy = [event for event in events if event["event"] == "lock_begin_end"]
    assert len(busy) == 1 and busy[0]["result"] == "threw" and "locked" in busy[0]["error"]
    return durations, crossed

def main():
    label = sys.argv[1]
    run = OUT / label
    run.mkdir()
    artifacts = Path(tempfile.mkdtemp(prefix="a2a-t040a-timing-" + label + "-", dir="/tmp"))
    fixture_env = dict(os.environ, COOP_SCRIPT=str(ENTRY), A2A_SYNARA_SLOT="t040a-timing",
                       COOP_NATIVE_ENTRY=str(FORK / "packages/a2a-gates/src/cli.ts"),
                       COOP_E2E_ARTIFACT_ROOT=str(artifacts), COOP_E2E_TRACE=str(run / "unused-suite-trace.json"))
    for key in ("BUN_OPTIONS", "NODE_OPTIONS", "A2A_TIMING_ENABLE", "A2A_TIMING_MARKS",
                "A2A_MUTANT_CORE", "A2A_MUTANT_CLI", "A2A_TEST_THREAD_CONTROL"):
        fixture_env.pop(key, None)
    os.environ.update({key: fixture_env[key] for key in ("COOP_SCRIPT", "A2A_SYNARA_SLOT",
        "COOP_NATIVE_ENTRY", "COOP_E2E_ARTIFACT_ROOT", "COOP_E2E_TRACE")})
    sys.path.insert(0, str(ROOT / "acceptance"))
    import test_recovery_e2e as recovery
    import test_coop_e2e as helper

    tracked = ["packages/a2a-gates/src/core.ts", "packages/a2a-gates/src/cli.ts",
               "a2a/scripts/bun", "packages/contracts/src/a2aGates.ts"]
    frozen = {path: (FORK / path).read_bytes() for path in tracked}
    versions = dict(a2a=revision(ROOT), fork=revision(FORK), python=sys.version,
                    logical_cpus=int(subprocess.check_output(["sysctl", "-n", "hw.logicalcpu"], text=True)),
                    bounded_seconds=600, samples_per_condition_per_command=20,
                    paired_uninstrumented_controls=True, artifacts=str(artifacts),
                    started=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save(run / "run-input.json", versions)
    records = []
    cpu_records = []
    load = []
    active_fixture = None
    failure = None

    def check_version():
        assert revision(FORK) == versions["fork"], "Fork revision changed during probe"
        assert all((FORK / path).read_bytes() == value for path, value in frozen.items()), "Fork source changed"

    def stop_load():
        for p, record in load:
            record["stop_started_ns"] = now()
            if p.poll() is None:
                p.terminate()
                record["signal"] = "SIGTERM"
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()
                record["extra_signal"] = "SIGKILL"
                p.wait(timeout=3)
            record["exit_code"] = p.returncode
            record["alive_after"] = p.poll() is None
            record["stopped_ns"] = now()
        load.clear()

    def end_fixture(fixture, original, barrier):
        fixture.release(barrier)
        result = fixture.complete(original)
        assert result.returncode == 0 and json.loads(result.stdout)["ok"] is True, result.stderr
        assert len(fixture.entries(fixture.oracle_control)) == 1, "Busy call started another oracle"
        status = fixture.status()
        assert status["state"] == "verified" and fixture.ref() == fixture.base
        fixture.artifact["timing_final_state"] = status["state"]
        fixture.doCleanups()

    def sample(fixture, original, condition, command, index, instrumented):
        check_version()
        assert original["process"].poll() is None, "Real lock owner ended before sample"
        sample_label = f"{condition}-{command}-{index:02d}-" + ("instrumented" if instrumented else "plain")
        marks = run / (sample_label + ".jsonl")
        env = dict(fixture.env)
        for key in ("BUN_OPTIONS", "NODE_OPTIONS", "A2A_TIMING_ENABLE", "A2A_TIMING_MARKS"):
            env.pop(key, None)
        if instrumented:
            env.update(A2A_TIMING_ENABLE="1", A2A_TIMING_MARKS=str(marks),
                       A2A_TIMING_PY_ENTRY=str(ENTRY), A2A_TIMING_PY_LAUNCHER=str(FORK / "a2a/scripts/bun"),
                       PYTHONPATH=str(OUT / "hooks"), BUN_OPTIONS="--preload " + str(OUT / "hooks/bun-timing.cjs"))
        argv = fixture.cli_argv(command, "--task", fixture.task)
        start = now()
        p = subprocess.Popen(argv, cwd=str(fixture.root), env=env, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        observed_timeout = False
        try:
            stdout, stderr = p.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            observed_timeout = True
            identity = subprocess.run(["ps", "-p", str(p.pid), "-o", "pid=,ppid=,command="],
                                      text=True, capture_output=True)
            save(run / (sample_label + "-timeout-identity.json"), dict(pid=p.pid, stdout=identity.stdout,
                 stderr=identity.stderr, expected_entry=str(FORK / "packages/a2a-gates/src/cli.ts")))
            assert str(FORK / "packages/a2a-gates/src/cli.ts") in identity.stdout and str(fixture.state) in identity.stdout and fixture.task in identity.stdout
            p.kill()
            stdout, stderr = p.communicate(timeout=3)
        end = now()
        events = [json.loads(line) for line in marks.read_text(encoding="utf-8").splitlines()] if marks.exists() else []
        result = dict(label=sample_label, condition=condition, command=command, index=index,
                      instrumented=instrumented, argv=argv, cwd=str(fixture.root), pid=p.pid,
                      state=str(fixture.state), task=fixture.task,
                      owner_pid=original["process"].pid, owner_alive_after=original["process"].poll() is None,
                      start_ns=start, end_ns=end, total_ms=(end-start)/1e6,
                      exceeds_2_seconds=end-start > 2_000_000_000, observation_timeout=observed_timeout,
                      exit_code=p.returncode, stdout=stdout, stderr=stderr, events=events,
                      environment={key:env[key] for key in ("A2A_SYNARA_SLOT", "A2A_TIMING_ENABLE", "PYTHONPATH",
                          "BUN_OPTIONS", "A2A_TIMING_MARKS") if key in env})
        save(run / (sample_label + ".json"), result)
        assert not observed_timeout and p.returncode == 1 and json.loads(stdout)["error"] == "operation_busy", result
        assert result["owner_alive_after"], "Real lock owner ended during sample"
        if instrumented:
            result["stages_ms"], result["threshold_crossing_stage"] = stages(events,start,end)
        records.append(result)
        with (run / "samples.jsonl").open("a",encoding="utf-8") as stream:
            stream.write(json.dumps(result,ensure_ascii=False)+"\n")
        print(f"{sample_label}: {result['total_ms']:.2f}ms operation_busy",flush=True)

    def deadline(signum, frame):
        raise TimeoutError("The authorized 600-second probe bound was reached")

    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(600)
    try:
        for condition in ("idle", "cpu-load"):
            if condition == "cpu-load":
                for index in range(versions["logical_cpus"]):
                    start=now()
                    p=subprocess.Popen(["/usr/bin/yes"],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL,start_new_session=True)
                    record=dict(pid=p.pid,argv=["/usr/bin/yes"],started_ns=start,start_new_session=True)
                    cpu_records.append(record); load.append((p,record))
            machine(run,condition+"-start-machine")
            for batch in range(4):
                fixture = recovery.RecoveryCLI("test_live_verify_excludes_verify_and_integrate")
                fixture.setUp()
                active_fixture = fixture
                fixture.env = dict(fixture_env, **{key:fixture.env[key] for key in
                    ("GIT_CONFIG_NOSYSTEM","GIT_CONFIG_GLOBAL","GIT_TERMINAL_PROMPT","PYTHONDONTWRITEBYTECODE")})
                attempt,candidate = fixture.setup_candidate()
                original=fixture.start_cli("verify","--task",fixture.task)
                barrier=fixture.wait_barrier(fixture.oracle_control,original)
                original_start=now()
                fixture.artifact.update(timing_condition=condition,timing_batch=batch,
                                        timing_owner_pid=original["process"].pid,
                                        timing_attempt=attempt,timing_candidate=candidate)
                for index in range(batch*5+1,batch*5+6):
                    for command in ("verify","integrate"):
                        for instrumented in ((True,False) if index%2 else (False,True)):
                            if (now()-original_start)/1e9 > 35:
                                end_fixture(fixture,original,barrier)
                                active_fixture=None
                                fixture = recovery.RecoveryCLI("test_live_verify_excludes_verify_and_integrate")
                                fixture.setUp(); active_fixture=fixture
                                fixture.env=dict(fixture_env,**{key:fixture.env[key] for key in
                                    ("GIT_CONFIG_NOSYSTEM","GIT_CONFIG_GLOBAL","GIT_TERMINAL_PROMPT","PYTHONDONTWRITEBYTECODE")})
                                attempt,candidate=fixture.setup_candidate()
                                original=fixture.start_cli("verify","--task",fixture.task)
                                barrier=fixture.wait_barrier(fixture.oracle_control,original); original_start=now()
                                fixture.artifact.update(timing_condition=condition,timing_batch=batch,
                                    timing_owner_pid=original["process"].pid,timing_attempt=attempt,timing_candidate=candidate)
                            sample(fixture,original,condition,command,index,instrumented)
                end_fixture(fixture,original,barrier)
                active_fixture=None
                machine(run,condition+f"-batch{batch+1}-machine")
            if condition=="cpu-load": stop_load()
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error))
        raise
    finally:
        signal.alarm(0)
        stop_load()
        if active_fixture is not None: active_fixture.doCleanups()
        save(run/"cpu-load-processes.json",cpu_records)
        save(run/"fixture-trace.json",dict(commands=helper.COMMANDS,artifacts=helper.ARTIFACTS,
                                           assertions=recovery.ASSERTIONS))
        save(run/"completion.json",dict(failure=failure,samples=len(records),
             fork_start=versions["fork"],fork_end=revision(FORK),
             tracked_source_unchanged=all((FORK/path).read_bytes()==value for path,value in frozen.items()),
             finished=datetime.datetime.now(datetime.timezone.utc).isoformat(),
             cpu_children_all_stopped=all(not r.get("alive_after",True) for r in cpu_records)))
        with tarfile.open(run/"retained-fixtures.tar.gz","w:gz",dereference=False) as archive:
            archive.add(artifacts,arcname="fixtures")
        save(run/"retained-fixtures.json",dict(artifacts=str(artifacts),archive="retained-fixtures.tar.gz",
                                              original_retained=True,nested_git_not_staged=True))
    summary=[]
    for condition in ("idle","cpu-load"):
        for command in ("verify","integrate"):
            group=[r for r in records if r["condition"]==condition and r["command"]==command and r["instrumented"]]
            plain=[r for r in records if r["condition"]==condition and r["command"]==command and not r["instrumented"]]
            assert len(group)==len(plain)==20
            measurements={key:dict(median=statistics.median(r["stages_ms"][key] for r in group),
                                   maximum=max(r["stages_ms"][key] for r in group)) for key in group[0]["stages_ms"]}
            summary.append(dict(condition=condition,command=command,samples=20,stages_ms=measurements,
                 instrumented_total_ms=dict(median=statistics.median(r["total_ms"] for r in group),maximum=max(r["total_ms"] for r in group),
                                            exceeds_2_seconds=sum(r["exceeds_2_seconds"] for r in group)),
                 plain_total_ms=dict(median=statistics.median(r["total_ms"] for r in plain),maximum=max(r["total_ms"] for r in plain),
                                     exceeds_2_seconds=sum(r["exceeds_2_seconds"] for r in plain)),
                 crossing_stages=[r["threshold_crossing_stage"] for r in group if r["exceeds_2_seconds"]]))
    save(run/"summary.json",summary)
    print("PROBE FINISHED: "+str(run),flush=True)

if __name__=="__main__":
    main()
