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
TERMINAL_OUTPUT = Path("/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/4cb6cda5-1e37-4e3e-8ff5-2755a799eb7c/scratchpad/t093-terminal-07.txt")


class StopProbe(Exception):
    pass


def require(value, reason):
    if not value:
        raise StopProbe(reason)


def encode(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def canonical_percent(text):
    # URL 百分号十六进制大小写等价；不改变未编码字符的大小写。
    return re.sub(r"%[0-9a-fA-F]{2}", lambda match: match[0].upper(), text)


def secret_variants(secrets):
    from urllib.parse import quote
    variants = set()
    for value in secrets:
        encoded = base64.b64encode(value.encode()).decode()
        url_encoded = base64.urlsafe_b64encode(value.encode()).decode()
        variants.update((value, json.dumps(value)[1:-1], quote(value, safe=""),
                         encoded, encoded.rstrip("="), url_encoded, url_encoded.rstrip("=")))
    return {canonical_percent(value) for value in variants if value}


def secret_hits(data, secrets):
    # 同时检查原值、JSON 转义、URL 编码和 base64。只返回次数。
    data = canonical_percent(data)
    variants = secret_variants(secrets)
    return sum(data.count(value) for value in variants if value)


def account_values(value):
    # 只处理已经读取的 auth status；不读额外配置或身份来源。
    result = set()
    fields = {"name", "email", "emailaddress", "org", "orgname", "orgid", "organization", "organizationname",
              "organizationid", "organisation", "organisationname", "account", "accountname", "accountid",
              "user", "username", "userid", "fullname", "displayname"}
    if isinstance(value, dict):
        for key, child in value.items():
            field = re.sub(r"[^a-z]", "", key.lower())
            if (field in fields or field.endswith("name")) and isinstance(child, str) and child:
                result.add(child)
            result.update(account_values(child))
    elif isinstance(value, list):
        for child in value:
            result.update(account_values(child))
    return result


def redact_terminal(raw, secrets, identities):
    text = raw.decode("utf-8", "strict")
    text = re.sub(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][\s\S]*?(?:\x07|\x1b\\)|[PX^_][\s\S]*?\x1b\\|(?![\[\]PX^_])[ -/]*[0-~])", "", text)
    require(not re.search(r"[\x1b\x80-\x9f]", text), "terminal_export_unsupported_escape")
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", text)
    text = canonical_percent(text)
    for value in sorted(secret_variants(secrets), key=len, reverse=True):
        text = text.replace(value, "<CREDENTIAL>")
    for identity in sorted(identities, key=len, reverse=True):
        replacement = "<EMAIL>" if "@" in identity else "<ACCOUNT>"
        for value in sorted(secret_variants([identity]), key=len, reverse=True):
            text = text.replace(value, replacement)
    text = re.sub(r'''(?:"(?:[^"\\]|\\.)+"|[\w.!#$%&'*+/=?^`{|}~-]+)@[\w-]+(?:\.[\w-]+)*''', "<EMAIL>", text)
    text = re.sub(r"(?im)^([ \t|+\u2500-\u257f]*(?:(?:organization|organisation|org|account|user)(?:\s+name)?|组织(?:名)?|账号(?:名)?)[ \t]*[:：=][ \t]*)[^\n]+", r"\1<ACCOUNT>", text)
    text = re.sub(r"(?im)^([ \t|+\u2500-\u257f]*(?:welcome(?: back)?[, ]+|(?:you are )?(?:signed|logged) in as\s+))[^\n]+", r"\1<ACCOUNT>", text)
    return text


