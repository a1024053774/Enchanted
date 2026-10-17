#!/usr/bin/env python3
"""只验证 T-093 探针辅助逻辑；不运行 Claude、不读取任何真实凭据。"""
import base64
import ctypes
import http.client
import importlib.util
import io
import json
import os
import re
from pathlib import Path
import select
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from urllib.parse import quote, unquote
from uuid import uuid4


SOURCE = Path(__file__).with_name("probe_t093_normal_login.py")
spec = importlib.util.spec_from_file_location("t093_probe", SOURCE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ProbeSafety(unittest.TestCase):
    def test_onboarding_state_is_one_new_field_in_private_config(self):
        self.assertTrue(callable(getattr(probe, "prepare_onboarding_state", None)))
        with tempfile.TemporaryDirectory(prefix="t093-onboarding-state-") as temp:
            root = Path(temp).resolve()
            probe.environment(root)
            result = probe.prepare_onboarding_state(root)
            path = root / "home/.claude/.claude.json"
            self.assertTrue(path.is_file(), "状态应在隔离 CLAUDE_CONFIG_DIR 内。")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"hasCompletedOnboarding": True})
            self.assertIs(json.loads(path.read_text(encoding="utf-8"))["hasCompletedOnboarding"], True)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(result["relative_path"], "home/.claude/.claude.json")
            self.assertFalse((root / "home/.claude.json").exists())
            with self.assertRaises(FileExistsError):
                probe.prepare_onboarding_state(root)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"hasCompletedOnboarding": True})
            linked, outside = root / "linked", root / "outside"
            linked.mkdir(); (outside / ".claude").mkdir(parents=True)
            (linked / "home").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(OSError):
                probe.prepare_onboarding_state(linked)
            self.assertFalse((outside / ".claude/.claude.json").exists())

    @unittest.skipUnless(sys.platform == "darwin", "探针入口只支持 macOS")
    def test_onboarding_state_precedes_cli_and_auth_only_when_requested(self):
        for prepare in (False, True):
            with self.subTest(prepare=prepare), tempfile.TemporaryDirectory(prefix="t093-onboarding-order-") as temp:
                outer = Path(temp).resolve()
                home, isolated = outer / "source", outer / "isolated"
                home.mkdir(); isolated.mkdir()
                foreign = home / ".claude.json"
                foreign.write_text('{"must_not_copy":"foreign-state"}', encoding="utf-8")
                calls = []

                def fake_capture(argv, **kwargs):
                    calls.append(argv)
                    state = isolated / "home/.claude/.claude.json"
                    self.assertEqual(state.exists(), prepare)
                    if prepare:
                        self.assertEqual(json.loads(state.read_text(encoding="utf-8")), {"hasCompletedOnboarding": True})
                    return (0, b"", b"") if len(calls) == 1 else (65, b"", b"synthetic profile stop")

                args = SimpleNamespace(claude=sys.executable, output=str(outer / "report.json"),
                                       terminal_output=None, prepare_onboarding_state=prepare)
                with patch.object(probe.Path, "home", return_value=home), \
                     patch.object(probe.tempfile, "mkdtemp", return_value=str(isolated)), \
                     patch.object(probe, "capture", side_effect=fake_capture), \
                     patch.object(probe, "credentials") as read_credentials, \
                     patch.object(probe.resource, "setrlimit"), patch.object(probe.signal, "signal"), \
                     patch.object(probe.os, "umask"), patch.object(sys, "stdout", io.StringIO()):
                    code = probe.run(args)
                report = json.loads((outer / "report.json").read_text(encoding="utf-8"))
                self.assertEqual(code, 2)
                self.assertEqual(report["stop_reason"], "precredential_bound_profile_cli_version_failed")
                self.assertEqual(len(calls), 2)
                self.assertEqual("onboarding_state" in report, prepare)
                self.assertFalse(read_credentials.called or isolated.exists())
                self.assertEqual(foreign.read_text(encoding="utf-8"), '{"must_not_copy":"foreign-state"}')

    def test_terminal_export_redacts_variants_identities_and_preserves_diagnostics(self):
        self.assertTrue(callable(getattr(probe, "write_terminal_output", None)), "需要仅写脱敏正文的入口。")
        with tempfile.TemporaryDirectory(prefix="t093-terminal-export-") as temp:
            root = Path(temp).resolve()
            token = "t093-敏感-" + uuid4().hex + ' /+"?%'
            org, account = "组织-" + uuid4().hex, "User " + uuid4().hex
            email = "用户+" + uuid4().hex + "@example.invalid"
            payload = {"loggedIn": True, "authMethod": "claude.ai", "configDirectory": str(root),
                       "email": email, "orgName": org, "account": {"displayName": account}}
            report = {"captured_output_secret_hits": 0}
            with patch.object(probe, "capture", return_value=(0, json.dumps(payload).encode(), b"")):
                identities = probe.auth_status("synthetic-cli", "synthetic-profile", {"CLAUDE_CONFIG_DIR": str(root)},
                                               str(root), report, "status_with_base_url", [token])
            variants = [token, json.dumps(token)[1:-1], quote(token, safe=""), base64.b64encode(token.encode()).decode()]
            encoded = quote(token, safe="")
            lower = re.sub(r"%[0-9A-F]{2}", lambda match: match[0].lower(), encoded)
            mixed = re.sub(r"%[0-9A-F]{2}", lambda match: match[0].lower() if match.start() % 2 else match[0], encoded)
            self.assertEqual(unquote(mixed), token)
            variants += [lower, mixed, base64.b64encode(token.encode()).decode().rstrip("="),
                         base64.urlsafe_b64encode(token.encode()).decode().rstrip("=")]
            raw = ("\x1b7\x1b(B\x1b[31mError: diagnostic remains\x1b[0m\x1b8\n" + "\n".join(variants) + "\n" +
                   token[:12] + "\x1b[0m" + token[12:] + "\n" + org + "\n" + account + "\n" + email +
                   "\nUnknown+alias@example.invalid\nAccount: Unlisted Alias\nWelcome back, Hidden Display!\nSigned in as Another Alias\n" +
                   "│ Welcome back, Decorated Greeting! │\n│ Account: Decorated Alias │\n").encode()
            destination = root / "redacted.txt"
            stopped, result = None, None
            try:
                result = probe.write_terminal_output(destination, raw, [token], identities)
            except probe.StopProbe as error:
                stopped = str(error)
            self.assertIsNone(stopped, "合法脱敏内容应能保存。")
            saved = destination.read_text(encoding="utf-8")
            self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o600)
            self.assertEqual(result["credential_scan_hits"], 0)
            self.assertTrue(result["written"])
            for value in [*variants, org, account, email, "Unknown+alias@example.invalid", "Unlisted Alias", "Hidden Display", "Another Alias", "Decorated Greeting", "Decorated Alias", "\x1b"]:
                self.assertFalse(value in saved, "脱敏文件仍含禁止内容。")
            for marker in ("<CREDENTIAL>", "<EMAIL>", "<ACCOUNT>", "Error: diagnostic remains"):
                self.assertIn(marker, saved)
            for value in (org, account, email, token):
                self.assertFalse(value in json.dumps(report) or value in json.dumps(result), "摘要只能保留计数。")

    def test_terminal_export_scans_before_create_and_refuses_existing_or_linked_paths(self):
        self.assertTrue(callable(getattr(probe, "write_terminal_output", None)), "需要在写盘前拒绝泄漏。")
        with tempfile.TemporaryDirectory(prefix="t093-terminal-safety-") as temp:
            root = Path(temp).resolve()
            token, account = "t093-secret-" + uuid4().hex + " /+?!", "Account " + uuid4().hex
            encoded = re.sub(r"%[0-9A-F]{2}", lambda match: match[0].lower(), quote(token, safe=""))
            self.assertNotEqual(base64.b64encode(token.encode()).decode(), base64.b64encode(token.encode()).decode().rstrip("="))
            for leak in (token, account, encoded, base64.b64encode(token.encode()).decode().rstrip("=")):
                with patch.object(probe, "redact_terminal", return_value=leak):
                    with self.assertRaises(probe.StopProbe):
                        probe.write_terminal_output(root / "must-not-exist.txt", b"synthetic", [token], {account})
                self.assertFalse((root / "must-not-exist.txt").exists())
            existing = root / "existing.txt"
            existing.write_text("KEEP", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                probe.write_terminal_output(existing, b"safe diagnostic", [token], {account})
            self.assertEqual(existing.read_text(encoding="utf-8"), "KEEP")
            outside = root / "outside"
            outside.mkdir()
            (root / "linked").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(OSError):
                probe.write_terminal_output(root / "linked/redacted.txt", b"safe diagnostic", [token], {account})
            self.assertFalse((outside / "redacted.txt").exists())
            for raw in (b"\x1b]unfinished", b"\x1bPunfinished", b"\x1b(", b"\xff"):
                with self.assertRaises((probe.StopProbe, UnicodeDecodeError)):
                    probe.write_terminal_output(root / "incomplete.txt", raw, [token], {account})
                self.assertFalse((root / "incomplete.txt").exists())

    @unittest.skipUnless(sys.platform == "darwin", "探针入口只支持 macOS")
    def test_terminal_export_wrong_destination_stops_before_private_setup(self):
        with tempfile.TemporaryDirectory(prefix="t093-terminal-destination-") as temp:
            root = Path(temp).resolve()
            args = SimpleNamespace(claude=sys.executable, output=str(root / "report.json"),
                                   terminal_output=str(root / "unauthorized.txt"), prepare_onboarding_state=False)
            with patch.object(probe.tempfile, "mkdtemp", side_effect=probe.StopProbe("private_setup_attempted")) as setup, \
                 patch.object(probe, "credentials") as read_credentials:
                with self.assertRaises(probe.StopProbe) as stopped:
                    probe.run(args)
            self.assertEqual(str(stopped.exception), "terminal_export_path_not_authorized")
            self.assertFalse(setup.called or read_credentials.called)

    def test_terminal_process_denials_and_host_failures_keep_only_categories(self):
        token, email = "t093-synthetic-" + uuid4().hex, uuid4().hex + "@example.invalid"
        cases = [
            (b"fork: Operation not permitted", ["fork"], False),
            (b"EPERM: posix_spawn /bin/zsh", ["spawn"], False),
            (b"execve: Permission denied", ["exec"], False),
            (b"\x1b[31mspawn\x1b[0m /bin/zsh EACCES", ["spawn"], False),
            (b"Failed to connect to api.anthropic.com", [], True),
            (b"Unable to connect to\n\x1b[31mapi.anthropic.com\x1b[0m", [], True),
            (b"api.anthropic.com: unable to connect", [], True),
            (b"https://api.anthropic.com:443: failed to connect", [], True),
            (b"Unable to connect to 127.0.0.1:54321.\nAPI documentation: https://api.anthropic.com", [], False),
            (b"Failed to connect to api.anthropic.com.invalid", [], False),
            (b"Failed to connect to https://api.anthropic.com@unrelated.invalid", [], False),
            (b"api.anthropic.com", [], False),
            (b"fork succeeded; spawn complete; exec ready", [], False),
            (b"Failed to connect to 127.0.0.1", [], False),
        ]
        for text, operations, host_failure in cases:
            with self.subTest(text=text):
                raw = text + b"\n" + token.encode() + b" " + email.encode()
                result = probe.terminal_facts(raw, "unseen prompt " + uuid4().hex)
                self.assertIn("process_denial_operations", result)
                self.assertEqual(result["process_denial_operations"], operations)
                self.assertEqual(result["official_host_connectivity_failure"], host_failure)
                saved = json.dumps(result)
                self.assertFalse(token in saved or email in saved, "分类不能保留原文、凭据或邮箱。")

    def test_submission_reader_does_not_follow_an_ancestor_symlink(self):
        with tempfile.TemporaryDirectory(prefix="t093-submission-") as temp:
            root, outside = Path(temp) / "root", Path(temp) / "outside"
            root.mkdir()
            project = outside / ".claude/projects/external"
            project.mkdir(parents=True)
            prompt = "external input " + uuid4().hex
            (project / "foreign.jsonl").write_text(json.dumps({"type": "user", "message": {"role": "user", "content": prompt}}) + "\n", encoding="utf-8")
            (root / "home").symlink_to(outside)
            result = probe.submission_facts(root, prompt)
            self.assertEqual(result["matching_user_records"], 0)
            self.assertFalse(result["scanned_scope_complete"])
            self.assertGreater(result["io_errors"], 0)

    def test_home_references_include_policy_and_duplicate_executable_fields(self):
        home = "/synthetic-real-home"
        executable = home + "/.local/share/claude/versions/2.1.302"
        policy = '(deny file-read* (subpath "' + home + '"))\n(allow file-read* (literal "' + executable + '"))'
        launch = {"argv": ["/usr/bin/sandbox-exec", "-p", policy, executable],
                  "cli_argv": [executable], "env": {"HOME": "/private/tmp/t093-synthetic/home"}}
        self.assertEqual(probe.home_references(launch, home), [
            {"field": "launch.argv[2]", "line": 1}, {"field": "launch.argv[2]", "line": 2},
            {"field": "launch.argv[3]", "line": 1}, {"field": "launch.cli_argv[0]", "line": 1}])

    def test_route_drains_output_from_a_child_that_already_exited(self):
        with tempfile.TemporaryDirectory(prefix="t093-route-exit-") as temp:
            root = Path(temp).resolve()
            env = probe.environment(root)
            token, email = "t093-synthetic-" + uuid4().hex, uuid4().hex + "@example.invalid"
            peer = root / "exit-peer"
            peer.write_text("#!" + sys.executable + "\nimport os\nos.write(1, " +
                            repr(("\x1b[6nChoose the text style\nError: spawn denied EPERM " + token + " " + email + "\n").encode()) + ")\nraise SystemExit(7)\n", encoding="utf-8")
            peer.chmod(0o700)
            original_popen = subprocess.Popen

            def completed_child(*args, **kwargs):
                child = original_popen(*args, **kwargs)
                child.wait(timeout=3)
                return child

            report, stopped = {"captured_output_secret_hits": 0}, None
            with patch.object(probe, "guarded", side_effect=lambda profile, argv: argv), \
                 patch.object(probe.subprocess, "Popen", side_effect=completed_child), \
                 patch.object(probe.os, "write", wraps=os.write) as pty_write:
                try:
                    probe.route(str(peer), "synthetic-profile", env, str(root / "cwd"), root, report, [token],
                                terminal_output=root / "terminal.txt", identities={email})
                except probe.StopProbe as error:
                    stopped = str(error)
                writes_after_exit = pty_write.call_count
            self.assertEqual(stopped, "no_authenticated_local_messages_request")
            self.assertIn("route_diagnostic", report, "快速退出也须读完 PTY 并保留安全诊断。")
            diagnostic = report["route_diagnostic"]
            self.assertGreater(diagnostic["terminal"]["bytes"], 0)
            self.assertEqual(diagnostic["exit_code_before_stop"], 7)
            self.assertEqual(writes_after_exit, 0, "已知退出后只能排空输出，不得再写 PTY。")
            self.assertEqual(diagnostic["protocol_replies"], {})
            self.assertEqual(report["startup_controls"], [])
            self.assertTrue(report["terminal_export"]["written"])
            exported = (root / "terminal.txt").read_text(encoding="utf-8")
            self.assertFalse(token in exported or email in exported or "\x1b" in exported)
            self.assertTrue(diagnostic["terminal"]["mentions_permission_error"])
            self.assertEqual(diagnostic["submission"]["matching_user_records"], 0)
            saved = json.dumps(report)
            self.assertFalse(token in saved or email in saved, "不得把终端原文写入报告。")

    def test_route_peer_needs_terminal_reply_and_records_external_prompt(self):
        with tempfile.TemporaryDirectory(prefix="t093-route-peer-") as temp:
            root = Path(temp)
            env = probe.environment(root)
            token, prompt = "t093-synthetic-" + uuid4().hex, "external prompt " + uuid4().hex
            (Path(env["CLAUDE_CONFIG_DIR"]) / ".credentials.json").write_text(
                json.dumps({"claudeAiOauth": {"accessToken": token}}), encoding="utf-8")
            server = subprocess.Popen([sys.executable, str(SOURCE.resolve()), "--sink", str(root)], cwd=root, env=env,
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
            probe.CHILDREN.append(server)
            try:
                server.stdin.write(json.dumps([token]).encode()); server.stdin.close()
                self.assertTrue(select.select([server.stdout], [], [], 5)[0])
                env["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:" + str(int(server.stdout.readline()))
                peer = root / "interactive-peer"
                peer.write_text("#!" + sys.executable + "\n" + '''import os,sys,json,tty,select,time
from pathlib import Path
import urllib.request,urllib.error
assert os.isatty(0)
tty.setraw(0)
os.write(1,b"\\x1b[6n")
received=b""
def expect(value):
    global received
    deadline=time.monotonic()+2
    while value not in received and time.monotonic()<deadline:
        if select.select([0],[],[],0.1)[0]:received+=os.read(0,4096)
    if value not in received:raise SystemExit(68)
expect(b"\\x1b[1;1R")
os.write(1,b"Choose the text style that looks best with your terminal\\n")
expect(b"1\\r")
config=Path(os.environ["CLAUDE_CONFIG_DIR"])
log=config/"projects"/"peer"/"session.jsonl"
log.parent.mkdir(parents=True)
log.write_text(json.dumps({"type":"user","message":{"role":"user","content":sys.argv[-1]}})+"\\n",encoding="utf-8")
token=json.loads((config/".credentials.json").read_text(encoding="utf-8"))["claudeAiOauth"]["accessToken"]
request=urllib.request.Request(os.environ["ANTHROPIC_BASE_URL"]+"/v1/messages",data=json.dumps({"messages":[{"role":"user","content":sys.argv[-1]}]}).encode(),headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"})
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:opener.open(request,timeout=2)
except urllib.error.HTTPError as error:assert error.code==400
''', encoding="utf-8")
                peer.chmod(0o700)
                report, stopped = {"captured_output_secret_hits": 0}, None
                with patch.object(probe, "guarded", side_effect=lambda profile, argv: argv), patch.object(probe, "PROMPT", prompt):
                    try:
                        probe.route(str(peer), "synthetic-profile", env, str(root / "cwd"), root, report, [token])
                    except probe.StopProbe as error:
                        stopped = str(error)
                self.assertIsNone(stopped, "独立终端 peer 应完成协议握手、主题按键与本地 HTTP 请求。")
                self.assertTrue(report["route_observed"])
                self.assertEqual(report["route_diagnostic"]["protocol_replies"]["cursor_position"], 1)
                self.assertEqual(report["route_diagnostic"]["submission"]["matching_user_records"], 1)
                self.assertFalse(token in json.dumps(report), "报告不得含合成凭据。")
            finally:
                probe.stop_child(server)
                server.stdout.close(); server.stderr.close()

    @unittest.skipUnless(sys.platform == "darwin", "探针入口只支持 macOS")
    def test_bound_profile_failure_stops_before_credential_read(self):
        for code, stdout in ((65, b""), (0, b"wrong version\n")):
            with self.subTest(code=code), tempfile.TemporaryDirectory(prefix="t093-order-") as temp:
                root = Path(temp)
                source_home = root / "source-home"
                source_home.mkdir()
                calls = []

                def fake_capture(argv, **kwargs):
                    calls.append(argv)
                    if len(calls) == 1:
                        return 0, b"", b""
                    if len(calls) == 2:
                        self.assertEqual(argv[-1], "--version")
                        self.assertRegex(argv[2], r'\(remote tcp4 "localhost:[0-9]+"\)')
                        self.assertEqual(list((Path(kwargs["env"]["HOME"]) / ".claude").iterdir()), [])
                        return code, stdout, b"sandbox-exec: synthetic failure"
                    raise probe.StopProbe("unexpected_post_version_capture")

                args = SimpleNamespace(claude=sys.executable, output=str(root / "report.json"), terminal_output=None,
                                       prepare_onboarding_state=False)
                with patch.object(probe.Path, "home", return_value=source_home), \
                     patch.object(probe, "capture", side_effect=fake_capture), \
                     patch.object(probe, "credentials") as read_credentials, \
                     patch.object(probe.resource, "setrlimit"), patch.object(probe.signal, "signal"), \
                     patch.object(probe.os, "umask"), patch.object(sys, "stdout", io.StringIO()):
                    exit_code = probe.run(args)
                saved = json.loads((root / "report.json").read_text(encoding="utf-8"))
                self.assertEqual(exit_code, 2)
                self.assertEqual(saved["stop_reason"], "precredential_bound_profile_cli_version_failed")
                self.assertEqual(len(calls), 2)
                self.assertFalse(read_credentials.called, "版本前检失败后不得触及凭据。")
                self.assertTrue(saved["isolated_home_removed"])

    @unittest.skipUnless(sys.platform == "darwin", "此边界只存在于 macOS")
    def test_bound_profile_compiles_without_applying_it(self):
        library = ctypes.CDLL("/usr/lib/libsandbox.1.dylib")
        library.sandbox_compile_string.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_char_p)]
        library.sandbox_compile_string.restype = ctypes.c_void_p
        library.sandbox_free_profile.argtypes = [ctypes.c_void_p]
        library.sandbox_free_error.argtypes = [ctypes.c_char_p]
        root, home, executable = Path("/private/tmp/t093-compile-fixture"), Path("/private/tmp/t093-source-fixture"), Path("/usr/bin/true")
        baseline = probe.sandbox_profile(root, home, executable)
        for port in (1, 45678, 65535):
            profile = probe.sandbox_profile(root, home, executable, port)
            error = ctypes.c_char_p()
            compiled = library.sandbox_compile_string(profile.encode(), None, ctypes.byref(error))
            try:
                self.assertTrue(bool(compiled), "带端口的 profile 必须通过本机编译器。")
                rule = '(allow network-outbound (remote tcp4 "localhost:' + str(port) + '"))'
                self.assertIn(rule, profile)
                self.assertEqual(profile.replace(rule, ""), baseline, "除指定 loopback TCP4 端口规则外，原限制不变。")
            finally:
                if compiled:
                    library.sandbox_free_profile(compiled)
                if error.value:
                    library.sandbox_free_error(error)

    def test_auth_status_keeps_only_safe_structure_and_stops_on_non_json(self):
        config = "/private/tmp/t093-synthetic-config"
        access = "t093-access-" + uuid4().hex
        refresh = "t093-refresh-" + uuid4().hex
        email = "t093-" + uuid4().hex + "@example.invalid"
        status = json.dumps({"loggedIn": True, "authMethod": "claude.ai", "configDirectory": config,
                             "email": email, "unknown": access}).encode()
        cases = [
            (0, status, b"", "json_object", True, False, False),
            (0, ("Warning: " + email + " " + access + "\n").encode() + status, b"", "warning", False, True, True),
            (1, b"", ("Error: OAuth subscription is not supported with this base URL " + email + " " + refresh).encode(), "empty", False, False, True),
            (65, b"", b"sandbox-exec: synthetic profile error\n", "empty", False, False, True),
            (0, b"[]", b"", "json_array", True, False, True),
            (1, status, b"", "json_object", True, False, True),
        ]
        for code, stdout, stderr, prefix, is_json, has_prefix, must_stop in cases:
            with self.subTest(code=code, prefix=prefix, must_stop=must_stop):
                report, stopped = {"captured_output_secret_hits": 0}, None
                calls = []

                def fake_capture(argv, **kwargs):
                    calls.append(argv)
                    return code, stdout, stderr

                with patch.object(probe, "capture", side_effect=fake_capture):
                    try:
                        probe.auth_status("/synthetic/claude", "synthetic-profile", {"CLAUDE_CONFIG_DIR": config},
                                          "/synthetic/cwd", report, "status_with_base_url", [access, refresh])
                    except probe.StopProbe as error:
                        stopped = str(error)
                self.assertIn("status_with_base_url_output", report, "失败也须保留安全结构，不能只留 not_json。")
                diagnostic = report["status_with_base_url_output"]
                self.assertEqual(diagnostic["exit_code"], code)
                self.assertEqual(diagnostic["stdout"]["prefix_kind"], prefix)
                self.assertEqual(diagnostic["stdout"]["is_json"], is_json)
                self.assertEqual(diagnostic["stdout"]["json_after_prefix"], has_prefix)
                self.assertEqual(diagnostic["stdout"]["line_count"], len(stdout.splitlines()))
                self.assertEqual(stopped is not None, must_stop)
                self.assertEqual(calls[0][-4:], ["/synthetic/claude", "auth", "status", "--json"])
                saved = json.dumps(report)
                for value in (email, access, refresh, "unknown", "synthetic profile error"):
                    self.assertFalse(value in saved, "摘要不得包含被禁止的字段或合成原文。")
                if code == 65:
                    self.assertEqual(diagnostic["stderr"]["prefix_kind"], "sandbox_exec")
                if not is_json:
                    self.assertNotIn("status_with_base_url", report)

    def test_exact_keychain_query_uses_one_explicit_keychain_with_unchanged_guards(self):
        with tempfile.TemporaryDirectory(prefix="t093-keychain-helper-") as temp:
            real_home = Path(temp) / "source-home"
            keychain = real_home / "Library/Keychains/login.keychain-db"
            keychain.parent.mkdir(parents=True)
            keychain.touch()
            isolated = Path(temp) / "isolated"
            isolated.mkdir()
            env = probe.environment(isolated)
            original_env = dict(env)
            access = "t093-synthetic-access-" + uuid4().hex
            refresh = "t093-synthetic-refresh-" + uuid4().hex
            oauth = {"accessToken": access, "refreshToken": refresh, "expiresAt": (time.time() + 3600) * 1000}
            payload = json.dumps({"claudeAiOauth": oauth, "mcpOAuth": {"must_not_copy": "synthetic-other-login"}}).encode()
            calls = []

            def fake_capture(argv, *, env, cwd, timeout):
                self.assertEqual(argv[:2], ["/usr/bin/sandbox-exec", "-p"])
                # 合同来自本次约束：原只读、无网络、禁止 fork 的 profile 不变。
                self.assertEqual(argv[2], '(version 1)(allow default)(deny file-write*)(deny network*)(deny process-fork)')
                self.assertEqual(env, original_env)
                calls.append(argv[3:])
                command = argv[3:]
                if command == ["/usr/bin/security", "find-generic-password", "-s", "Claude Code-credentials", str(keychain)]:
                    return 0, b"discarded synthetic attributes", b""
                if command == ["/usr/bin/security", "find-generic-password", "-s", "Claude Code-credentials", "-w", str(keychain)]:
                    return 0, payload, b""
                # 重现用户给出的反差：隔离 HOME 中的默认搜索返回 44。
                return 44, b"", b"synthetic item not visible in default search scope"

            report, stopped, result = {}, None, None
            with patch.object(probe, "capture", side_effect=fake_capture):
                try:
                    result = probe.credentials(real_home, env, str(isolated / "cwd"), report)
                except probe.StopProbe as error:
                    stopped = str(error)
            self.assertIsNone(stopped, "精确服务在指定钥匙串可见，不应因隔离 HOME 的默认搜索遗漏而判缺失。")
            self.assertEqual(len(calls), 2)
            self.assertEqual(result, [access, refresh])
            destination = Path(env["CLAUDE_CONFIG_DIR"]) / ".credentials.json"
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), {"claudeAiOauth": oauth})
            self.assertEqual(destination.stat().st_mode & 0o777, 0o600)
            self.assertNotIn(access, json.dumps(report))
            self.assertNotIn(refresh, json.dumps(report))

    def test_scanner_detects_sentinel_and_encoded_forms(self):
        sentinel = "t093-synthetic/" + uuid4().hex + "+secret"
        for value in (sentinel, quote(sentinel, safe=""), base64.b64encode(sentinel.encode()).decode()):
            self.assertGreater(probe.secret_hits("before " + value + " after", [sentinel]), 0)
        self.assertEqual(probe.secret_hits('{"status":"PASS"}', [sentinel]), 0)

    def test_inventory_detects_metadata_change_without_following_symlink(self):
        with tempfile.TemporaryDirectory(prefix="t093-probe-helper-") as temp:
            home = Path(temp)
            (home / ".claude").mkdir()
            (home / ".claude/history").write_text("first", encoding="utf-8")
            (home / "external").mkdir()
            (home / "external/must-not-list").touch()
            (home / "external/Keychains").mkdir()
            (home / "external/Keychains/must-not-list").touch()
            (home / ".claude/link").symlink_to(home / "external")
            (home / "Library").symlink_to(home / "external")
            before = probe.metadata(home)
            self.assertNotIn(".claude/link/must-not-list", before)
            self.assertNotIn("Library/Keychains/must-not-list", before)
            self.assertIn("Library", before)
            self.assertIn("link", before["Library"])
            (home / ".claude/history").write_text("different length", encoding="utf-8")
            after = probe.metadata(home)
            changed = [name for name in before if before[name] != after[name]]
            self.assertIn(".claude/history", changed)

    def test_capture_stops_a_process_that_ignores_sigterm(self):
        with tempfile.TemporaryDirectory(prefix="t093-probe-helper-") as temp:
            # communicate 超时后必须回收，不把超时解释为被测行为通过。
            with self.assertRaisesRegex(probe.StopProbe, "command_timeout"):
                probe.capture([sys.executable, "-c", "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(30)"],
                              env={"PATH": "/usr/bin:/bin"}, cwd=temp, timeout=0.3)
            self.assertEqual(probe.CHILDREN, [])

    def test_real_sink_separates_matching_and_wrong_bearer_without_leak(self):
        with tempfile.TemporaryDirectory(prefix="t093-probe-helper-") as temp:
            root = Path(temp)
            env = probe.environment(root)
            sentinel = "t093-synthetic-" + uuid4().hex
            credential = Path(env["CLAUDE_CONFIG_DIR"]) / ".credentials.json"
            credential.write_text(json.dumps({"claudeAiOauth": {"accessToken": sentinel}}), encoding="utf-8")
            self.assertTrue(credential.is_relative_to(Path(env["HOME"])))
            child = subprocess.Popen([sys.executable, str(SOURCE.resolve()), "--sink", str(root)],
                                     cwd=root, env=env, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
            probe.CHILDREN.append(child)
            try:
                child.stdin.write(json.dumps([sentinel]).encode("utf-8"))
                child.stdin.close()
                self.assertTrue(select.select([child.stdout], [], [], 5)[0])
                port = int(child.stdout.readline())
                replacement = "t093-replacement-" + uuid4().hex
                cases = [("/v1/messages", sentinel), ("/v1/messages", replacement),
                         ("/v1/messages", "wrong-synthetic-token"),
                         ("/v1/messages/" + quote(sentinel, safe=""), sentinel),
                         ("/v1/messages", sentinel)]
                for index, (path, token) in enumerate(cases):
                    if index == 1:
                        credential.write_text(json.dumps({"claudeAiOauth": {"accessToken": replacement}}), encoding="utf-8")
                    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
                    body = json.dumps({"messages": [{"role": "user", "content": "sentinel-body-" + str(index)}]})
                    connection.request("POST", path + "?not-retained=" + sentinel, body,
                                       {"Authorization": "Bearer " + token, "Content-Type": "application/json"})
                    response = connection.getresponse()
                    self.assertEqual(response.status, 400)
                    self.assertIn(b"No upstream exists", response.read())
                    connection.close()
                observed = probe.rows(root)
                self.assertEqual(len(observed), 5)
                self.assertEqual([row["bearer_matches_copied_login"] for row in observed], [True, False, False, True, True])
                self.assertEqual([row["path"] for row in observed], ["/v1/messages"] * 3 + ["<credential-redacted>", "/v1/messages"])
                self.assertGreater(observed[3]["path_credential_hits"], 0)
                self.assertTrue(all(row["has_messages"] for row in observed))
                raw = (root / "home/requests.jsonl").read_text(encoding="utf-8")
                self.assertNotIn(sentinel, raw)
                self.assertNotIn("sentinel-body", raw)
            finally:
                probe.stop_child(child)
                child.stdout.close()
                child.stderr.close()
        self.assertFalse(root.exists())


if __name__ == "__main__":
    suite = (unittest.defaultTestLoader.loadTestsFromNames(sys.argv[1:], module=sys.modules[__name__])
             if len(sys.argv) > 1 else unittest.defaultTestLoader.loadTestsFromTestCase(ProbeSafety))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({"status": "PASS" if result.wasSuccessful() else "INCOMPLETE",
                      "scope": "synthetic probe helper checks only", "checks": result.testsRun,
                      "real_cli_starts": 0, "real_credential_reads": 0}))
    sys.exit(0 if result.wasSuccessful() else 1)
