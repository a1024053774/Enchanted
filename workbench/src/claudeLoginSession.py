"""Prepare auth once, start independent F/D profiles, then exec the C root.

All session data must be outside the OS account HOME. No DNS lookup, fallback,
vendor turn, or global setting is performed. The caller supplies one pinned
IPv4 peer for the configured URL. TLS still checks that URL's hostname.
F's OS policy restricts ports only; the forwarder enforces the configured host.
"""
import sys
sys.dont_write_bytecode = True


def require_safe_python():
    if not (sys.flags.isolated and sys.flags.no_site and sys.flags.dont_write_bytecode):
        raise ValueError("python_isolated_no_site_no_bytecode_required")


if __name__ == "__main__":
    try:
        require_safe_python()
    except ValueError:
        sys.stderr.write("python_isolated_no_site_no_bytecode_required\n")
        raise SystemExit(2)

import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import pwd
import resource
import re
import shutil
import signal
import socket
import stat
import subprocess
import tempfile
import time
import unicodedata
import uuid
from urllib.parse import urlsplit

SOURCE = Path(__file__).resolve().parent
NODE = "/opt/homebrew/bin/node"
_spec = importlib.util.spec_from_file_location("claude_login_files", SOURCE / "claudeLoginFiles.py")
_files = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_files)
inventory, read_auth = _files.inventory, _files.read_auth


def save(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.pending-' + uuid.uuid4().hex)
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, ensure_ascii=True)
            stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
        os.link(temporary, path, follow_symlinks=False)
    finally:
        temporary.unlink()


def read(path):
    return json.loads(Path(path).read_text())


def arm_deadline(deadline):
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, deadline - time.time()))


def outside_home(path, home):
    resolved = Path(path).resolve()
    if resolved == home or home in resolved.parents:
        raise ValueError("session_data_must_be_outside_real_home")
    return resolved


def home_read_barrier(home, readable):
    q = lambda value: json.dumps(str(value), ensure_ascii=False)
    exceptions = ' '.join('(' + kind + ' ' + q(path) + ')' for kind, path in readable)
    rule = '(deny file-read* (require-all (subpath ' + q(home) + ')(require-not (require-any ' + exceptions + '))))'
    # Node realpath walks the ancestors of each permitted entry/dependency.
    # Exact metadata exceptions do not permit directory enumeration or data.
    ancestors = sorted({parent for _, path in readable for parent in Path(path).parents}, key=str)
    rule += '(allow file-read-metadata ' + ' '.join('(literal ' + q(path) + ')' for path in ancestors) + ')'
    return rule


def policies(session):
    q = lambda value: json.dumps(str(value), ensure_ascii=False)
    home, private = session["real_home"], session["private_root"]
    source = SOURCE.parent.resolve()
    read_barrier = home_read_barrier(home, [('subpath', source), ('subpath', (source / 'node_modules').resolve()),
                                          ('literal', Path(NODE).resolve()), ('literal', Path(session['manifest']['executable']).resolve())])
    source_barrier = ''
    if session["credential_home"] != home:
        source_barrier = '(deny file-read* file-write* (subpath ' + q(session["credential_home"]) + '))'
    common = '(version 1)(allow default)(deny file-write* (subpath ' + q(home) + '))(deny network*)(deny mach-lookup (global-name-regex #".*[Ss]ecurity.*"))'
    port = session["forward_port"]
    upstream_port = session["upstream_port"]
    if type(upstream_port) is not int or not 1 <= upstream_port <= 65535:
        raise ValueError("invalid_upstream_port")
    socket_path = str(Path(session["manifest"]["state"]) / "control.sock")
    c = common + read_barrier + source_barrier
    c += '(allow network-outbound (remote tcp4 "localhost:' + str(port) + '"))'
    c += '(allow network-outbound (remote unix-socket (path-literal ' + q(socket_path) + ')))'
    c += '(allow network-bind network-inbound (literal ' + q(socket_path) + '))'
    f = common + read_barrier + source_barrier + '(deny process-fork)(deny file-write*)(allow file-write* (subpath ' + q(session["forwarder_directory"]) + '))'
    f += '(allow network-bind network-inbound (local tcp4 "localhost:' + str(port) + '"))'
    # macOS accepts * or localhost, not numeric remote-host filters.
    # Production fixes this port to 443. The no-model chain supplies its local
    # test port to this same generator; every other rule stays identical.
    f += '(allow network-outbound (remote tcp4 "*:' + str(upstream_port) + '"))'
    # D reads directories/stat in the four approved scopes, never HOME file
    # bodies (except this program's source). Its private snapshots are removed
    # with the isolated HOME, before facts can be considered complete.
    d = common + '(deny process-fork)(deny file-write*)(allow file-write* (subpath ' + q(private) + '))(allow file-write* (subpath ' + q(session["metadata_directory"]) + '))'
    d += '(deny file-read-data (require-all (subpath ' + q(home) + ')(require-not (vnode-type DIRECTORY))(require-not (subpath ' + q(source) + '))))'
    d += source_barrier
    return {"C": c, "F": f, "D": d}