def terminal_parent(path):
    require(path.is_absolute(), "terminal_export_absolute_path_required")
    directory = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for ancestor in path.parent.parts[1:]:
            child = os.open(ancestor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        return directory
    except BaseException:
        os.close(directory)
        raise


def write_terminal_output(path, raw, secrets, identities):
    text = redact_terminal(raw, secrets, identities)
    hits = secret_hits(text, secrets)
    require(hits == 0, "terminal_export_credential_scan_failed")
    require(secret_hits(text, identities) == 0, "terminal_export_identity_scan_failed")
    # 扫描通过后才打开文件；逐级拒绝祖先链接，且不覆盖已有文件。
    parent = terminal_parent(path)
    try:
        fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
    finally:
        os.close(parent)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(text)
    return {"written": True, "bytes": len(text.encode("utf-8")), "mode": "0600", "credential_scan_hits": hits}


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
    network = (f'(allow network-outbound (remote tcp4 "localhost:{port}"))'
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
    return account_values(data)


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


def terminal_replies(pending, part):
    # 与 workbench/src/panes.ts terminalProtocol 使用同一组固定终端协议。
    # 回复没有 Enter，不是用户输入或未知屏幕授权。
    pending += part
    replies = []
    table = {b"6n": ("cursor_position", b"\x1b[1;1R"),
             b"c": ("primary_attributes", b"\x1b[?1;2c"), b"0c": ("primary_attributes", b"\x1b[?1;2c"),
             b">c": ("secondary_attributes", b"\x1b[>0;0;0c"), b">0c": ("secondary_attributes", b"\x1b[>0;0;0c"),
             b"?u": ("keyboard_protocol", b"\x1b[?0u"),
             b"11;?": ("background_color", b"\x1b]11;rgb:0000/0000/0000\x1b\\")}
    while True:
        start = pending.find(b"\x1b")
        if start < 0:
            return b"", replies
        pending = pending[start:]
        if len(pending) == 1:
            return pending, replies
        if pending[1:2] not in (b"[", b"]"):
            pending = pending[2:]
            continue
        match = re.match(rb"^(?:\x1b\[([0-?]*[ -/]*[@-~])|\x1b\]([^\x07]*?)(?:\x07|\x1b\\))", pending)
        if not match:
            return pending if len(pending) <= 4096 else b"", replies
        reply = table.get(match[1] or match[2])
        if reply:
            replies.append(reply)
        pending = pending[match.end():]


def terminal_facts(raw, prompt):
    text = raw.decode("utf-8", "replace")
    clean = re.sub(r"\x1b\][^\x07]*?(?:\x07|\x1b\\)|\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    tail = clean[-32768:].lower()
    normalized = " ".join(clean.lower().split())
    denial = r"\b(?:eperm|eacces|operation not permitted|permission denied|denied)\b"
    operations = (("fork", r"\b(?:fork|vfork)\b"),
                  ("exec", r"\bexec(?:ve|vpe|vp|v|le|lp|l)?\b"),
                  ("spawn", r"\b(?:posix_spawnp?|spawnsync|spawn)\b"))
    # 固定词在 160 字符内相邻仅是终端文字信号，不是 syscall/沙箱归属证明。
    process_denials = [name for name, pattern in operations if re.search(
        pattern + r".{0,160}" + denial + "|" + denial + r".{0,160}" + pattern, normalized)]
    failure = r"(?:failed|unable) to connect"
    targets = (r"\b" + failure + r"(?: to)?\s+(?:https?://)?([a-z0-9.-]+)(?=$|[\s:/,;!?)\]])",
               r"(?<![\w.@/-])(?:https?://)?([a-z0-9.-]+)(?::[0-9]+)?\s*:\s*" + failure + r"\b")
    host_connection_failure = any(match[1].rstrip(".") == "api.anthropic.com"
                                  for pattern in targets for match in re.finditer(pattern, normalized))
    categories = {"theme": ("choose the text style",),
                  "security_notice": ("security notes:", "please review the security notes"),
                  "workspace_trust": ("do you trust the files", "is this a project you created", "trust this folder"),
                  "login": ("select login method", "how would you like to log in", "sign in to your account"),
                  "terminal_setup": ("terminal setup",),
                  "argument_error": ("unknown option", "allowed choices", "invalid argument", "unexpected argument"),
                  "runtime_error": ("error:", "typeerror", "eperm", "permission denied", "operation not permitted"),
                  "connection_error": ("unable to connect", "failed to connect", "connection refused", "econnrefused", "fetch failed")}
    classes = [name for name, markers in categories.items() if any(m in tail for m in markers)]
    if process_denials:
        classes.append("process_launch_denial")
    if host_connection_failure:
        classes.append("official_host_connectivity_failure")
    return {**output_shape(raw), "tail_marker_classes": classes,
            "process_denial_operations": process_denials, "official_host_connectivity_failure": host_connection_failure,
            "prompt_echo_seen": prompt in clean, "prompt_like_marker": bool(re.search(r"(?:^|\n)\s*[❯>]\s", clean)),
            "mentions_official_api_host": "api.anthropic.com" in clean.lower(),
            "mentions_spawn": "spawn" in clean.lower()}


def submission_facts(root, prompt):
    result = {"scope": "isolated home/.claude/projects/<project>/*.jsonl", "available": False,
              "matching_user_records": 0, "jsonl_files": 0, "parse_errors": 0,
              "io_errors": 0, "symlinks_skipped": 0, "partial_lines": 0, "limit_reached": False}
    directory = None
    try:
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        for part in ("home", ".claude", "projects"):
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        result["available"] = True
        total = 0
        for project in os.listdir(directory):
            info = os.stat(project, dir_fd=directory, follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode):
                result["symlinks_skipped"] += 1
                continue
            if not stat.S_ISDIR(info.st_mode):
                continue
            project_fd = os.open(project, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            try:
                for name in os.listdir(project_fd):
                    if not name.endswith(".jsonl"):
                        continue
                    info = os.stat(name, dir_fd=project_fd, follow_symlinks=False)
                    if stat.S_ISLNK(info.st_mode):
                        result["symlinks_skipped"] += 1
                        continue
                    if not stat.S_ISREG(info.st_mode):
                        continue
                    if result["jsonl_files"] >= 64 or total >= 8 * 1024 * 1024:
                        result["limit_reached"] = True
                        return result
                    result["jsonl_files"] += 1
                    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=project_fd)
                    with os.fdopen(fd, "rb") as stream:
                        while True:
                            line = stream.readline(262145)
                            if not line:
                                break
                            total += len(line)
                            if len(line) > 262144 or total > 8 * 1024 * 1024:
                                result["limit_reached"] = True
                                return result
                            if not line.endswith(b"\n"):
                                result["partial_lines"] += 1
                                break
                            try:
                                record = json.loads(line)
                            except ValueError:
                                result["parse_errors"] += 1
                                continue
                            message = record.get("message") if isinstance(record, dict) and record.get("type") == "user" else None
                            if not isinstance(message, dict) or message.get("role") != "user":
                                continue
                            content = message.get("content")
                            if isinstance(content, str):
                                texts = [content]
                            elif isinstance(content, list):
                                texts = [block.get("text") for block in content if isinstance(block, dict) and block.get("type") == "text"]
                            else:
                                texts = []
                            result["matching_user_records"] += int(prompt in texts)
            finally:
                os.close(project_fd)
    except FileNotFoundError:
        if result["available"]:
            result["io_errors"] += 1
    except OSError:
        result["io_errors"] += 1
    finally:
        if directory is not None:
            os.close(directory)
        result["scanned_scope_complete"] = result["available"] and not any(result[key] for key in
            ("parse_errors", "io_errors", "symlinks_skipped", "partial_lines", "limit_reached"))
    return result


def home_references(value, home, field="launch"):
    if isinstance(value, dict):
        return [item for key, child in value.items() for item in home_references(child, home, field + "." + key)]
    if isinstance(value, list):
        return [item for index, child in enumerate(value) for item in home_references(child, home, field + "[" + str(index) + "]")]
    if isinstance(value, str):
        return [{"field": field, "line": index + 1} for index, line in enumerate(value.splitlines()) for _ in range(line.count(home))]
    return []


def route(executable, profile, env, cwd, root, report, secrets, *, terminal_output=None, identities=()):
    arguments = [executable, "--model", "claude-haiku-5-5", "--effort", "low",
                 "--permission-mode", "manual", "--tools", "", "--strict-mcp-config",
                 "--mcp-config", '{"mcpServers":{}}', "--disable-slash-commands", PROMPT]
    report["launch"] = {"argv": guarded(profile, arguments), "cli_argv": arguments, "env": env}
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 45, 160, 0, 0))
    try:
        child = subprocess.Popen(guarded(profile, arguments), cwd=cwd, env=env,
                                 stdin=slave, stdout=slave, stderr=slave, start_new_session=True)
    except (OSError, subprocess.SubprocessError) as error:
        report["route_diagnostic"] = {"child_started": False, "spawn_error_errno": getattr(error, "errno", None)}
        os.close(slave); os.close(master)
        raise StopProbe("interactive_process_start_failed") from None
    CHILDREN.append(child)
    # 保留本进程的 slave 引用到排空结束，避免最后一个 slave 关闭时
    # 快速退出子进程留下的 PTY 输出被丢弃；本进程不向 slave 写入。
    captured, screen, answered, pending = bytearray(), "", [], b""
    replies_count, eof, deadline_reached, output_truncated = {}, False, False, False
    try:
        foreground_is_child = os.tcgetpgrp(master) == child.pid
    except OSError:
        foreground_is_child = None
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
            ready, _, _ = select.select([master], [], [], 0.1)
            if not ready:
                if child.poll() is not None:
                    break
                continue
            try:
                part = os.read(master, 65536)
            except OSError as error:
                if error.errno == errno.EIO:
                    eof = True
                    break
                raise
            if not part:
                eof = True
                break
            captured.extend(part)
            require(len(captured) < 4 * 1024 * 1024, "terminal_output_limit")
            if child.poll() is not None:
                continue
            screen += re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", part.decode("utf-8", "replace"))
            pending, replies = terminal_replies(pending, part)
            for name, response in replies:
                os.write(master, response)
                replies_count[name] = replies_count.get(name, 0) + 1
            for marker, key, name in known:
                if marker in screen and name not in answered:
                    os.write(master, key)
                    answered.append(name)
                    screen = ""
                    break
        else:
            deadline_reached = True
    finally:
        exit_before_stop = child.poll()
        stop_child(child)
        # 子进程可能快速退出；仍须排空它已经写入 PTY 的字节，只做诊断，不再发键。
        while select.select([master], [], [], 0)[0]:
            try:
                part = os.read(master, 65536)
            except OSError as error:
                if error.errno == errno.EIO:
                    eof = True
                    break
                raise
            if not part:
                eof = True
                break
            if len(captured) + len(part) > 4 * 1024 * 1024:
                output_truncated = True
                break
            captured.extend(part)
        os.close(slave)
        os.close(master)
        report["captured_output_secret_hits"] += secret_hits(captured.decode("utf-8", "replace"), secrets)
        report["startup_controls"] = answered
        report["route_diagnostic"] = {"child_started": True, "foreground_is_child": foreground_is_child,
                                      "exit_code_before_stop": exit_before_stop, "exit_code_after_stop": child.returncode,
                                      "stopped_by_probe": exit_before_stop is None, "deadline_reached": deadline_reached,
                                      "pty_eof_seen": eof, "output_truncated": output_truncated,
                                      "protocol_replies": replies_count, "terminal": terminal_facts(captured, PROMPT),
                                      "query_via_argv": True, "submission": submission_facts(root, PROMPT)}
        if terminal_output is not None:
            report["terminal_export"] = {"requested": True, "written": False}
            report["terminal_export"].update(write_terminal_output(terminal_output, captured, secrets, identities))
    report["route_observed"] = any(row["method"] == "POST" and row["path"] == "/v1/messages" and
                                   row["has_messages"] and row["bearer_matches_copied_login"] for row in rows(root))
    require(report["route_observed"], "no_authenticated_local_messages_request")


def run(args):
    real_home = Path.home().resolve()
    executable = Path(args.claude).resolve(strict=True)
    require(sys.platform == "darwin", "macOS_required")
    require(Path("/usr/bin/sandbox-exec").is_file(), "sandbox_exec_required")
    require(args.output is not None, "output_required")
    output = Path(args.output).absolute()
    require(output.parent.is_dir() and not output.exists(), "new_output_file_required")
    terminal_output = Path(args.terminal_output) if args.terminal_output else None
    if terminal_output is not None:
        require(terminal_output == TERMINAL_OUTPUT, "terminal_export_path_not_authorized")
        parent = terminal_parent(terminal_output)
        try:
            try:
                os.stat(terminal_output.name, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise StopProbe("terminal_export_file_already_exists")
        finally:
            os.close(parent)
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
            # 先独立验证带端口的 profile；此时尚未查询或复制任何登录凭据。
            with socket.socket() as allowed:
                allowed.bind(("127.0.0.1", 0))
                allowed.listen(1)
                allowed_port = allowed.getsockname()[1]
                bound_profile = sandbox_profile(root, real_home, executable, allowed_port)
                bound_env = {**env, "ANTHROPIC_BASE_URL": f"http://127.0.0.1:{allowed_port}"}
                code, stdout, stderr = capture(guarded(bound_profile, [str(executable), "--version"]), env=bound_env, cwd=cwd)
                report["precredential_bound_profile_probe"] = {
                    "exit_code": code, "version_matches": stdout.strip() == VERSION.encode(),
                    "stdout": output_shape(stdout), "stderr": output_shape(stderr)}
                require(code == 0 and report["precredential_bound_profile_probe"]["version_matches"],
                        "precredential_bound_profile_cli_version_failed")
                bound_check = check_script + '\nwith socket.create_connection(("127.0.0.1", int(sys.argv[4])), timeout=2):\n    pass\n'
                code, stdout, stderr = capture(guarded(bound_profile, [sys.executable, "-c", bound_check,
                                                                      str(real_home), str(blocked.getsockname()[1]),
                                                                      str(root / "readonly"), str(allowed_port)]), env=bound_env, cwd=cwd)
                report["precredential_bound_profile_guards"] = {
                    "exit_code": code, "passed": code == 0,
                    "checks": ["other_loopback_port_denied", "real_home_read_denied", "fixture_write_denied",
                               "fork_denied", "bound_loopback_port_connected"],
                    "stdout": output_shape(stdout), "stderr": output_shape(stderr)}
                require(code == 0, "precredential_bound_profile_guards_failed")
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
        identities = auth_status(str(executable), profile, env, cwd, report, "status_without_base_url", secrets)
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
        # 同一 profile 到真实假上游端口的 TCP 正例，不发送 HTTP 或任何凭据。
        tcp_check = 'import socket,sys\nwith socket.create_connection(("127.0.0.1", int(sys.argv[1])), timeout=2):\n    pass\n'
        code, stdout, stderr = capture(guarded(profile, [sys.executable, "-c", tcp_check, str(port)]), env=env, cwd=cwd)
        report["sink_tcp_preflight"] = {"exit_code": code, "connected": code == 0,
                                         "stdout": output_shape(stdout), "stderr": output_shape(stderr)}
        require(code == 0, "local_sink_tcp_unreachable")
        identities.update(auth_status(str(executable), profile, env, cwd, report, "status_with_base_url", secrets))
        route(str(executable), profile, env, cwd, root, report, secrets, terminal_output=terminal_output, identities=identities)
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
    report["real_home_path_references"] = home_references(report.get("launch", {}), str(real_home))
    report["real_home_path_mentions_in_launch"] = len(report["real_home_path_references"]) if "launch" in report else None
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
    parser.add_argument("--terminal-output", help="仅允许主控指定的 probe-07 脱敏终端临时文件；不覆盖。")
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
