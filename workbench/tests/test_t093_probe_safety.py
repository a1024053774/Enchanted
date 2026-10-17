#!/usr/bin/env python3
"""只验证 T-093 探针辅助逻辑；不运行 Claude、不读取任何真实凭据。"""
import base64
import ctypes
import http.client
import importlib.util
import io
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from urllib.parse import quote
from uuid import uuid4


SOURCE = Path(__file__).with_name("probe_t093_normal_login.py")
spec = importlib.util.spec_from_file_location("t093_probe", SOURCE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ProbeSafety(unittest.TestCase):
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

                args = SimpleNamespace(claude=sys.executable, output=str(root / "report.json"))
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
