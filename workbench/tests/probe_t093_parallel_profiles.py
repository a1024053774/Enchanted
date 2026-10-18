"""Outside-only OS-boundary probe for controller #83. No auth or vendor CLI.

F, U and synthetic controls detach, then exec their own profile exactly once.
Bootstrap execs C, so no unprotected supervisor remains. This probe tests OS
capabilities, not controller_start, forwarding records or model accounting.
"""
import argparse
import ctypes
import errno
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import pwd
import resource
import secrets
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time

SCRIPT = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("parent_probe", SCRIPT.with_name("probe_t093_parent_sandbox.py"))
parent_probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent_probe)


def profile(role, home, root, ports):
    q = lambda path: json.dumps(str(path), ensure_ascii=False)
    common = '(version 1)(allow default)(deny file-write* (subpath ' + q(home) + '))'
    common += '(deny network*)(deny mach-lookup (global-name-regex #".*[Ss]ecurity.*"))'
    if role == "C":
        # Keep the CLI's real-HOME read barrier. Metadata collection runs in U
        # in-process, under U, without giving C new HOME read permissions.
        exceptions = '(subpath ' + q(SCRIPT.parents[1]) + ')(literal ' + q(Path('/opt/homebrew/bin/node').resolve()) + ')'
        return common + '(deny file-read* (require-all (subpath ' + q(home) + ')(require-not (require-any ' + exceptions + '))))' + '(allow network-outbound (remote tcp4 "localhost:' + str(ports["forward_port"]) + '"))'
    if role in ("S", "M"):
        return common + ('(deny file-write* (subpath ' + q(root / "synthetic-home") + '))' if role == "S" else '')
    # F and the test-only U own distinct record directories. Neither can write
    # elsewhere, fork, resolve a DNS name, or choose another listener/peer.
    common += '(deny process-fork)(deny file-write*)(allow file-write* (subpath ' + q(root / role) + '))'
    for port in ([ports["forward_port"]] if role == "F" else [ports["upstream_port"], ports["other_port"]]):
        common += '(allow network-bind network-inbound (local tcp4 "localhost:' + str(port) + '"))'
    if role == "F":
        common += '(allow network-outbound (remote tcp4 "localhost:' + str(ports["upstream_port"]) + '"))'
    return common