def prepare(manifest, repo, forward_port, upstream_address, lifetime, credential_home=None, *, on_failure, upstream_port=443):
    home = Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
    if manifest.get("authentication") != "normal-login" or manifest.get("version") != "2.1.302":
        raise ValueError("normal_login_version_requires_probe")
    if manifest.get("credential_source") not in ("file", "macos-keychain"):
        raise ValueError("login_credential_source_required")
    if not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', str(manifest.get('launch',''))):
        raise ValueError("invalid_controller_identity")
    if str(Path(manifest['executable']).resolve()) != manifest['executable']:
        raise ValueError("canonical_cli_executable_required")
    if type(upstream_port) is not int or not 1 <= upstream_port <= 65535 or not 1 <= forward_port <= 65535 or not 10 <= lifetime <= 3600:
        raise ValueError("invalid_session_port_or_lifetime")
    socket.inet_pton(socket.AF_INET, upstream_address)
    url = urlsplit(manifest["upstream_url"])
    if url.username or url.password or url.path not in ('', '/') or url.query or url.fragment or not url.hostname:
        raise ValueError("invalid_login_upstream")
    peer_port = url.port if url.port is not None else (443 if url.scheme == 'https' else 0)
    if peer_port != upstream_port:
        raise ValueError("upstream_port_443_required" if upstream_port == 443 else "upstream_port_mismatch")
    if not 1 <= peer_port <= 65535 or not (url.scheme == 'https' or url.scheme == 'http' and url.hostname == upstream_address == '127.0.0.1'):
        raise ValueError("invalid_login_upstream")
    if ':' in url.hostname:
        raise ValueError("ipv4_upstream_required")
    try: socket.inet_pton(socket.AF_INET, url.hostname)
    except OSError: pass
    else:
        if url.hostname != upstream_address: raise ValueError("pinned_upstream_address_mismatch")
    if upstream_address == '127.0.0.1' and peer_port == forward_port:
        raise ValueError("forwarder_cannot_target_its_listener")
    for field in ("root", "state"):
        if str(outside_home(manifest[field], home)) != manifest[field]: raise ValueError("canonical_session_path_required")
    if Path(manifest['state']) != Path(manifest['root']) / 'state': raise ValueError('isolated_controller_state_required')
    repo = outside_home(repo, home)
    credential_home = Path(credential_home or home).resolve()
    if manifest["credential_source"] == "macos-keychain" and credential_home != home:
        raise ValueError("exact_account_keychain_required")
    private = Path(tempfile.mkdtemp(prefix="a2a-claude-login-", dir="/private/tmp")).resolve()
    try:
        for relative in ("home/.claude", "tmp", "shell", "metadata", "bootstrap"):
            (private / relative).mkdir(parents=True, mode=0o700)
        nominal = Path(manifest["state"]) / "login-audits" / manifest["launch"]
        audit = outside_home(nominal, home)
        if audit != nominal: raise ValueError("canonical_audit_path_required")
        audit.mkdir(parents=True, mode=0o700)
        for name in ("forwarder", "metadata", "C-tmp"):
            (audit / name).mkdir(mode=0o700)
        session = {"schema": 1, "manifest": manifest, "repo": str(repo), "real_home": str(home),
                   "credential_home": str(credential_home), "private_root": str(private), "c_root_pid": os.getpid(),
                   "deadline": time.time() + lifetime, "forward_port": forward_port,
                   "upstream_address": upstream_address, "upstream_port": peer_port,
                   "audit_directory": str(audit), "forwarder_directory": str(audit / "forwarder"),
                   "metadata_directory": str(audit / "metadata"), "auth_original_reads": 1}
        session["profiles"] = policies(session)
        baseline, process = collect_baseline(session)
        save(private / 'metadata/before.json', baseline)
        session['initial_inventory_process'] = process
        # Original auth is read only after the protected before inventory.
        auth = read_auth(str(credential_home), manifest["credential_source"])
        save(private / "home/.claude/.credentials.json", auth)
        save(private / "home/.claude/.claude.json", {"hasCompletedOnboarding": True,
             "projects": {unicodedata.normalize('NFC', str(repo)): {"hasTrustDialogAccepted": True}}})
        save(private / "session.json", session)
        return session
    except BaseException as error:
        # The caller owns the durable failure report. Publication must succeed
        # before this owner removes preparation data; keep the original error.
        on_failure(error, private, True, None)
        cleanup_error = None
        try: shutil.rmtree(private)
        except OSError as secondary: cleanup_error = secondary
        on_failure(error, private, False, cleanup_error)
        raise


