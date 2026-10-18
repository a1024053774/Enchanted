"""Outside-only probe: real HOME deny-write and inherited/nested profiles.

No vendor CLI, auth, network or ps. Bootstrap replaces itself with sandbox-exec
before probing. All probe children then inherit the real-HOME deny rule.
The rule-removal mutation targets a synthetic HOME only.
"""
import argparse
import errno
import fcntl
import json
import os
from pathlib import Path
import pwd
import resource
import signal
import stat
import subprocess
import sys
import tempfile
import uuid


def profile(home, extra=""):
    return '(version 1)(allow default)(deny file-write* (subpath ' + json.dumps(str(home), ensure_ascii=False) + '))' + extra


def attempt(home):
    path = home / (".a2a-t093-deny-" + uuid.uuid4().hex)
    result = {"path": str(path), "exclusive_create": True, "preexisting": os.path.lexists(path),
              "denied": False, "created": False, "deleted": False, "absent_after": False}
    if result["preexisting"]:
        raise RuntimeError("unique_probe_path_already_exists")
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except OSError as error:
        result["errno"] = error.errno
        result["denied"] = error.errno in (errno.EPERM, errno.EACCES)
    else:
        result["created"] = True
        owned = os.fstat(fd)
        os.close(fd)
        # Delete only this invocation's exclusive creation, never a replacement.
        current = os.lstat(path)
        if (current.st_dev, current.st_ino) != (owned.st_dev, owned.st_ino) or not stat.S_ISREG(current.st_mode):
            raise RuntimeError("probe_file_ownership_changed")
        try:
            os.unlink(path)
            result["deleted"] = True
        except OSError as error:
            result["cleanup_errno"] = error.errno
    result["absent_after"] = not os.path.lexists(path)
    return result


def child(home):
    value = {"pid": os.getpid(), "ppid": os.getppid(), "attempt": attempt(home), "primary_failure": None}
    real_home = Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
    if home.resolve() != real_home:
        value["inherited_real_home_attempt"] = attempt(real_home)
    try:
        if not (value["attempt"]["denied"] and value["attempt"]["absent_after"]):
            raise AssertionError("home_write_must_be_denied")
        if "inherited_real_home_attempt" in value:
            inherited = value["inherited_real_home_attempt"]
            if not (inherited["denied"] and inherited["absent_after"]):
                raise AssertionError("inherited_real_home_write_must_be_denied")
    except AssertionError as error:
        value["primary_failure"] = {"kind": "AssertionError", "message": str(error)}
    print(json.dumps(value), flush=True)
    return 2 if value["primary_failure"] else 0


