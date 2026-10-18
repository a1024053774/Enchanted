"""Pure Mach verdicts and an owned Python→Node→Python deadline. No OS profile.

No auth, Security lookup, HOME write, vendor CLI or network. Counterexamples
exercise the actual probe assertion and a missing-timer mutation.
"""
import argparse
import ast
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

SCRIPT = Path(__file__).resolve()
probe_path = SCRIPT.with_name("probe_t093_parallel_profiles.py")
spec = importlib.util.spec_from_file_location("parallel_probe", probe_path)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def timer_child(omit):
    if not omit:
        probe.arm_deadline(int(time.time() * 1000) + 1000)
    # Same exec phases as U. The final Python simulates a stalled metadata walk.
    code = 'process.execve("/usr/bin/python3", ["/usr/bin/python3", "-I", "-S", "-B", "-c", "import time; time.sleep(60)"], {PATH:"/usr/bin:/bin"});'
    os.execve("/opt/homebrew/bin/node", ["node", "--input-type=module", "-e", code], {"PATH": "/usr/bin:/bin"})


def timer_case(omit):
    argv = ["/usr/bin/python3", "-I", "-S", "-B", str(SCRIPT), "--timer-child"]
    if omit: argv.append("--omit-deadline")
    process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    observed = None
    failure = None
    killed_by_cleanup = False
    try:
        try:
            observed = process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass
        try:
            assert observed == -signal.SIGALRM, "detached_phase_must_end_at_hard_deadline"
        except AssertionError as error:
            failure = str(error)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            killed_by_cleanup = True
        out, err = process.communicate(timeout=3)
    return {"omit_deadline": omit, "observed_exit_before_cleanup": observed, "primary_failure": failure,
            "cleanup_killed_owned_group": killed_by_cleanup, "exit_after_cleanup": process.returncode,
            "stdout_bytes": len(out), "stderr_bytes": len(err)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timer-child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--omit-deadline", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.timer_child: return timer_child(args.omit_deadline)
    if not args.output or args.output.exists(): parser.error("select a new output path")
    # Execute the real acceptance predicate with external SDK return-code
    # fixtures. Do not connect to a Mach service or reproduce its rule here.
    tree = ast.parse(probe_path.read_text())
    assertion = next(node for node in ast.walk(tree) if isinstance(node, ast.Assert)
        and isinstance(node.msg, ast.Constant) and node.msg.value == "security_lookup_must_be_denied")
    expression = compile(ast.Expression(assertion.test), str(probe_path), "eval")
    cases = [("permission_denied", {"com.apple.securityd": 1100, "com.apple.SecurityServer": 1100}, True),
             ("service_unavailable", {"com.apple.securityd": 1102, "com.apple.SecurityServer": 1102}, False),
             ("other_failure", {"com.apple.securityd": 5, "com.apple.SecurityServer": 5}, False),
             ("service_available", {"com.apple.securityd": 0, "com.apple.SecurityServer": 0}, False),
             ("empty_results", {}, False),
             ("one_missing_service", {"com.apple.securityd": 1100}, False)]
    checks = []
    for name, values, expected in cases:
        observed = bool(eval(expression, vars(probe) | {"preflight": {"security_lookup": values}}))
        checks.append({"name": name, "expected": expected, "observed": observed, "pass": observed == expected})
    guarded, mutant = timer_case(False), timer_case(True)
    timer_pass = guarded["primary_failure"] is None and guarded["observed_exit_before_cleanup"] == -signal.SIGALRM
    mutant_rejected = mutant["primary_failure"] == "detached_phase_must_end_at_hard_deadline" and mutant["cleanup_killed_owned_group"]
    result = {"status": "PASS" if all(item["pass"] for item in checks) and timer_pass and mutant_rejected else "INCOMPLETE",
              "scope": "Mach predicate and exec deadline only. No sandbox, auth, HOME write, Security lookup or network.",
              "mach_cases": checks, "guarded_timer": guarded, "missing_timer_mutant": mutant,
              "missing_timer_mutant_rejected": mutant_rejected}
    with args.output.open("x") as stream: json.dump(result, stream, indent=2); stream.write("\n")
    print(json.dumps({"status": result["status"], "mach_cases": len(checks), "timer_pass": timer_pass, "mutant_rejected": mutant_rejected}))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__": raise SystemExit(main())