def save(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(data, stream, ensure_ascii=True, indent=2)
        stream.write("\n")


def read(path):
    return json.loads(path.read_text())


def wait_file(path, timeout=12):
    until = time.monotonic() + timeout
    while not path.is_file():
        if time.monotonic() > until:
            raise AssertionError("profile_process_result_deadline")
        time.sleep(0.03)
    return read(path)


def connect_denied(port):
    try:
        connection = socket.create_connection(("127.0.0.1", port), timeout=1)
    except OSError as error:
        return {"denied": error.errno in (errno.EPERM, errno.EACCES), "errno": error.errno}
    connection.close()
    return {"denied": False, "errno": None}


def mach_denials():
    # Look up only these service endpoints, without a Keychain operation.
    library = ctypes.CDLL("/usr/lib/libSystem.B.dylib")
    bootstrap = ctypes.c_uint.in_dll(library, "bootstrap_port").value
    result = {}
    for name in ("com.apple.securityd", "com.apple.SecurityServer"):
        port = ctypes.c_uint()
        code = library.bootstrap_look_up(bootstrap, name.encode(), ctypes.byref(port))
        result[name] = int(code)
        if code == 0:
            library.mach_port_deallocate(library.mach_task_self(), port.value)
    return result


def fork_denied():
    try:
        pid = os.fork()
    except OSError as error:
        return {"denied": error.errno in (errno.EPERM, errno.EACCES), "errno": error.errno, "child_pid": None}
    if pid == 0:
        os._exit(0)
    os.waitpid(pid, 0)
    return {"denied": False, "errno": None, "child_pid": pid}


def worker(options, role):
    root, home = Path(options["root"]), Path(options["real_home"])
    directory = root / role
    result = {"pid": os.getpid(), "ppid": os.getppid(), "pgrp": os.getpgrp(), "role": role,
              "profile": role, "real_home_write": parent_probe.attempt(home), "primary_failure": None}
    result["security_lookup"] = mach_denials()
    if role == "U":
        save(directory / "inventory-before.json", local_inventory(options))
    if role in ("S", "M"):
        result["synthetic_write"] = parent_probe.attempt(root / "synthetic-home")
        if not result["synthetic_write"]["denied"] or not result["synthetic_write"]["absent_after"]:
            result["primary_failure"] = {"kind": "AssertionError", "message": "home_write_must_be_denied"}
        save(directory / "result.json", result)
        return 2 if result["primary_failure"] else 0
    result["fork"] = fork_denied()
    if role == "F":
        wait_file(root / "U/ready.json")
        result["unconfigured_upstream"] = connect_denied(options["other_port"])
        result["outside_records_write"] = parent_probe.attempt(root)
    required = [result["real_home_write"]["denied"], result["real_home_write"]["absent_after"],
                result["fork"]["denied"], all(value != 0 for value in result["security_lookup"].values())]
    if role == "F":
        required += [result["unconfigured_upstream"]["denied"], result["outside_records_write"]["denied"],
                     result["outside_records_write"]["absent_after"]]
    save(directory / "preflight.json", result)
    if not all(required):
        return 2
    # exec preserves PID, process group and this exact OS profile. No fork.
    os.execve(options["node"], [options["node"], str(SCRIPT.with_name("t093_profile_endpoint.mjs")),
                              str(root / "options.json"), role], {"PATH": "/usr/bin:/bin", "LANG": "C"})


def local_inventory(options):
    helper = SCRIPT.parents[1] / "src/claudeLoginFiles.py"
    module_spec = importlib.util.spec_from_file_location("private_files", helper)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module.inventory(options["real_home"])


def upstream_after(options):
    root = Path(options["root"])
    result = {"pid": os.getpid(), "ppid": os.getppid(), "pgrp": os.getpgrp(), "profile": "U (exec inherited)",
              "inventory": local_inventory(options), "cli_attempt_paths_absent": []}
    for item in read(root / "C-attempts.json"):
        path = Path(item["path"])
        assert path.parent == Path(options["real_home"]) and path.name.startswith(".a2a-t093-deny-"), "invalid_probe_stat_path"
        result["cli_attempt_paths_absent"].append({"path": str(path), "absent": not os.path.lexists(path)})
    save(root / "U/inventory-after.json", result)
    return 0


def cli_child(options):
    return {"role": "synthetic CLI-chain child", "pid": os.getpid(), "ppid": os.getppid(),
            "pgrp": os.getpgrp(), "profile": "C inherited",
            "real_home_write": parent_probe.attempt(Path(options["real_home"])),
            "upstream_bypass": connect_denied(options["upstream_port"])}


def controller(options):
    root = Path(options["root"])
    result = {"status": "INCOMPLETE", "scope": "OS-boundary probe only; not product-chain acceptance",
              "task": "T-093", "source_revision": options["source_revision"], "profiles": options["profiles"],
              "ports": {key: options[key] for key in ("forward_port", "upstream_port", "other_port", "bind_probe_port")},
              "real_cli_starts": 0, "auth_reads": 0, "real_model_turns": 0, "real_upstream_requests": 0,
              "processes": [{"role": "probe parent after exec", "pid": os.getpid(), "ppid": os.getppid(), "pgrp": os.getpgrp(), "profile": "C"}],
              "bootstrap_processes": [{"role": "initial argument, FD and temporary-root preparation", "pid": os.getpid(), "profile": "pre-exec bootstrap; no auth, network or real HOME writes"},
                  *[{"role": role + " detachment helper then true", "pid": owned["pgrp"],
                     "profile": role + ("; standalone apply; exited before C" if owned["bootstrap_exit"] == 0 else "; apply failed"),
                     "exit": owned["bootstrap_exit"]} for role, owned in options["detached"].items()]],
              "primary_failure": None, "cleanup_failures": [], "inventory": {"pass_condition": False},
              "mutation_limit": "The removed deny rule targets synthetic HOME only. The actual HOME deny rule remains in every profile."}
    before = after = None
    try:
        result["parent_write"] = parent_probe.attempt(Path(options["real_home"]))
        assert result["parent_write"]["denied"] and result["parent_write"]["absent_after"], "parent_home_write_must_be_denied"
        assert all(owned["bootstrap_exit"] == 0 for owned in options["detached"].values()), "outer_profile_compilation_must_succeed"
        for role in ("U", "F"):
            preflight = wait_file(root / role / "preflight.json")
            result[role + "_preflight"] = preflight
            result["processes"].append({key: preflight[key] for key in ("role", "pid", "ppid", "pgrp", "profile")})
            assert preflight["real_home_write"]["denied"] and preflight["real_home_write"]["absent_after"], "endpoint_home_write_must_be_denied"
            assert preflight["fork"]["denied"], "endpoint_fork_must_be_denied"
            assert all(code != 0 for code in preflight["security_lookup"].values()), "security_lookup_must_be_denied"
            ready = wait_file(root / role / "ready.json")
            assert ready["pid"] == preflight["pid"] and ready["ppid"] == 1, "endpoint_must_be_a_separate_protected_process"
        before = wait_file(root / "U/inventory-before.json")
        result["inventory_process"] = {"pid": result["U_preflight"]["pid"], "profile": "U; before Node exec and after Node exec"}
        assert result["F_preflight"]["unconfigured_upstream"]["denied"], "forwarder_unconfigured_upstream_must_be_denied"
        assert result["F_preflight"]["outside_records_write"]["denied"], "forwarder_write_must_stay_in_records"
        result["forwarder_other_listener"] = wait_file(root / "F/bind-probe.json")
        assert result["forwarder_other_listener"]["denied"], "forwarder_other_listener_must_be_denied"
        result["upstream_bypass"] = connect_denied(options["upstream_port"])
        assert result["upstream_bypass"]["denied"], "cli_upstream_bypass_must_be_denied"
        child = subprocess.Popen(["/usr/bin/python3", "-I", "-S", "-B", str(SCRIPT),
                                  "--stage", "cli-child", "--options", str(root / "options.json")],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            out, err = child.communicate(timeout=8)
        except subprocess.TimeoutExpired:
            child.kill(); child.communicate(); raise AssertionError("cli_child_deadline")
        assert child.returncode == 0, "cli_child_must_complete"
        child_result = json.loads(out)
        result["processes"].append({key: child_result[key] for key in ("role", "pid", "ppid", "pgrp", "profile")})
        result["cli_child"] = child_result
        assert child_result["real_home_write"]["denied"] and child_result["real_home_write"]["absent_after"], "cli_child_home_write_must_be_denied"
        assert child_result["upstream_bypass"]["denied"], "cli_child_upstream_bypass_must_be_denied"
        with socket.create_connection(("127.0.0.1", options["forward_port"]), timeout=2) as connection:
            connection.sendall(b"GET /t093-connection-probe HTTP/1.1\r\nHost: local-probe\r\nConnection: close\r\n\r\n")
            data = b""
            while True:
                part = connection.recv(4096)
                if not part: break
                data += part
                assert len(data) < 8192, "local_response_limit"
        assert data.startswith(b"HTTP/1.1 200") and b"local-probe-ok" in data, "allowed_local_path_must_complete"
        result["configured_local_path_completed"] = True
        for role in ("S", "M"):
            item = wait_file(root / role / "result.json")
            result["synthetic_" + role] = item
            result["processes"].append({key: item[key] for key in ("role", "pid", "ppid", "pgrp", "profile")})
            assert item["real_home_write"]["denied"] and item["real_home_write"]["absent_after"], "mutant_must_keep_actual_home_guard"
        base, mutant = result["synthetic_S"], result["synthetic_M"]
        assert base["primary_failure"] is None and base["synthetic_write"]["denied"], "synthetic_control_must_enforce_guard"
        assert mutant["primary_failure"] == {"kind": "AssertionError", "message": "home_write_must_be_denied"}, "missing_guard_must_fail_business_assertion"
        assert all(mutant["synthetic_write"][key] for key in ("created", "deleted", "absent_after")), "mutant_exclusive_creation_must_be_deleted"
        result["synthetic_mutant_rejected"] = True
        result["status"] = "PASS"
    except Exception as error:
        result["primary_failure"] = {"kind": type(error).__name__, "message": str(error) if isinstance(error, AssertionError) else "profile_probe_failed"}
    finally:
        attempts = [result[key] for key in ("parent_write",) if key in result]
        if "cli_child" in result: attempts.append(result["cli_child"]["real_home_write"])
        save(root / "C-attempts.json", attempts)
        result["startup_diagnostics"] = {}
        for role in ("F", "U", "S", "M"):
            error_path = root / role / "startup.stderr"
            if error_path.exists():
                data = error_path.read_bytes()
                result["startup_diagnostics"][role] = {
                    "bytes": len(data), "lines": len(data.splitlines()),
                    "sandbox_exec_error": b"sandbox-exec:" in data,
                    "operation_not_permitted": b"Operation not permitted" in data,
                    "profile_parse_error": b"syntax error" in data or b"unbound variable" in data,
                    "invalid_network_address": b"invalid network address" in data,
                }
        for role in ("F", "U"):
            try:
                save(root / role / "stop", {})
                ready = root / role / "ready.json"
                if ready.exists():
                    result[role + "_closed"] = wait_file(root / role / "closed.json", 3)
                    if role == "U":
                        collected = wait_file(root / "U/inventory-after.json", 8)
                        after = collected["inventory"]
                        result["cli_attempt_paths_absent"] = collected["cli_attempt_paths_absent"]
                        assert all(item["absent"] for item in collected["cli_attempt_paths_absent"]), "cli_probe_files_must_be_absent"
                        result["processes"].append({key: collected[key] for key in ("pid", "ppid", "pgrp", "profile")})
            except AssertionError as error:
                result["status"] = "INCOMPLETE"
                if result["primary_failure"] is None:
                    result["primary_failure"] = {"kind": "AssertionError", "message": str(error)}
            except Exception:
                result["cleanup_failures"].append({"role": role, "message": "endpoint_shutdown_unconfirmed"})
        if result["status"] == "PASS":
            try:
                assert result["F_closed"] == {"received": 1, "forwarded": 1, "deadline_reached": False}, "configured_forward_path_must_complete_once"
                assert result["U_closed"] == {"received": 1, "forwarded": 0, "deadline_reached": False}, "unconfigured_paths_must_not_reach_upstream"
            except (AssertionError, KeyError) as error:
                result["status"] = "INCOMPLETE"
                if result["primary_failure"] is None:
                    result["primary_failure"] = {"kind": type(error).__name__, "message": str(error)}
        for role, owned in options["detached"].items():
            try:
                if os.getpgid(owned["pid"]) == owned["pgrp"]:
                    os.killpg(owned["pgrp"], signal.SIGKILL)
            except ProcessLookupError:
                pass
            except OSError as error:
                result["cleanup_failures"].append({"role": role, "errno": error.errno})
        # Confirm the original owned groups have gone; do not hide a primary
        # business failure behind a later cleanup result.
        for role, owned in options["detached"].items():
            until = time.monotonic() + 3
            while True:
                try:
                    os.killpg(owned["pgrp"], 0)
                except ProcessLookupError:
                    break
                if time.monotonic() > until:
                    result["cleanup_failures"].append({"role": role, "message": "owned_process_group_still_exists"})
                    break
                time.sleep(0.03)
        if after is None:
            result["cleanup_failures"].append({"message": "after_inventory_unavailable"})
        result["inventory"].update({"acceptance_basis": "User decision A; metadata differences are informational.",
            "scope": [".claude", ".claude.json", ".claude.json.backup", "Library/Keychains"],
            "excludes": ["atime", "contents", "symlink targets", "other HOME paths"], "collection_complete": before is not None and after is not None})
        if before is not None and after is not None:
            changed = [path for path in sorted(set(before) | set(after)) if before.get(path) != after.get(path)]
            result["inventory"].update({"before_entries": len(before), "after_entries": len(after), "changed": changed,
                "differences": [{"path": path, "before": before.get(path), "after": after.get(path)} for path in changed]})
        try:
            shutil.rmtree(root)
        except OSError as error:
            result["cleanup_failures"].append({"message": "probe_root_cleanup_failed", "errno": error.errno})
        result["probe_root_removed"] = not root.exists()
        if result["cleanup_failures"]:
            result["status"] = "INCOMPLETE"
        save(Path(options["output"]), result)
    print(json.dumps({"status": result["status"], "primary_failure": result["primary_failure"],
                      "cleanup_failures": result["cleanup_failures"], "output": options["output"]}))
    return 0 if result["status"] == "PASS" else 2


def detach(options_path, role, policy, directory):
    # These two short bootstrap forks only detach and exec. All probe work is
    # after the single outer sandbox-exec. No unprotected daemon remains.
    first = os.fork()
    if first == 0:
        os.setsid()
        second = os.fork()
        if second:
            save(directory / "bootstrap.json", {"pid": second, "pgrp": os.getpgrp()})
            # This short helper also ends under the same explicit profile.
            # It does not supervise the endpoint or leave a background parent.
            for descriptor in (0, 1, 2):
                null = os.open("/dev/null", os.O_RDWR)
                os.dup2(null, descriptor)
                if null > 2: os.close(null)
            os.execve("/usr/bin/sandbox-exec", ["sandbox-exec", "-p", policy, "/usr/bin/true"],
                      {"PATH": "/usr/bin:/bin", "LANG": "C"})
        for descriptor in (0, 1, 2):
            null = os.open(directory / "startup.stderr", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600) if descriptor == 2 else os.open("/dev/null", os.O_RDWR)
            os.dup2(null, descriptor)
            if null > 2: os.close(null)
        os.execve("/usr/bin/sandbox-exec", ["sandbox-exec", "-p", policy, "/usr/bin/python3", "-I", "-S", "-B",
                  str(SCRIPT), "--stage", role, "--options", str(options_path)], {"PATH": "/usr/bin:/bin", "LANG": "C"})
    _, status = os.waitpid(first, 0)
    owned = read(directory / "bootstrap.json") if (directory / "bootstrap.json").exists() else {"pid": first, "pgrp": first}
    owned["bootstrap_exit"] = os.waitstatus_to_exitcode(status)
    return owned


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source-revision")
    parser.add_argument("--stage", choices=("bootstrap", "C", "U", "F", "S", "M", "cli-child", "U-after"), default="bootstrap", help=argparse.SUPPRESS)
    parser.add_argument("--options", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.stage != "bootstrap":
        options = read(args.options)
        if args.stage == "C": return controller(options)
        if args.stage == "U-after": return upstream_after(options)
        if args.stage == "cli-child":
            print(json.dumps(cli_child(options)))
            return 0
        return worker(options, args.stage)
    home = Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
    if not args.output or not args.source_revision or len(args.source_revision) != 40 or any(c not in "0123456789abcdef" for c in args.source_revision):
        parser.error("a new --output and full --source-revision are required")
    output = args.output.resolve()
    if os.path.lexists(output) or not output.parent.is_dir() or Path("/private/tmp") not in output.parents or home in output.parents:
        parser.error("select a new output file under /private/tmp, outside actual HOME")
    for descriptor in (1, 2):
        if stat.S_ISREG(os.fstat(descriptor).st_mode):
            raw = fcntl.fcntl(descriptor, 50, bytes(1024))
            target = Path(os.fsdecode(raw.split(b"\0", 1)[0])).resolve()
            if target == home or home in target.parents:
                os.close(descriptor); os._exit(2)
    limit = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
    if limit == resource.RLIM_INFINITY: parser.error("finite descriptor limit required")
    os.closerange(3, limit)
    null = os.open("/dev/null", os.O_RDONLY)
    os.dup2(null, 0)
    if null: os.close(null)
    if os.getpgrp() != os.getpid(): os.setsid()
    root = Path(tempfile.mkdtemp(prefix="t093-parallel-probe-", dir="/private/tmp")).resolve()
    # Do not bind a socket before C/F/U are applied. Fixed random ports have
    # no fallback: a collision is an INCOMPLETE setup result, never a retry.
    values = set()
    while len(values) != 4: values.add(49152 + secrets.randbelow(16000))
    ports = dict(zip(("forward_port", "upstream_port", "other_port", "bind_probe_port"), sorted(values)))
    options = {"root": str(root), "real_home": str(home), "output": str(output), "node": "/opt/homebrew/bin/node",
               "source_revision": args.source_revision, "python_probe": str(SCRIPT), "deadline_ms": int(time.time() * 1000) + 60_000, **ports, "detached": {}}
    for role in ("F", "U", "S", "M", "synthetic-home"): (root / role).mkdir(mode=0o700)
    options["profiles"] = {role: profile(role, home, root, ports) for role in ("C", "F", "U", "S", "M")}
    options_path = root / "options.json"
    save(options_path, options)
    for role in ("U", "F", "S", "M"):
        options["detached"][role] = detach(options_path, role, options["profiles"][role], root / role)
    # F/U keep reading their immutable initial config. A separate final config
    # avoids truncation races and supplies only C with owned process groups.
    final_options = root / "options-final.json"
    save(final_options, options)
    print(json.dumps({"stage": "entering_C", "probe_root": str(root), "endpoint_deadline_seconds": 60}), flush=True)
    os.execve("/usr/bin/sandbox-exec", ["sandbox-exec", "-p", options["profiles"]["C"], "/usr/bin/python3", "-I", "-S", "-B",
              str(SCRIPT), "--stage", "C", "--options", str(final_options)], {"PATH": "/usr/bin:/bin", "LANG": "C"})


if __name__ == "__main__":
    raise SystemExit(main())