def captured(arguments, input_json=None):
    try:
        process = subprocess.Popen(arguments, stdin=subprocess.PIPE if input_json is not None else subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    except OSError as error:
        return {"pid": None, "exit": 127, "timed_out": False, "result": None, "spawn_errno": error.errno}
    try:
        out, err = process.communicate(input=json.dumps(input_json).encode() if input_json is not None else None, timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        return {"pid": process.pid, "exit": 124, "timed_out": True, "result": None}
    try:
        result = json.loads(out)
    except ValueError:
        result = None
    # Only output shape/classification is saved; no arbitrary child text.
    return {"pid": process.pid, "exit": process.returncode, "timed_out": False, "result": result,
            "stdout_lines": len(out.splitlines()), "stderr_lines": len(err.splitlines()),
            "sandbox_exec_error": b"sandbox-exec:" in err,
            "operation_not_permitted": b"Operation not permitted" in err}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-revision", help="Caller-supplied frozen source commit; does not run Git.")
    parser.add_argument("--stage", choices=("bootstrap", "parent", "child"), default="bootstrap", help=argparse.SUPPRESS)
    parser.add_argument("--home", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.source_revision and not (len(args.source_revision) == 40 and all(c in "0123456789abcdef" for c in args.source_revision)):
        parser.error("source-revision must be a full commit identity")
    script = str(Path(__file__).resolve())
    if args.stage == "child":
        return child(args.home)
    real_home = Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
    output = args.output.resolve()
    if output.exists() or not output.parent.is_dir() or Path("/private/tmp") not in output.parents or real_home in output.parents:
        parser.error("select a new output path under /private/tmp; real HOME output is forbidden")
    if args.stage == "bootstrap":
        if not Path("/usr/bin/sandbox-exec").is_file():
            parser.error("macOS sandbox-exec required")
        if os.getpgrp() != os.getpid():
            os.setsid()
        # A sandbox does not revoke an already-open writable descriptor. Refuse
        # stdout/stderr files inside real HOME; all other extra FDs close on exec.
        for descriptor in (1, 2):
            if stat.S_ISREG(os.fstat(descriptor).st_mode):
                raw = fcntl.fcntl(descriptor, 50, bytes(1024))  # SDK fcntl.h: F_GETPATH
                target = Path(os.fsdecode(raw.split(b"\0", 1)[0])).resolve()
                if target == real_home or real_home in target.parents:
                    os.close(descriptor)
                    os._exit(2)
        null_input = os.open("/dev/null", os.O_RDONLY)
        if null_input != 0:
            os.dup2(null_input, 0)
            os.close(null_input)
        descriptor_limit = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
        if descriptor_limit == resource.RLIM_INFINITY:
            parser.error("finite descriptor limit required")
        os.closerange(3, descriptor_limit)
        # exec leaves no unprotected probe supervisor behind. Before this point
        # bootstrap only parsed args/read account/descriptor metadata.
        os.execve("/usr/bin/sandbox-exec", ["sandbox-exec", "-p", profile(real_home),
                  "/usr/bin/python3", "-I", "-S", "-B", script, "--output", str(output), "--stage", "parent",
                  *(["--source-revision", args.source_revision] if args.source_revision else [])],
                  {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "C"})
    root = Path(tempfile.mkdtemp(prefix="t093-parent-probe-", dir="/private/tmp")).resolve()
    report = {"status": "INCOMPLETE", "stop_reason": None, "scope": "parent profile compatibility probe only; product not implemented",
              "real_home": str(real_home), "profiles": {"H": profile(real_home)},
              "source_revision": args.source_revision, "revision_source": "caller supplied; run from the frozen worktree",
              "real_cli_starts": 0, "auth_reads": 0, "network_requests": 0, "ps_calls": 0,
              "primary_failure": None, "cleanup_failures": [],
              "processes": [{"role": "probe parent after exec", "pid": os.getpid(), "profile": "H"}]}
    synthetic = root / "synthetic-home"
    synthetic.mkdir(mode=0o700)
    inventory_command = ["/usr/bin/python3", "-I", "-S", "-B", str(Path(script).parents[1] / "src/claudeLoginFiles.py")]
    before = captured(inventory_command, {"operation": "inventory", "home": str(real_home)})
    report["processes"].append({"role": "inventory before helper", "pid": before.get("pid"), "profile": "H inherited"})
    try:
        report["parent_write"] = attempt(real_home)
        if not report["parent_write"]["denied"] or not report["parent_write"]["absent_after"]:
            report["stop_reason"] = "parent_home_write_not_denied"
        else:
            other_restrictions = '(deny network*)(deny mach-lookup (global-name-regex #".*[Ss]ecurity.*"))'
            synthetic_rule = '(deny file-write* (subpath ' + json.dumps(str(synthetic), ensure_ascii=False) + '))'
            inner = profile(real_home, other_restrictions + synthetic_rule)
            report["profiles"]["C"] = inner
            nested = captured(["/usr/bin/sandbox-exec", "-p", inner, "/usr/bin/python3", "-I", "-S", "-B", script,
                               "--output", str(output), "--stage", "child", "--home", str(synthetic)])
            report["nested_profile"] = nested
            report["processes"].append({"role": "nested sandbox-exec / child", "profile": "H inherited + C requested"})
            if nested["exit"] != 0 or not nested["result"]:
                report["stop_reason"] = "nested_profile_did_not_enforce" if nested["result"] else "nested_profile_unavailable"
            else:
                guarded = inner
                mutant_profile = profile(real_home, other_restrictions)
                report["profiles"]["S"] = guarded
                report["profiles"]["M"] = mutant_profile
                baseline = captured(["/usr/bin/sandbox-exec", "-p", guarded, "/usr/bin/python3", "-I", "-S", "-B", script,
                                     "--output", str(output), "--stage", "child", "--home", str(synthetic)])
                mutant = captured(["/usr/bin/sandbox-exec", "-p", mutant_profile, "/usr/bin/python3", "-I", "-S", "-B", script,
                                   "--output", str(output), "--stage", "child", "--home", str(synthetic)])
                report["synthetic_baseline"] = baseline
                report["synthetic_rule_removed"] = mutant
                report["processes"] += [{"role": "synthetic baseline child", "profile": "H inherited + S"},
                                        {"role": "synthetic rule-removal child", "profile": "H inherited + M; real HOME still denied"}]
                attempt_result = (mutant.get("result") or {}).get("attempt", {})
                real_attempt = (mutant.get("result") or {}).get("inherited_real_home_attempt", {})
                failure = (mutant.get("result") or {}).get("primary_failure")
                report["synthetic_mutant_rejected"] = (baseline["exit"] == 0 and mutant["exit"] == 2
                    and failure == {"kind": "AssertionError", "message": "home_write_must_be_denied"}
                    and attempt_result.get("created") and attempt_result.get("deleted") and attempt_result.get("absent_after")
                    and real_attempt.get("denied") and real_attempt.get("absent_after"))
                report["mutation_limit"] = "Synthetic HOME proves the assertion rejects a missing deny rule there; it does not test removing the real HOME rule."
                if report["synthetic_mutant_rejected"]:
                    report["status"] = "PASS"
                else:
                    report["stop_reason"] = "synthetic_mutant_not_rejected_by_business_assertion"
    except Exception as error:
        report["primary_failure"] = {"kind": type(error).__name__, "message": "parent_profile_probe_failed"}
        report["stop_reason"] = "probe_operation_failed"
    finally:
        after = captured(inventory_command, {"operation": "inventory", "home": str(real_home)})
        report["processes"].append({"role": "inventory after helper", "pid": after.get("pid"), "profile": "H inherited"})
        valid = before["exit"] == 0 and after["exit"] == 0 and isinstance(before["result"], dict) and isinstance(after["result"], dict)
        report["inventory"] = {"pass_condition": False,
            "acceptance_basis": "User decision A; main c06a73179 T-093 decision section",
            "scope": [".claude", ".claude.json", ".claude.json.backup", "Library/Keychains"],
            "excludes": ["atime", "contents", "symlink targets", "other HOME paths"], "collection_complete": valid}
        if valid:
            first, last = before["result"], after["result"]
            changed = [path for path in sorted(set(first) | set(last)) if first.get(path) != last.get(path)]
            report["inventory"].update({"before_entries": len(first), "after_entries": len(last), "changed": changed,
                "differences": [{"path": path, "before": first.get(path), "after": last.get(path)} for path in changed]})
        else:
            report["status"] = "INCOMPLETE"
            if report["stop_reason"] is None:
                report["stop_reason"] = "inventory_collection_unavailable"
        for directory in (synthetic, root):
            try:
                directory.rmdir()
            except OSError as error:
                report["cleanup_failures"].append({"path": str(directory), "errno": error.errno})
        report["probe_root_removed"] = not root.exists()
        if report["cleanup_failures"]:
            report["status"] = "INCOMPLETE"
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(report, stream, ensure_ascii=True, indent=2)
            stream.write("\n")
    print(json.dumps({"status": report["status"], "stop_reason": report["stop_reason"], "output": str(output)}))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
