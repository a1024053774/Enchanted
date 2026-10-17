#!/usr/bin/env python3
"""只验证 T-093 探针辅助逻辑；不运行 Claude、不读取任何真实凭据。"""
import base64
import http.client
import importlib.util
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import quote
from uuid import uuid4


SOURCE = Path(__file__).with_name("probe_t093_normal_login.py")
spec = importlib.util.spec_from_file_location("t093_probe", SOURCE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ProbeSafety(unittest.TestCase):
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