def collect_baseline(session):
    child = subprocess.Popen(['/usr/bin/sandbox-exec','-p',session['profiles']['D'],
        '/usr/bin/python3','-I','-S','-B',str(SOURCE/'claudeLoginFiles.py')],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,cwd=session['private_root'])
    try:
        output,_=child.communicate(json.dumps({'operation':'inventory','home':session['real_home']}).encode(),timeout=25)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid,signal.SIGKILL);child.communicate()
        raise ValueError('before_inventory_deadline')
    if child.returncode != 0:raise ValueError('before_inventory_failed')
    return json.loads(output),{'pid':child.pid,'pgrp':child.pid,'profile':'D','role':'before original auth inventory','exit':child.returncode}


def detach(session, role, command):
    private = Path(session["private_root"])
    boot = private / "bootstrap" / (role + ".json")
    first = os.fork()
    if first == 0:
        os.setsid(); arm_deadline(session["deadline"] + 10)
        second = os.fork()
        if second:
            save(boot, {"pid": second, "pgrp": os.getpgrp(), "bootstrap_pid": os.getpid(), "profile": role})
            command = ["/usr/bin/true"]
        else:
            arm_deadline(session["deadline"] + 10)
        for descriptor in (0, 1, 2):
            fd = os.open("/dev/null", os.O_RDWR)
            os.dup2(fd, descriptor)
            if fd > 2: os.close(fd)
        close_extra_fds()
        if not second:
            until=time.monotonic()+2
            while not boot.exists():
                if time.monotonic()>=until:os._exit(2)
                time.sleep(.001)
        os.chdir(private)
        os.execve("/usr/bin/sandbox-exec", ["sandbox-exec", "-p", session["profiles"][role], *command],
                  {"PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "C"})
    _, status = os.waitpid(first, 0)
    owned = read(boot)
    owned["bootstrap_exit"] = os.waitstatus_to_exitcode(status)
    with (private / "owned-groups.jsonl").open('a') as stream:
        stream.write(json.dumps({"role":role,**owned})+'\n')
    return owned


def start_services(session, forwarder_command=None, metadata_command=None):
    path = str(Path(session["private_root"]) / "session.json")
    f = forwarder_command or ["/usr/bin/python3", "-I", "-S", "-B", str(SOURCE / "claudeLoginSession.py"), "--stage", "F", "--session", path]
    d = metadata_command or ["/usr/bin/python3", "-I", "-S", "-B", str(SOURCE / "claudeLoginSession.py"), "--stage", "D", "--session", path]
    # The cleanup owner exists before any process can load the auth copy.
    services = {"D": detach(session, "D", d)}
    if services['D']['bootstrap_exit'] == 0:
        services['F'] = detach(session, "F", f)
    save(Path(session["private_root"]) / "services.json", services)
    if 'F' not in services or any(value['bootstrap_exit'] != 0 for value in services.values()):
        # Startup never reached C. R still owns the private credential copy;
        # terminate only the groups it just created before deleting that copy.
        groups=[json.loads(line)['pgrp'] for line in (Path(session['private_root'])/'owned-groups.jsonl').read_text().splitlines()]
        for group in groups:
            try: os.killpg(group,signal.SIGKILL)
            except ProcessLookupError: pass
        until=time.monotonic()+5
        while time.monotonic()<until:
            alive=False
            for group in groups:
                try: os.killpg(group,0);alive=True
                except ProcessLookupError: pass
            if not alive: break
            time.sleep(.03)
        if not alive: shutil.rmtree(session['private_root'])
        save(Path(session['audit_directory'])/'preparation-failed.json',{'error':'service_profile_failed','services':services,'isolated_home_removed':not Path(session['private_root']).exists(),'owned_groups_gone':not alive})
        raise ValueError('service_profile_failed')
    return services


def close_extra_fds():
    limit = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
    if limit == resource.RLIM_INFINITY: raise ValueError("finite_descriptor_limit_required")
    os.closerange(3, limit)


def validate_bootstrap():
    home = Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
    for descriptor in (1, 2):
        if stat.S_ISREG(os.fstat(descriptor).st_mode):
            raw = fcntl.fcntl(descriptor, 50, bytes(1024))
            target = Path(os.fsdecode(raw.split(b'\0', 1)[0])).resolve()
            if target == home or home in target.parents:
                os.close(descriptor); os._exit(2)
    close_extra_fds()
    fd = os.open("/dev/null", os.O_RDONLY); os.dup2(fd, 0)
    if fd: os.close(fd)
    if os.getpgrp()!=os.getpid():os.setsid()


def enter_cli(session, command, extra_env=None):
    validate_bootstrap()
    private = Path(session["private_root"])
    env = {"PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "en_US.UTF-8",
           "HOME": str(private / "home"), "TMPDIR": str(Path(session["audit_directory"]) / "C-tmp"),
           "A2A_CLAUDE_LOGIN_SESSION": str(private / "session.json"),
           "A2A_PROFILE_PROCESS_LOG": str(Path(session["audit_directory"]) / "C-processes.jsonl"),
           "NODE_OPTIONS": "--import=" + (SOURCE / "claudeLoginProcessTrace.ts").as_uri()}
    if extra_env: env.update(extra_env)
    os.chdir(session['repo'])
    if os.getpgrp() != os.getpid(): os.setsid()
    os.execve("/usr/bin/sandbox-exec", ["sandbox-exec", "-p", session["profiles"]["C"], *command], env)


def metadata_service(session):
    private = Path(session["private_root"])
    directory = Path(session["metadata_directory"])
    own = {"pid": os.getpid(), "ppid": os.getppid(), "pgrp": os.getpgrp(), "profile": "D"}
    primary = None; cleanup = []
    class SessionCancelled(Exception): pass
    def deadline_signal(signum, frame):
        raise TimeoutError("login_session_deadline")
    signal.signal(signal.SIGALRM, deadline_signal)
    signal.setitimer(signal.ITIMER_REAL, max(.001, session["deadline"] - time.time()))
    try:
        read(private / "metadata/before.json")
        save(directory / "ready.json", own)
        while not (directory / "stop.json").exists():
            if (directory / "abort").exists(): raise SessionCancelled()
            try: os.kill(session["c_root_pid"], 0)
            except ProcessLookupError: raise RuntimeError("cli_root_ended_before_finalization")
            time.sleep(.03)
        request = read(directory / "stop.json")
        after = inventory(session["real_home"])
        absent = []
        for value in request.get("home_probe_paths", []):
            path = Path(value)
            if path.parent != Path(session["real_home"]) or not path.name.startswith(".a2a-t093-deny-"):
                raise ValueError("invalid_probe_stat_path")
            absent.append({"path": value, "absent": not os.path.lexists(path)})
        save(private / "metadata/after.json", after)
        save(directory / "closed.json", {**own, "collection_complete": True, "home_probe_paths": absent})
        while not (directory / "cleanup").exists():
            if (directory / "abort").exists(): raise SessionCancelled()
            try: os.kill(session["c_root_pid"], 0)
            except ProcessLookupError: raise RuntimeError("cli_root_ended_before_cleanup")
            time.sleep(.03)
    except BaseException as error:
        primary = type(error).__name__
    finally:
        arm_deadline(time.time() + 8)
        # Only this session's registered groups are terminated. No ps, fork,
        # Keychain lookup, source auth read or unprotected cleanup supervisor.
        owners = {}
        service_path = private / "services.json"
        if service_path.exists():
            value = read(service_path)["F"]; owners[value['pgrp']] = value['pid']
        registered = private / "owned-groups.jsonl"
        if primary and registered.exists():
            for line in registered.read_text().splitlines():
                if line:
                    value=json.loads(line)
                    if value['role']!='D': owners[value['pgrp']]=value['pid']
        if primary:
            for path in (private/'bootstrap').glob('*.json'):
                value=read(path)
                if value['profile']!='D':owners[value['pgrp']]=value['pid']
        pty_path = private / "pty-groups.jsonl"
        if pty_path.exists():
            for line in pty_path.read_text().splitlines():
                if line:
                    value=json.loads(line); owners[value['pgrp']]=value['pgrp']
        if primary and primary != "SessionCancelled":
            owners[session['c_root_pid']] = session['c_root_pid']
        groups=[]
        for group,pid in owners.items():
            if not isinstance(group,int) or not isinstance(pid,int) or group<=1 or pid<=1 or group==os.getpgrp():
                cleanup.append('invalid_owned_group');continue
            try:
                if os.getpgid(pid)!=group:
                    cleanup.append('owned_group_identity_lost');continue
            except ProcessLookupError:
                try: os.killpg(group,0)
                except ProcessLookupError: continue
                cleanup.append('owned_group_identity_lost');continue
            except OSError:
                cleanup.append('owned_group_identity_unavailable');continue
            groups.append(group)
            try: os.killpg(group, signal.SIGKILL)
            except ProcessLookupError: pass
            except OSError: cleanup.append("owned_group_cleanup_failed")
        for group in groups:
            until = time.monotonic() + 3
            while True:
                try: os.killpg(group, 0)
                except ProcessLookupError: break
                if time.monotonic() >= until:
                    cleanup.append("owned_group_exit_unconfirmed"); break
                time.sleep(.03)
        if not cleanup:
            try: shutil.rmtree(private)
            except OSError: cleanup.append("isolated_home_cleanup_failed")
        save(directory / "removed.json", {**own, "primary_failure": primary, "cleanup_failures": cleanup,
                                         "isolated_home_removed": not private.exists()})
    return 2 if primary or cleanup else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("launch", "facts", "F", "D"), default="launch")
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--session", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--forward-port", type=int)
    parser.add_argument("--upstream-address")
    parser.add_argument("--lifetime-seconds", type=int, default=600)
    args = parser.parse_args()
    if args.stage == 'facts':
        validate_bootstrap()
        if not args.audit:parser.error('audit directory required')
        home=Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
        audit=outside_home(args.audit,home)
        q=lambda value:json.dumps(str(value),ensure_ascii=False)
        policy='(version 1)(allow default)(deny file-write* (subpath '+q(home)+'))(deny network*)(deny mach-lookup (global-name-regex #".*[Ss]ecurity.*"))'
        policy+=home_read_barrier(home,[('subpath',SOURCE.parent.resolve())])
        command=[NODE,str(SOURCE/'claudeLoginCheck.ts'),*(['--preflight'] if args.preflight else []),str(audit)]
        os.chdir(audit)
        os.execve('/usr/bin/sandbox-exec',['sandbox-exec','-p',policy,*command],{'PATH':'/usr/bin:/bin','LANG':'C','TMPDIR':'/private/tmp'})
    if args.stage != "launch":
        session = read(args.session)
        if args.stage == "D": return metadata_service(session)
        arm_deadline(session["deadline"] + 5)
        save(Path(session["forwarder_directory"]) / "host.json",
             {"pid": os.getpid(), "ppid": os.getppid(), "pgrp": os.getpgrp(), "profile": "F"})
        os.execve(NODE, [NODE, str(SOURCE / "claudeForwarderProcess.ts"), str(args.session)], {"PATH": "/usr/bin:/bin", "LANG": "C"})
    if not args.manifest or not args.repo or not args.forward_port or not args.upstream_address:
        parser.error("manifest, repo, forward-port and upstream-address are required")
    validate_bootstrap()
    manifest=read(args.manifest)
    failure_path=None
    def preparation_failure(error, private, pending, cleanup_error):
        nonlocal failure_path
        if failure_path is None:
            home=Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()
            directory=outside_home(manifest['state'],home)
            failure_path=directory/('login-preparation-failure-'+str(uuid.uuid4())+'.json')
        # Error text can contain auth input. The production entry publishes
        # types and errno only; the synthetic test caller has its own redactor.
        value={'status':'INCOMPLETE','phase':'R','primary_failure':type(error).__name__,'isolated_home':str(private),'cleanup_pending':pending,
               'cleanup_failures':[] if cleanup_error is None else [{'type':type(cleanup_error).__name__,'errno':cleanup_error.errno}]}
        # Immutable primary and separate cleanup receipt; never truncate the
        # already durable primary while recording a secondary cleanup error.
        save(failure_path if pending else failure_path.with_suffix('.cleanup.json'),value)
    # Public production entry has no port override; the test caller passes its
    # local port directly to prepare(), without changing this entry contract.
    session = prepare(manifest, args.repo, args.forward_port, args.upstream_address, args.lifetime_seconds,on_failure=preparation_failure,upstream_port=443)
    start_services(session)
    enter_cli(session, [NODE, str(SOURCE / "daemon.ts"), session['manifest']['state']])


if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception:
        sys.stderr.write("normal_login_session_setup_failed\n")
        raise SystemExit(2)
