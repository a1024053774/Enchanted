"""Independent T-008 contract checks through CLI, Git and read-only SQLite.

Run: python3 -B acceptance/test_run_e2e.py
COOP_SCRIPT selects a frozen parent or a controller-owned candidate/mutant.
Herdr/Codex substitutes below establish isolated orchestration evidence only.
They do not establish a real Herdr, model, service-tier or reliability claim.
"""
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
import uuid

import test_coop_e2e as helper
import test_recovery_e2e as recovery


ROOT = helper.ROOT
SCRIPT = helper.SCRIPT
EVIDENCE = ROOT / "evidence/2026-10-06-run-01"
CONTRACT = ROOT / ".project-map/specs/supervised-run-2026-10-06.md"
COMMANDS = helper.COMMANDS
ARTIFACTS = helper.ARTIFACTS
ASSERTIONS = recovery.ASSERTIONS
TEST_RESULTS = []
write_new = recovery.write_new


class ContractMissing(AssertionError):
    """The requested new CLI contract is absent, not an old product defect."""


class RunCLI(recovery.RecoveryCLI):
    def setUp(self):
        super().setUp()
        # Use the independent frozen pagination oracle without a barrier unless
        # a particular test explicitly controls it.
        (self.oracle_control / "release-all").write_text("continue", encoding="utf-8")

    def new_result(self, process, command, ok=True, error=None):
        missing = process.returncode == 2 and (
            (command == "run" and "invalid choice: 'run'" in process.stderr) or
            (command in ("verify", "integrate", "reclaim") and
             "unrecognized arguments: --attempt" in process.stderr))
        if missing:
            ASSERTIONS.append({"test": self.id(), "claim": "New CLI contract exists",
                               "expected": command + " contract", "observed": process.stderr,
                               "pass": False, "classification": "expected-contract-red"})
            raise ContractMissing("EXPECTED_CONTRACT_RED new command/guard missing: " + command)
        return self.cli_result(process, ok=ok, error=error,
                               claim="Frozen CLI result for " + command)

    def test_run_entry_point_completes_registered_task(self):
        self.create()
        before = self.snapshot("before-new-run")
        p = self.process(self.cli_argv("run", "--task", self.task,
                                     "--parent-pane", "wcheck:p1", "--name", "check-run",
                                     "--wait-seconds", "1"), label="coop:run")
        if p.returncode == 2:
            after = self.snapshot("after-missing-run")
            self.check(before["status"] == after["status"] and before["refs"] == after["refs"],
                       "Missing run cannot change business state or Git", before["status"],
                       after["status"])
        self.new_result(p, "run")
        self.finish_checks()

    def test_verify_expected_attempt_uses_real_gate(self):
        attempt, candidate = self.setup_candidate()
        before = self.snapshot("before-new-verify-guard")
        p = self.process(self.cli_argv("verify", "--task", self.task,
                                     "--attempt", attempt["attempt_id"]), label="coop:verify-guard")
        if p.returncode == 2:
            after = self.snapshot("after-missing-verify-guard")
            self.check(before["status"] == after["status"] and before["refs"] == after["refs"],
                       "Missing guard cannot verify or change Git", before["status"], after["status"])
        self.new_result(p, "verify")
        self.check(self.ref() == self.base, "Verify never integrates", self.base, self.ref())
        self.check(self.status()["state"] == "verified", "Matching guard permits verification",
                   "verified", self.status()["state"])
        self.finish_checks()


class EvidenceResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        TEST_RESULTS.append({"test": test.id(), "status": "PASS"})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        category = ("expected-contract-red" if issubclass(err[0], ContractMissing) else
                    "business-red" if test.business_failures else "fixture-error")
        TEST_RESULTS.append({"test": test.id(), "status": "INCOMPLETE", "classification": category,
                             "traceback": self._exc_info_to_string(err, test)})

    def addError(self, test, err):
        super().addError(test, err)
        TEST_RESULTS.append({"test": test.id(), "status": "INCOMPLETE",
                             "classification": "fixture-error",
                             "traceback": self._exc_info_to_string(err, test)})


def run_suite():
    names = [name for name in RunCLI.__dict__ if name.startswith("test_")]
    suite = unittest.TestSuite(RunCLI(name) for name in names)
    result = unittest.TextTestRunner(verbosity=2, resultclass=EvidenceResult).run(suite)
    write_new(os.environ["COOP_E2E_TRACE"], {
        "results": TEST_RESULTS, "assertions": ASSERTIONS, "artifacts": ARTIFACTS,
        "commands": COMMANDS, "tests_run": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors)})
    return 0 if result.wasSuccessful() else 1


def main():
    if sys.argv[1:] == ["--run-suite"]:
        return run_suite()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    stem = "check-" + stamp + "-" + uuid.uuid4().hex[:8]
    evidence_path = EVIDENCE / (stem + ".json")
    artifact_root = EVIDENCE / (stem + "-artifacts")
    artifact_root.mkdir(exist_ok=False)
    for source, name in ((Path(__file__), "run-acceptance-source.py"),
                         (Path(helper.__file__), "managed-helper-source.py"),
                         (Path(recovery.__file__), "recovery-helper-source.py"),
                         (CONTRACT, "run-contract.md"), (SCRIPT, "selected-entry-point.py")):
        shutil.copyfile(source, artifact_root / name)
    trace_path = artifact_root / "subprocess-trace.json"
    env = dict(os.environ, COOP_E2E_ARTIFACT_ROOT=str(artifact_root), COOP_E2E_TRACE=str(trace_path))
    argv = [sys.executable, "-B", str(Path(__file__).resolve()), "--run-suite"]
    started = helper.utc_now()
    p = subprocess.run(argv, cwd=str(ROOT), env=env, text=True, capture_output=True)
    trace = json.loads(trace_path.read_text(encoding="utf-8")) if trace_path.is_file() else None
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True, capture_output=True)
    write_new(evidence_path, {
        "role": "run-check", "ticket": "T-008", "contract": str(CONTRACT.relative_to(ROOT)),
        "status": "PASS" if p.returncode == 0 else "INCOMPLETE",
        "started": started, "finished": helper.utc_now(),
        "command": ["python3", "-B", "acceptance/test_run_e2e.py"], "actual_command": argv,
        "COOP_SCRIPT": str(SCRIPT), "cwd": str(ROOT), "repository_head": head.stdout.strip(),
        "python": sys.version, "real_git": recovery.REAL_GIT, "exit_code": p.returncode,
        "stdout": p.stdout, "stderr": p.stderr, "artifact_root": str(artifact_root),
        "trace_path": str(trace_path), "trace": trace,
        "independence": "Frozen contract; no product import or source-derived expected values. "
                        "Real CLI subprocesses, real Git and read-only SQLite observations.",
        "limitations": ["Isolated orchestration only; real Herdr/Codex run is controller-owned.",
                        "New-command expected-red is not evidence of an old defect.",
                        "Counterfactual, candidate approval and ticket closure are controller-owned."]})
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    print("Acceptance evidence: " + str(evidence_path))
    print("Retained isolated artifacts: " + str(artifact_root))
    return p.returncode


if __name__ == "__main__":
    sys.exit(main())
