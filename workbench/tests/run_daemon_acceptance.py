#!/usr/bin/env python3
"""Run the approved T-075-5 probes and retain every isolated fixture.

Use --validation for the full controller handoff, or select a probe/suite.
Each child has its own process, source snapshot, output, and temporary state.
"""
import argparse
import contextlib
import datetime
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from audit_legacy_scope import audit

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "evidence/2026-10-10-batch12/T-075/card-5"
RUNNER = Path(__file__).resolve()
IDENTITY = {
    "runner": "daemon-acceptance", "real_codex_turns": 0,
}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_new(path, value):
    with path.open("x", encoding="utf-8") as out:
        json.dump(value, out, ensure_ascii=False, indent=2)
        out.write("\n")


def observe(argv):
    result = subprocess.run([str(arg) for arg in argv], cwd=ROOT,
                            text=True, capture_output=True)
    return {"argv": [str(arg) for arg in argv], "cwd": str(ROOT),
            "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def clean_fixture_environment():
    # Do not let this worker's launch capability or commit hook reach fixture
    # clients. Original helpers still set their isolated Git configuration.
    for key in list(os.environ):
        if key.startswith("A2A_") or key.startswith("GIT_CONFIG_"):
            del os.environ[key]


def preflight(out):
    observations = [observe(["node", "--version"]), observe(["git", "--version"])]
    assertions_diff = observe(["git", "diff", "a7f4cc3033c16d5888de50d8352da516c941f8e9", "--",
                               "acceptance/test_coop_e2e.py", "acceptance/test_recovery_e2e.py", "acceptance/test_run_e2e.py"])
    problems = []
    if not os.path.ismount("/Volumes/WD-Elements"):
        problems.append("外置盘未挂载；不安装依赖、不回退缓存")
    node = observations[0]
    if node["exit_code"] != 0 or not node["stdout"].strip().startswith("v26.5."):
        problems.append("本轮要求已核对的 Node 26.5 系列")
    try:
        scope = audit(ROOT)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        scope = {'error': str(error)}; problems.append('断言变更超出批准hunk：' + str(error))
    if not problems:
        observations.append(observe(["node", "--input-type=module", "-e",
            "import { spawnHelper } from './workbench/src/panes.ts'; console.log(spawnHelper());"]))
        if observations[-1]["exit_code"] != 0:
            problems.append("已有 node-pty helper 无法加载或执行；不自动修复依赖")
    record = {"observed_at": now(), "volume": "/Volumes/WD-Elements",
              "is_mount": os.path.ismount("/Volumes/WD-Elements"),
              "node_modules": str(ROOT / "workbench/node_modules"),
              "observations": observations, "acceptance_diff": assertions_diff, 'approved_scope': scope,
              "problems": problems}
    write_new(out / "preflight.json", record)
    return record


def snapshot_sources(out):
    paths = sorted((ROOT / "workbench/src").rglob("*.ts"))
    paths += [ROOT / "workbench/tests" / name for name in
              ("daemon_acceptance_adapter.py", "daemon_acceptance_host.ts", "run_daemon_acceptance.py",
               "prepare_daemon_mutants.py", "test_cas_race.py")]
    paths += [ROOT / name for name in
              ("workbench/package.json", "workbench/package-lock.json", "workbench/.npmrc",
               "acceptance/test_coop_e2e.py", "acceptance/test_recovery_e2e.py", "acceptance/test_run_e2e.py",
               "acceptance/pagination_oracle.py", "acceptance/reference/pager.py",
               "acceptance/entry/a2a_gates.py", "acceptance/entry/native-runtime.ts",
               "acceptance/entry/native-entry.py", "acceptance/entry/native-entry.ts",
               "acceptance/entry/thread-boundary.py", "fixtures/pagination/CONTRACT.md",
               "fixtures/pagination/pager.py", ".project-map/specs/recovery-2026-10-06.md",
               ".project-map/specs/managed-delivery-2026-10-06.md",
               ".project-map/specs/supervised-run-2026-10-06.md",
               "evidence/2026-10-10-batch12/T-075/card-5/controller-decision-01.md",
               "evidence/2026-10-10-batch12/T-075/card-5/outside-sandbox.sh",
               "evidence/2026-10-10-batch12/T-075/card-5/readback-timing-probe.py")]
    paths.append(ROOT / "evidence/2026-10-10-batch12/T-075/run-acceptance.py")
    paths += [ROOT / 'workbench/tests' / name for name in ('audit_legacy_scope.py', 'legacy_quality_driver.py',
              'legacy_review_runtime.ts', 'controlled_quality_pty.ts')]
    paths += [ROOT / 'evidence/2026-10-11-batch13/T-076/card-2' / name for name in
              ('controller-decision-03.md', 'legacy-acceptance-hunks.diff')]
    captured = {str(path.relative_to(ROOT)): path.read_bytes() for path in paths}
    with tarfile.open(out / "sources.tar.gz", "x:gz") as archive:
        for name, data in captured.items():
            entry = tarfile.TarInfo(name)
            entry.size = len(data)
            entry.mode = 0o644
            archive.addfile(entry, io.BytesIO(data))
    write_new(out / "source-manifest.json", {"paths": list(captured),
              "head": observe(["git", "rev-parse", "HEAD"]),
              "diff": observe(["git", "diff", "--", "workbench/src/daemon.ts"]),
              "skills": ["project-map", "reality-first-engineering", "evidence-first-testing", "document-writing"]})
    return captured


def read_state(artifacts):
    observations = []
    for artifact in artifacts:
        snapshot = json.loads(Path(artifact["state_readback"]).read_text(encoding="utf-8"))
        if (snapshot["test"] != artifact["test"] or
                snapshot["database"] != str((Path(artifact["state"]) / "state.sqlite3").resolve())):
            raise RuntimeError("Persisted readback belongs to a different fixture")
        observations.append(snapshot)
    return observations


def run_probe(probe, out, suite_name=None, test_name=None, mutant_core=None):
    record = {**IDENTITY, "status": "INCOMPLETE", "probe": probe,
              "started": now(), "argv": sys.argv, "cwd": str(ROOT), "python": sys.version}
    check = preflight(out)
    if check["problems"]:
        record.update({"classification": "preflight-error", "problems": check["problems"], "exit_code": 2})
        write_new(out / "run.json", record)
        print(json.dumps(record, ensure_ascii=False))
        return 2
    sources = snapshot_sources(out)
    artifact_root = Path(tempfile.mkdtemp(prefix="a5-", dir="/tmp"))
    os.environ["COOP_E2E_ARTIFACT_ROOT"] = str(artifact_root)
    os.environ["COOP_E2E_TRACE"] = str(artifact_root / "subprocess-trace.json")
    readbacks = out / "readbacks"
    readbacks.mkdir()
    os.environ["COOP_E2E_READBACK_ROOT"] = str(readbacks.resolve())
    if mutant_core:
        os.environ["COOP_E2E_MUTANT_CORE"] = str(mutant_core)
    else:
        os.environ.pop("COOP_E2E_MUTANT_CORE", None)
    import daemon_acceptance_adapter as adapter
    selections = {
        "coop": (adapter.DaemonDelivery, adapter.delivery.ManagedDeliveryCLI, unittest.TextTestResult),
        "recovery": (adapter.DaemonRecovery, adapter.recovery.RecoveryCLI, adapter.recovery.EvidenceResult),
        "run": (adapter.DaemonRun, adapter.orchestration.RunCLI, adapter.orchestration.EvidenceResult),
        "cas": (adapter.DaemonCAS, adapter.cas.CASRace, adapter.recovery.EvidenceResult),
    }
    focus = {
        "delivery": ("coop", ["test_good_candidate_uses_oracle_snapshot_and_integrates_once"]),
        "recovery": ("recovery", ["test_interrupted_verify_gets_new_id_worktree_and_full_oracle"]),
        "run": ("run", ["test_fixture_existing_dispatch_submit_oracle_integration_and_reclaim",
                        "test_run_entry_point_completes_registered_task"]),
    }
    if suite_name is None:
        suite_name, names = focus[probe]
    cls, original, result_class = selections[suite_name]
    members = [name for name in original.__dict__ if name.startswith("test_")]
    if len(members) != {"coop": 8, "recovery": 9, "run": 18, "cas": 1}[suite_name]:
        raise RuntimeError("Original suite membership differs from the frozen task card")
    if probe is None:
        names = [test_name] if test_name else members
    if any(name not in members for name in names):
        raise RuntimeError("Selected method is not in this original suite")
    for name in names:
        if getattr(cls, name) is not getattr(original, name):
            raise RuntimeError("Probe replaced an original business method: " + name)
    suite = unittest.TestSuite(cls(name) for name in names)
    with (out / "stdout.txt").open("x", encoding="utf-8") as stdout, \
            (out / "stderr.txt").open("x", encoding="utf-8") as stderr:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = unittest.TextTestRunner(verbosity=2, resultclass=result_class, failfast=True).run(suite)
    original_results = (adapter.orchestration.TEST_RESULTS if suite_name == "run" else
                        adapter.recovery.TEST_RESULTS if suite_name in ("recovery", "cas") else [])
    record.update({"finished": now(), "tests_run": result.testsRun,
                   "failures": len(result.failures), "errors": len(result.errors),
                   "skipped": len(result.skipped), "original_results": original_results,
                   "failure_text": [{"test": test.id(), "traceback": text} for test, text in result.failures],
                   "error_text": [{"test": test.id(), "traceback": text} for test, text in result.errors],
                   "selected_original_methods": names,
                   "suite": suite_name, "mutant_core": str(mutant_core) if mutant_core else None,
                   "original_source": str(Path(sys.modules[original.__module__].__file__).relative_to(ROOT)),
                   "entry": str(adapter.ENTRY), "cli": str(adapter.CLI),
                   "runtime_layers": {item["test"]: item.get("evidence_layer", "fixture-setup-incomplete")
                                      for item in adapter.delivery.ARTIFACTS},
                   "artifact_root": str(artifact_root), "commands": adapter.delivery.COMMANDS,
                   "assertions": adapter.recovery.ASSERTIONS, "artifacts": adapter.delivery.ARTIFACTS,
                   "head_after": observe(["git", "rev-parse", "HEAD"]),
                   "limitations": ["受控线程项属于隔离编排证据，不证明真实 PTY、Codex 或 B 转交通道。",
                                    "变异体的测试失败结果照实保存；由协调记录另判反事实是否成立。"]})
    changed = [name for name, data in sources.items()
               if not (ROOT / name).is_file() or (ROOT / name).read_bytes() != data]
    record["changed_source_paths"] = changed
    passed = result.wasSuccessful() and not changed and result.testsRun == len(names) and not result.skipped
    record["test_phase_status"] = "PASS" if passed else "INCOMPLETE"
    # A later collection error must not erase completed test results or fixtures.
    write_new(out / "test-result.json", record)
    with tarfile.open(out / "artifacts.tar.gz", "x:gz") as archive:
        archive.add(artifact_root, arcname=artifact_root.name,
                    filter=lambda item: None if Path(item.name).name.startswith('operator-') and
                    Path(item.name).name.endswith('.credential.json') else item)
    write_new(out / "state-readback.json", read_state(adapter.delivery.ARTIFACTS))
    record["status"] = "PASS" if passed else "INCOMPLETE"
    record["exit_code"] = 0 if passed else 1
    write_new(out / "run.json", record)
    print(json.dumps({key: record[key] for key in
                     ("runner", "probe", "status", "tests_run", "failures", "errors", "exit_code", "artifact_root")},
                     ensure_ascii=False))
    return record["exit_code"]


def run_all(label, out):
    record = {**IDENTITY, "status": "INCOMPLETE", "started": now(),
              "argv": sys.argv, "cwd": str(ROOT), "probes": []}
    code = 0
    for probe in ("delivery", "recovery", "run"):
        child_label = label + "-" + probe
        argv = [sys.executable, "-B", str(RUNNER), "--probe", probe, "--label", child_label,
                "--output-root", str(BASE)]
        result = observe(argv)
        (out / (probe + ".stdout.txt")).write_text(result["stdout"], encoding="utf-8")
        (out / (probe + ".stderr.txt")).write_text(result["stderr"], encoding="utf-8")
        result.update({"probe": probe, "output": str(BASE / child_label)})
        record["probes"].append(result)
        write_new(out / (probe + ".command.json"), result)
        print(result["stdout"], end="")
        if result["exit_code"] != 0:
            code = result["exit_code"]
            break
    record.update({"finished": now(), "status": "PASS" if code == 0 else "INCOMPLETE",
                   "exit_code": code, "stopped_after_failure": code != 0,
                   "scope": "三个探针、四个原测试方法；不是全量验收"})
    write_new(out / "run.json", record)
    return code


def entry_red(output, count):
    record = json.loads((output / "run.json").read_text(encoding="utf-8"))
    checks = list(output.glob("check-*.json"))
    if len(checks) != 1:
        return {"pass": False, "reason": "Original red run did not produce one check record"}
    trace = json.loads(checks[0].read_text(encoding="utf-8"))["trace"]
    calls = [item for item in trace["commands"] if item.get("label", "").startswith("coop:")]
    replies = [json.loads(item["stdout"]) for item in calls]
    passed = (record["exit_code"] == 1 and record["tests_run"] == count and record["errors"] == 0
              and bool(replies) and all(reply.get("ok") is False and reply.get("error") == "daemon_call_failed"
                  and reply.get("details") == "Error: Unix socket path exceeds 103 bytes" for reply in replies))
    return {"pass": passed, "classification": "entry-red-only", "tests_run": record["tests_run"],
            "failures": record["failures"], "errors": record["errors"], "cli_replies": replies}


def business_mutant(output, name, core):
    record = json.loads((output / "run.json").read_text(encoding="utf-8"))
    loaded = [generation.get("host_ready", {}).get("gate")
              for artifact in record["artifacts"] for generation in artifact["daemons"]]
    base = (record["exit_code"] == 1 and record["tests_run"] == 1 and record["failures"] > 0
            and record["errors"] == 0 and bool(loaded) and all(path == str(core) for path in loaded))
    evidence = []
    if name == "fence":
        attempts = [json.loads(item["stdout"])["attempt"] for item in record["commands"]
                    if item.get("label") == "coop:claim" and item.get("exit_code") == 0]
        for item in record["commands"]:
            if item.get("label") != "coop:submit":
                continue
            argv = item["argv"]
            fence = int(argv[argv.index("--fence") + 1])
            session = argv[argv.index("--session") + 1]
            reply = json.loads(item["stdout"])
            if any(fence == attempt["fence"] + 31 and session == attempt["session_id"] for attempt in attempts):
                evidence.append({"submitted_fence": fence, "session": session, "gate_reply": reply})
        rejected_contract = any(item["gate_reply"].get("ok") is True for item in evidence)
    else:
        claims = ({"CAS rejects a changed expected old value", "CAS preserves the external writer reference"}
                  if name == "cas" else {"Live operation excludes concurrent verify",
                      "Live operation excludes concurrent integrate", "Busy commands never start a second oracle"})
        evidence = [item for item in record["assertions"] if item["claim"] in claims and item["pass"] is False]
        rejected_contract = bool(evidence) and any(item.get("classification") == "business-red"
                                                   for item in record["original_results"])
    return {"pass": bool(base and rejected_contract), "classification": "business-counterfactual",
            "mutant_test_status": record["status"], "mutant_test_exit": record["exit_code"],
            "failures": record["failures"], "errors": record["errors"], "loaded_core": loaded,
            "business_evidence": evidence}


def run_validation(label, out):
    record = {**IDENTITY, "status": "INCOMPLETE", "task_status": "INCOMPLETE", "started": now(),
              "argv": sys.argv, "cwd": str(ROOT), "steps": [],
              "scope": "Entry red, full 8/9/18 green, CAS supplement, three business mutants; review is pending."}
    sources = {}

    def step(name, argv, check):
        result = observe(argv)
        (out / (name + ".stdout.txt")).write_text(result["stdout"], encoding="utf-8")
        (out / (name + ".stderr.txt")).write_text(result["stderr"], encoding="utf-8")
        write_new(out / (name + ".command.json"), result)
        verdict = check(result)
        expected_exit = 1 if name.startswith("red-") or name.startswith("mutant-") else 0
        verdict["pass"] = bool(verdict["pass"] and result["exit_code"] == expected_exit)
        record["steps"].append({"name": name, "command": result, "verdict": verdict})
        write_new(out / (name + ".verdict.json"), verdict)
        print(json.dumps({"step": name, "command_exit": result["exit_code"], "verdict": verdict["pass"]}))
        return verdict["pass"]

    def finish(passed):
        changed = [name for name, data in sources.items()
                   if not (ROOT / name).is_file() or (ROOT / name).read_bytes() != data]
        passed = passed and not changed
        record.update({"finished": now(), "status": "PASS" if passed else "INCOMPLETE",
                       "exit_code": 0 if passed else 1, "stopped_after_failure": not passed,
                       "changed_source_paths": changed,
                       "map": observe(["python3", "/Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py",
                                      "status", "--root", "."])})
        write_new(out / "run.json", record)
        return record["exit_code"]

    check = preflight(out)
    if check["problems"]:
        record["preflight_problems"] = check["problems"]
        return finish(False)
    sources = snapshot_sources(out)

    # Use the old unchanged runner and its original transport selections. These
    # failures establish lifecycle red only, never a gate business counterexample.
    for key in ("COOP_SCRIPT", "COOP_NATIVE_ENTRY", "COOP_E2E_MUTANT_CORE"):
        os.environ.pop(key, None)
    for suite, count in (("coop", 8), ("recovery", 9), ("run", 18)):
        child = label + "-red-" + suite
        argv = [sys.executable, "-B", str(ROOT / "evidence/2026-10-10-batch12/T-075/run-acceptance.py"),
                suite, "card-5/" + child]
        if not step("red-" + suite, argv,
                    lambda result, child=child, count=count: entry_red(BASE / child, count)
                    if (BASE / child / "run.json").is_file() else {"pass": False, "reason": "Red receipt missing"}):
            return finish(False)
    for suite in ("coop", "recovery", "run", "cas"):
        child = label + "-green-" + suite
        argv = [sys.executable, "-B", str(RUNNER), "--suite", suite, "--label", child,
                "--output-root", str(BASE)]

        def green_check(result, child=child, suite=suite):
            path = BASE / child / "run.json"
            if not path.is_file():
                return {"pass": False, "reason": "Green receipt missing"}
            data = json.loads(path.read_text(encoding="utf-8"))
            count = {"coop": 8, "recovery": 9, "run": 18, "cas": 1}[suite]
            passed = (result["exit_code"] == 0 and data["status"] == "PASS" and data["tests_run"] == count
                      and data["failures"] == data["errors"] == data["skipped"] == 0)
            if suite == "run":
                layers = list(data["runtime_layers"].values())
                passed = passed and layers.count("default-production-daemon") == 5 and layers.count("isolated-orchestration") == 13
            return {"pass": passed, "tests_run": data["tests_run"], "failures": data["failures"],
                    "errors": data["errors"], "runtime_layers": data["runtime_layers"]}

        if not step("green-" + suite, argv, green_check):
            return finish(False)
    from prepare_daemon_mutants import prepare
    manifest_path = prepare(BASE / (label + "-mutants"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    record["mutant_manifest"] = str(manifest_path)
    cases = (("fence", "coop", "test_identity_gates_and_revocation_reject_old_verified_attempt"),
             ("cas", "cas", "test_external_write_between_read_and_cas_is_preserved"),
             ("lock", "recovery", "test_live_verify_excludes_verify_and_integrate"))
    for name, suite, method in cases:
        child = label + "-mutant-" + name
        argv = [sys.executable, "-B", str(RUNNER), "--suite", suite, "--test", method,
                "--mutant", name, "--mutant-manifest", str(manifest_path), "--label", child,
                "--output-root", str(BASE)]
        core = Path(manifest["mutants"][name]["core"])
        if not step("mutant-" + name, argv,
                    lambda result, child=child, name=name, core=core: business_mutant(BASE / child, name, core)
                    if (BASE / child / "run.json").is_file() else {"pass": False, "reason": "Mutant receipt missing"}):
            return finish(False)
    return finish(True)


def main():
    global BASE, IDENTITY
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--probe", choices=("all", "delivery", "recovery", "run"))
    mode.add_argument("--suite", choices=("coop", "recovery", "run", "cas"))
    mode.add_argument("--validation", action="store_true")
    parser.add_argument("--test")
    parser.add_argument("--mutant", choices=("fence", "cas", "lock", "provenance"))
    parser.add_argument("--mutant-manifest", type=Path)
    parser.add_argument("--label", required=True, help="输出根下尚未存在的证据目录名")
    parser.add_argument("--output-root", type=Path, default=BASE, help="证据根；默认沿用 T-075/card-5")
    parser.add_argument("--output", type=Path, help="单组 suite/probe 的显式新证据目录")
    parser.add_argument("--identity-file", type=Path, help="本次任务的证据身份；不含凭据")
    args = parser.parse_args()
    if args.validation and args.output_root.resolve() != BASE.resolve():
        parser.error('Legacy validation uses its frozen baseline runner; use --suite/--probe for a separate output root')
    BASE = args.output_root.resolve()
    BASE.mkdir(parents=True, exist_ok=True)
    if args.test and not args.suite:
        parser.error("--test requires --suite")
    if args.output and (args.validation or args.probe == 'all'):
        parser.error("--output requires one suite or one focused probe")
    if args.identity_file:
        identity = json.loads(args.identity_file.read_text(encoding='utf-8'))
        if not isinstance(identity, dict) or not identity.get('task') or not identity.get('worker'):
            parser.error("identity file requires task and worker")
        IDENTITY = {**IDENTITY, **identity}
    if (bool(args.mutant) != bool(args.mutant_manifest)) or (args.mutant and not args.suite):
        parser.error("--mutant and --mutant-manifest require each other and --suite")
    if (not args.label or args.label in (".", "..") or
            any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_." for char in args.label)):
        parser.error("label 只能包含字母、数字、点、短横线和下划线")
    out = args.output.resolve() if args.output else BASE / args.label
    out.mkdir(exist_ok=False)
    clean_fixture_environment()
    if args.validation:
        return run_validation(args.label, out)
    if args.probe == "all":
        return run_all(args.label, out)
    core = None
    if args.mutant:
        manifest = json.loads(args.mutant_manifest.read_text(encoding="utf-8"))
        core = Path(manifest["mutants"][args.mutant]["core"])
        if not core.is_file():
            raise RuntimeError("Selected mutant gate module is missing")
    return run_probe(args.probe, out, args.suite, args.test, core)


if __name__ == "__main__":
    raise SystemExit(main())
