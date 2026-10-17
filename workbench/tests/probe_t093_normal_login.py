#!/usr/bin/env python3
"""T-093 前置探针。默认只显示范围，--run 才读取指定登录凭据。"""
import argparse
import base64
import errno
import fcntl
import json
import os
from pathlib import Path
import pty
import re
import resource
import select
import shutil
import signal
import socket
import stat
import struct
import subprocess
import sys
import tempfile
import termios
import time
from http.server import BaseHTTPRequestHandler, HTTPServer


SCOPES = (".claude", ".claude.json", ".claude.json.backup", "Library/Keychains")
SERVICE = "Claude Code-credentials"
VERSION = "2.1.302 (Claude Code)"
PROMPT = "T-093 本地假上游探针。请求只到本机，不执行工具。"
CHILDREN = []


class StopProbe(Exception):
    pass


def require(value, reason):
    if not value:
        raise StopProbe(reason)


def encode(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def secret_hits(data, secrets):
    # 同时检查原值、JSON 转义、URL 编码和 base64。只返回次数。
    from urllib.parse import quote
    variants = set()
    for value in secrets:
        variants.update((value, json.dumps(value)[1:-1], quote(value, safe=""),
                         base64.b64encode(value.encode()).decode()))
    return sum(data.count(value) for value in variants if value)


def output_shape(raw):
    # 只返回固定标签、布尔值和计数；绝不返回原始前缀、JSON 字段或错误正文。
    text = raw.decode("utf-8", "replace")
    leading = text.lstrip()
    prefix = "text"
    for marker, kind in (("sandbox-exec:", "sandbox_exec"), ("warning", "warning"),
                         ("error", "error"), ("usage:", "usage"), ("\x1b", "ansi_escape"),
                         ("{", "json_object"), ("[", "json_array")):
        if leading.lower().startswith(marker):
            prefix = kind
            break
    if not leading:
        prefix = "empty"
    is_json = True
    try:
        json.loads(raw)
    except ValueError:
        is_json = False
    after_prefix = False
    if not is_json:
        for marker in ("{", "["):
            index = text.find(marker)
            if index <= 0:
                continue
            try:
                json.loads(text[index:])
                after_prefix = True
            except ValueError:
                pass
    lower = text.lower()
    return {"bytes": len(raw), "line_count": len(raw.splitlines()), "prefix_kind": prefix,
            "starts_with_json": leading.startswith(("{", "[")), "is_json": is_json,
            "json_after_prefix": after_prefix, "has_ansi": "\x1b" in text,
            "mentions_oauth": "oauth" in lower, "mentions_subscription": "subscription" in lower,
            "mentions_base_url": "base_url" in lower or "base url" in lower,
            "mentions_not_supported": "not supported" in lower or "unsupported" in lower,
            "mentions_permission_error": any(word in lower for word in ("eperm", "eacces", "permission denied", "operation not permitted"))}


def metadata(home):
    result = {}

    def visit(name, parent_fd, relative):
        try:
            info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            result[relative] = {"missing": True}
            return
        result[relative] = {"mode": info.st_mode, "bytes": info.st_size,
                            "mtime_ns": info.st_mtime_ns, "inode": info.st_ino}
        if stat.S_ISLNK(info.st_mode):
            result[relative]["link"] = os.readlink(name, dir_fd=parent_fd)
        elif stat.S_ISDIR(info.st_mode):
            directory = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
            try:
                for child in sorted(os.listdir(directory)):
                    visit(child, directory, relative + "/" + child)
            finally:
                os.close(directory)
    home_fd = os.open(home, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for scope in SCOPES:
            parent_fd = os.dup(home_fd)
            parts = Path(scope).parts
            try:
                for index, part in enumerate(parts):
                    if index == len(parts) - 1:
                        visit(part, parent_fd, scope)
                        break
                    try:
                        info = os.stat(part, dir_fd=parent_fd, follow_symlinks=False)
                    except FileNotFoundError:
                        result[scope] = {"missing": True}
                        break
                    if not stat.S_ISDIR(info.st_mode):
                        visit(part, parent_fd, "/".join(parts[:index + 1]))
                        break
                    directory = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
                    os.close(parent_fd)
                    parent_fd = directory
            finally:
                os.close(parent_fd)
    finally:
        os.close(home_fd)
    return result


def stop_child(child):
    # 子进程均为新 session；即使 leader 已退出，也回收其后代。
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        child.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass
    finally:
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait(timeout=2)
        if child in CHILDREN:
            CHILDREN.remove(child)


def capture(argv, *, env, cwd, timeout=12):
    child = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             start_new_session=True)
    CHILDREN.append(child)
    try:
        stdout, stderr = child.communicate(timeout=timeout)
        return child.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        raise StopProbe("command_timeout") from None
    finally:
        stop_child(child)


def sandbox_profile(root, real_home, executable, port=None):
    literal = lambda path: json.dumps(str(path))
    network = (f'(allow network-outbound (remote ip "127.0.0.1:{port}"))'
               if port is not None else "")
    return f'''(version 1)
(allow default)
(deny file-write*)
(allow file-write* (subpath {literal(root)}))
(deny file-write* (subpath {literal(root / 'readonly')}))
(allow file-write* (literal "/dev/null") (literal "/dev/tty") (regex #"^/dev/ttys[0-9]+$"))
(deny file-read* (subpath {literal(real_home)}))
(allow file-read* (literal {literal(executable)}))
(deny mach-lookup (global-name-regex #".*[Ss]ecurity.*"))
(deny process-fork)
(deny network*)
{network}
'''


def guarded(profile, argv):
    return ["/usr/bin/sandbox-exec", "-p", profile, *argv]


def environment(root):
    paths = {name: root / name for name in ("home", "config", "tmp", "shell", "cwd")}
    paths["config"] = paths["home"] / ".claude"
    for path in paths.values():
        path.mkdir(mode=0o700)
    return {"PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
            "HOME": str(paths["home"]), "CLAUDE_CONFIG_DIR": str(paths["config"]),
            "TMPDIR": str(paths["tmp"]), "ZDOTDIR": str(paths["shell"]),
            "SHELL": "/bin/zsh", "TERM": "xterm-256color", "LANG": "en_US.UTF-8",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
            "CLAUDE_CODE_DISABLE_TERMINAL_TITLE": "1"}


def credentials(home, env, cwd, report):
    source = home / ".claude/.credentials.json"
    require(not source.is_symlink(), "credential_file_is_symlink")
    require(not (home / ".claude").is_symlink(), "credential_directory_is_symlink")
    # 不枚举钥匙串，不使用 dump-keychain，不访问其他服务。
    command = ["/usr/bin/security", "find-generic-password", "-s", SERVICE]
    # Security 会用 HOME 展开默认搜索位置；显式限定到已核对的单一
    # login keychain，避免隔离 HOME 被误当作真实登录的搜索根。
    keychain = home / "Library/Keychains/login.keychain-db"
    for relative in ("Library", "Library/Keychains", "Library/Keychains/login.keychain-db"):
        require(not (home / relative).is_symlink(), "keychain_path_is_symlink")
    require(keychain.is_file(), "reviewed_login_keychain_missing")
    read_only = '(version 1)(allow default)(deny file-write*)(deny network*)(deny process-fork)'
    code, _, _ = capture(guarded(read_only, [*command, str(keychain)]), env=env, cwd=cwd, timeout=5)
    report["keychain_query"] = {"service": SERVICE, "keychain": "~/Library/Keychains/login.keychain-db",
                                "exit_code": code, "profile_changed": False,
                                "home_is_isolated": env["HOME"] != str(home)}
    require(code in (0, 44), "keychain_lookup_unavailable")
    report["credential_locations"] = {"file_present": source.exists(),
                                      "exact_keychain_service_present": code == 0}
    require(not (source.exists() and code == 0), "credential_source_is_ambiguous")
    if code == 0:
        code, raw, _ = capture(guarded(read_only, [*command, "-w", str(keychain)]), env=env, cwd=cwd, timeout=5)
        report["keychain_read_exit_code"] = code
        require(code == 0, "keychain_read_unavailable")
        report["credential_source"] = "macOS Keychain: " + SERVICE
    else:
        require(source.is_file(), "login_credential_not_visible_in_reviewed_scope")
        require(source.stat().st_size < 1024 * 1024, "credential_file_too_large")
        raw = source.read_bytes()
        report["credential_source"] = "~/.claude/.credentials.json"
    require(len(raw) < 1024 * 1024, "credential_payload_too_large")
    try:
        payload = json.loads(raw)
        oauth = payload["claudeAiOauth"]
        access, refresh = oauth["accessToken"], oauth.get("refreshToken")
        require(isinstance(access, str) and len(access) >= 16, "invalid_access_token")
        require(refresh is None or isinstance(refresh, str), "invalid_refresh_token")
        require(isinstance(oauth["expiresAt"], (int, float)), "invalid_expiry")
        require(oauth["expiresAt"] > (time.time() + 120) * 1000, "login_expired_or_near_expiry")
    except (ValueError, KeyError, TypeError):
        raise StopProbe("unsupported_credential_format") from None
    secrets = [access] + ([refresh] if refresh else [])
    # 只复制订阅登录对象；不复制 MCP 凭据、设置、账号资料或历史。
    destination = Path(env["CLAUDE_CONFIG_DIR"]) / ".credentials.json"
    with destination.open("x", encoding="utf-8") as stream:
        os.chmod(destination, 0o600)
        stream.write(encode({"claudeAiOauth": oauth}))
    return secrets


def auth_status(executable, profile, env, cwd, report, name, secrets):
    code, stdout, stderr = capture(guarded(profile, [executable, "auth", "status", "--json"]), env=env, cwd=cwd)
    report["captured_output_secret_hits"] += secret_hits((stdout + stderr).decode("utf-8", "replace"), secrets)
    report[name + "_output"] = {"exit_code": code, "stdout": output_shape(stdout), "stderr": output_shape(stderr)}
    try:
        data = json.loads(stdout)
    except ValueError:
        raise StopProbe("auth_status_not_json") from None
    require(isinstance(data, dict), "auth_status_json_not_object")
    # 不保存原始状态输出（可含邮箱、账号标识等）。
    report[name] = {"exit_code": code, "loggedIn": data.get("loggedIn") is True,
                    "uses_claude_ai": data.get("authMethod") == "claude.ai",
                    "config_is_isolated": data.get("configDirectory") == env["CLAUDE_CONFIG_DIR"]}
    require(code == 0 and all(report[name][key] for key in
                             ("loggedIn", "uses_claude_ai", "config_is_isolated")), "isolated_login_not_recognized")


def sink(root):
    # 独立进程；只有 HTTP 接收与固定 400 响应，没有上游或转发代码。
    # 最初复制的凭据通过匿名管道送入并固定，不从 CLI 可写副本重读。
    secrets = json.loads(sys.stdin.buffer.read())
    expected = secrets[0]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def receive(self):
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 4 * 1024 * 1024:
                self.send_error(413)
                return
            body = self.rfile.read(length)
            try:
                message = json.loads(body)
            except ValueError:
                message = {}
            path = self.path.split("?", 1)[0]
            path_hits = secret_hits(path, secrets)
            record = {"method": self.command, "path": "<credential-redacted>" if path_hits else path,
                      "path_credential_hits": path_hits,
                      "body_bytes": len(body), "has_messages": isinstance(message, dict) and isinstance(message.get("messages"), list),
                      "bearer_matches_copied_login": self.headers.get("Authorization") == "Bearer " + expected,
                      "response_status": 400}
            with (root / "home/requests.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            response = b'{"type":"error","error":{"type":"invalid_request_error","message":"T-093 local sink. No upstream exists."}}'
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        do_GET = receive
        do_POST = receive

    server = HTTPServer(("127.0.0.1", 0), Handler)
    print(server.server_port, flush=True)
    server.serve_forever()


def rows(root):
    path = root / "home/requests.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def route(executable, profile, env, cwd, root, report, secrets):
    arguments = [executable, "--model", "claude-haiku-5-5", "--effort", "low",
                 "--permission-mode", "manual", "--tools", "", "--strict-mcp-config",
                 "--mcp-config", '{"mcpServers":{}}', "--disable-slash-commands", PROMPT]
    report["launch"] = {"argv": guarded(profile, arguments), "cli_argv": arguments, "env": env}
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 45, 160, 0, 0))
    child = subprocess.Popen(guarded(profile, arguments), cwd=cwd, env=env,
                             stdin=slave, stdout=slave, stderr=slave, start_new_session=True)
    CHILDREN.append(child)
    os.close(slave)
    captured, screen, answered = bytearray(), "", []
    # 只处理已知的一次性主题/说明/隔离 cwd 信任屏；未知屏幕到期即停。
    known = (("Choose the text style", b"1\r", "theme"),
             ("Please review the security notes", b"\r", "security_notice"),
             ("Do you trust the files in this folder?", b"1\r", "isolated_cwd_trust"),
             ("Is this a project you created or one you trust?", b"1\r", "isolated_cwd_trust"))
    try:
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            observed = rows(root)
            if any(row["method"] == "POST" and row["path"] == "/v1/messages" and
                   row["has_messages"] and row["bearer_matches_copied_login"] for row in observed):
                report["route_observed"] = True
                break
            if child.poll() is not None:
                break
            ready, _, _ = select.select([master], [], [], 0.1)
            if not ready:
                continue
            try:
                part = os.read(master, 65536)
            except OSError as error:
                if error.errno == errno.EIO:
                    break
                raise
            captured.extend(part)
            require(len(captured) < 4 * 1024 * 1024, "terminal_output_limit")
            screen += re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", part.decode("utf-8", "replace"))
            for marker, key, name in known:
                if marker in screen and name not in answered:
                    os.write(master, key)
                    answered.append(name)
                    screen = ""
                    break
        report["startup_controls"] = answered
        require(report.get("route_observed"), "no_authenticated_local_messages_request")
    finally:
        stop_child(child)
        os.close(master)
        report["captured_output_secret_hits"] += secret_hits(captured.decode("utf-8", "replace"), secrets)


def run(args):
    real_home = Path.home().resolve()
    executable = Path(args.claude).resolve(strict=True)
    require(sys.platform == "darwin", "macOS_required")
    require(Path("/usr/bin/sandbox-exec").is_file(), "sandbox_exec_required")
    require(args.output is not None, "output_required")
    output = Path(args.output).absolute()
    require(output.parent.is_dir() and not output.exists(), "new_output_file_required")
    require(not os.environ.get("CLAUDE_CONFIG_DIR"), "custom_source_config_requires_review")
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    root = Path(tempfile.mkdtemp(prefix="t093-probe-", dir="/private/tmp")).resolve()
    report = {"task": "T-093", "attempt": "a1", "scope": "前置探针；不替代产品验收",
              "status": "INCOMPLETE", "real_upstream_requests": 0,
              "captured_output_secret_hits": 0, "inventory_scope": list(SCOPES),
              "inventory_excludes": ["atime", "文件正文", "符号链接指向的内容", "其余 HOME 路径"]}
    before, secrets = None, []
    try:
        before = metadata(real_home)
        env = environment(root)
        cwd = str(root / "cwd")
        profile = sandbox_profile(root, real_home, executable)
        # 先用无凭据子进程检查读保护、写保护和网络保护。
        # 写保护只对隔离夹具做反例，绝不尝试写真实 HOME。
        (root / "readonly").mkdir(mode=0o700)
        check_script = '''import os, pathlib, socket, sys
home = pathlib.Path(sys.argv[1])
assert not socket.socket().connect_ex(("127.0.0.1", int(sys.argv[2]))) == 0
for path, flags in [(home, os.O_RDONLY), (pathlib.Path(sys.argv[3]) / "must-not-create", os.O_CREAT | os.O_WRONLY | os.O_EXCL)]:
    try:
        fd = os.open(path, flags, 0o600)
    except PermissionError:
        continue
    else:
        os.close(fd)
        raise SystemExit(9)
try:
    pid = os.fork()
except PermissionError:
    pass
else:
    if pid == 0:
        os._exit(0)
    os.waitpid(pid, 0)
    raise SystemExit(10)
'''
        # 活跃拒绝端口避免把连接拒绝误当作沙箱阻断。
        blocked = socket.socket()
        blocked.bind(("127.0.0.1", 0))
        blocked.listen(1)
        try:
            code, _, _ = capture(guarded(profile, [sys.executable, "-c", check_script,
                                                  str(real_home), str(blocked.getsockname()[1]),
                                                  str(root / "readonly")]), env=env, cwd=cwd)
            require(code == 0, "sandbox_preflight_failed")
        finally:
            blocked.close()
        for command, label in ((["--version"], "version"), (["--help"], "help"),
                               (["auth", "--help"], "auth_help"), (["auth", "status", "--help"], "status_help")):
            code, stdout, _ = capture(guarded(profile, [str(executable), *command]), env=env, cwd=cwd)
            require(code == 0, "cli_help_or_version_failed")
            text = stdout.decode("utf-8", "strict")
            if label == "version":
                require(text.strip() == VERSION, "cli_version_mismatch")
                report["cli_version"] = text.strip()
            elif label == "help":
                for flag in ("--model", "--effort", "--permission-mode", "--tools", "--strict-mcp-config", "--disable-slash-commands"):
                    require(flag in text, "required_flag_missing_from_help")
                report[label] = [line.strip() for line in text.splitlines() if "auth" in line.lower()]
            else:
                require("status" in text.lower(), "auth_status_missing_from_help")
                if label == "status_help":
                    require("--json" in text, "auth_status_json_flag_missing_from_help")
                report[label] = text.strip()
        secrets = credentials(real_home, env, cwd, report)
        auth_status(str(executable), profile, env, cwd, report, "status_without_base_url", secrets)
        sink_profile = ('(version 1)(allow default)(deny process-fork)(deny network-outbound)'
                        '(deny file-write*)(allow file-write* (subpath ' + json.dumps(str(root)) + '))')
        server = subprocess.Popen(guarded(sink_profile, [sys.executable, str(Path(__file__).resolve()), "--sink", str(root)]),
                                  cwd=cwd, env=env, stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True)
        CHILDREN.append(server)
        server.stdin.write(json.dumps(secrets).encode("utf-8"))
        server.stdin.close()
        require(select.select([server.stdout], [], [], 5)[0], "sink_start_timeout")
        port = int(server.stdout.readline())
        env["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{port}"
        profile = sandbox_profile(root, real_home, executable, port)
        # BASE_URL 与端口规则同时改变；先区分沙箱/启动错误和状态输出错误。
        code, stdout, stderr = capture(guarded(profile, [str(executable), "--version"]), env=env, cwd=cwd)
        report["captured_output_secret_hits"] += secret_hits((stdout + stderr).decode("utf-8", "replace"), secrets)
        report["bound_profile_probe"] = {"exit_code": code, "version_matches": stdout.strip() == VERSION.encode(),
                                          "stdout": output_shape(stdout), "stderr": output_shape(stderr)}
        require(code == 0 and report["bound_profile_probe"]["version_matches"], "bound_profile_cli_version_failed")
        auth_status(str(executable), profile, env, cwd, report, "status_with_base_url", secrets)
        route(str(executable), profile, env, cwd, root, report, secrets)
        auth_status(str(executable), profile, env, cwd, report, "status_after_route", secrets)
        report["status"] = "PASS"
    except StopProbe as error:
        report["stop_reason"] = str(error)
    except Exception:
        # 原始异常可能含凭据、路径或子进程输出，不打印、不保存。
        report["stop_reason"] = "unexpected_probe_error"
    finally:
        for name in (signal.SIGINT, signal.SIGTERM):
            signal.signal(name, signal.SIG_IGN)
        try:
            for child in list(reversed(CHILDREN)):
                stop_child(child)
            report["local_requests"] = rows(root)
            report["local_request_count"] = len(report["local_requests"])
            if before is not None:
                after = metadata(real_home)
                changes = [name for name in sorted(before.keys() | after.keys()) if before.get(name) != after.get(name)]
                report["inventory"] = {"before_entries": len(before), "after_entries": len(after),
                                       "changed_count": len(changes), "changes": changes}
                if changes:
                    report["status"] = "INCOMPLETE"
                    report["inventory_note"] = "有差异；不推断是否由探针造成。"
        except Exception:
            report["status"] = "INCOMPLETE"
            report["cleanup_observation_error"] = True
        finally:
            shutil.rmtree(root)
            report["isolated_home_removed"] = not root.exists()
    launch_text = encode(report.get("launch", {}))
    report["real_home_path_mentions_in_launch"] = launch_text.count(str(real_home)) if "launch" in report else None
    report["route_launch_attempted"] = "launch" in report
    report_text = encode(report)
    report["credential_scan_hits"] = secret_hits(report_text, secrets)
    if report["credential_scan_hits"]:
        report = {"task": "T-093", "status": "NO_GO", "stop_reason": "report_contains_credential",
                  "credential_scan_hits": report["credential_scan_hits"], "isolated_home_removed": not root.exists()}
    text = encode(report).replace(str(real_home), "<REAL_HOME>")
    require(secret_hits(text, secrets) == 0, "safe_output_scan_failed")
    with output.open("x", encoding="utf-8") as stream:
        stream.write(text)
    print(encode({"status": report["status"], "task": "T-093", "credential_scan_hits": report["credential_scan_hits"],
                  "isolated_home_removed": not root.exists()}), end="")
    return 0 if report["status"] == "PASS" else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--claude", default=str(Path.home() / ".local/share/claude/versions/2.1.302"))
    parser.add_argument("--output")
    parser.add_argument("--sink", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.sink:
        sink(Path(args.sink))
        return 0
    if not args.run:
        print(encode({"status": "INCOMPLETE", "mode": "scope_only", "inventory_scope": ["~/" + p for p in SCOPES],
                      "credential_reads": ["~/.claude/.credentials.json 或钥匙串精确服务 " + SERVICE],
                      "real_model_turns": 0, "next": "请先审阅 PROBE.md，再由主控在沙箱外执行 --run。"}), end="")
        return 0
    for name in (signal.SIGINT, signal.SIGTERM):
        signal.signal(name, lambda *_: (_ for _ in ()).throw(StopProbe("probe_interrupted")))
    return run(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except StopProbe as error:
        print(encode({"status": "INCOMPLETE", "stop_reason": str(error)}), end="")
        sys.exit(2)
    except Exception:
        print(encode({"status": "INCOMPLETE", "stop_reason": "probe_setup_or_cleanup_failed"}), end="")
        sys.exit(2)
