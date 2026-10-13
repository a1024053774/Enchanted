"""T-054 rev 1: real CLI/filesystem, explicitly fake Herdr, no provider calls.

Replay: python3 -B acceptance/test_dispatch_session_e2e.py --artifacts NEW_DIR
DISPATCH_SCRIPT / SESSION_COPY_SCRIPT select frozen candidates or mutants.
Requirements supply expected results; product modules are never imported.
"""
import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
import uuid

REPO = Path(__file__).resolve().parents[1]
DISPATCH = Path(os.environ.get("DISPATCH_SCRIPT", REPO / "scripts/dispatch")).resolve()
COPY = Path(os.environ.get("SESSION_COPY_SCRIPT", REPO / "scripts/session-copy")).resolve()
ARTIFACTS = None
COMMANDS = []


class Contract(unittest.TestCase):
    def setUp(self):
        self.root = ARTIFACTS / self._testMethodName
        self.root.mkdir()
        self.roles = self.root / ".project-map/roles"
        self.roles.mkdir(parents=True)
        for role in ("worker", "reviewer", "monitor"):
            (self.roles / (role + ".md")).write_text("独立角色卡 " + role + " café\n", encoding="utf-8")
        fakebin = self.root / "explicitly-fake-herdr-bin"
        fakebin.mkdir()
        fake = fakebin / "herdr"
        fake.write_text("#!" + sys.executable + "\n" + '''
# EXPLICIT HERDR TEST DOUBLE: never connects to a server or a real pane.
import json, os, sys
from pathlib import Path
Path(os.environ['FAKE_CALL_DIR'], str(os.getpid())+'.json').write_text(
    json.dumps({'argv':sys.argv[1:]},ensure_ascii=False),encoding='utf-8')
print('fake stdout sentinel')
print('agent_blocked' if os.environ.get('FAKE_EXIT')=='7' else 'fake stderr sentinel',file=sys.stderr)
sys.exit(int(os.environ.get('FAKE_EXIT','0')))
''', encoding="utf-8")
        fake.chmod(0o755)
        self.calls = self.root / "fake-calls"
        self.calls.mkdir()
        self.env = dict(os.environ, PATH=str(fakebin)+os.pathsep+os.environ["PATH"],
                        FAKE_CALL_DIR=str(self.calls), PYTHONDONTWRITEBYTECODE="1")

    def run_cli(self, script, args, code=0, env=None):
        argv = [sys.executable, "-B", str(script), "--root", str(self.root), *args]
        p = subprocess.run(argv, capture_output=True, text=True, env=env or self.env, timeout=20)
        COMMANDS.append(dict(argv=argv, exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr))
        self.assertEqual(p.returncode, code, p.stdout+p.stderr)
        return p

    def dispatch(self, body, agent="sentinel", role="worker", batch="batch-a", code=0, env=None, extra=()):
        return self.run_cli(DISPATCH, ["--batch", batch, "--agent", agent, "--role", role,
                                      "--body", body, *extra], code=code, env=env)

    def logs(self, batch="batch-a"):
        return [json.loads(line) for line in (self.root / "evidence" / batch / "dispatch.jsonl").read_text(encoding="utf-8").splitlines()]

    def receipts(self):
        return [json.loads(p.read_text(encoding="utf-8"))["argv"] for p in self.calls.glob("*.json")]

    def copy(self, source, batch="batch-a", sid="native-sentinel", code=0):
        return self.run_cli(COPY, ["--batch", batch, "--provider", "codex", "--session-id", sid,
                                  "--source", str(source)], code=code)

    def manifest(self, batch="batch-a"):
        return [json.loads(line) for line in (self.root / "evidence" / batch / "sessions/manifest.jsonl").read_text(encoding="utf-8").splitlines()]

    def test_dispatch_multiline_roles_and_append(self):
        self.assertTrue(DISPATCH.is_file(), "EXPECTED_RED dispatch entry point missing")
        body = '输入 ' + uuid.uuid4().hex + '\n"单引号\'" ⟦主控 #999⟧\n末行\n'
        for role in ("worker", "reviewer", "monitor"):
            self.dispatch(body, agent=role, role=role)
            self.dispatch(body+"后续", agent=role, role=role)
        rows = self.logs()
        prepared = [r for r in rows if r["phase"] == "prepared"]
        completed = [r for r in rows if r["phase"] == "completed"]
        self.assertEqual(len(prepared), 6)
        self.assertEqual(len(completed), 6)
        self.assertEqual([r["sequence"] for r in prepared], [1, 2, 3, 4, 5, 6])
        self.assertEqual(sorted(r["text"] for r in completed), sorted(a[3] for a in self.receipts()))
        for r in completed:
            first = r["sequence"] % 2 == 1
            expected = f'⟦主控 #{r["sequence"]}⟧\n' + body + ("" if first else "后续")
            if first:
                expected += "\n\n" + "独立角色卡 " + r["role"] + " café\n"
            self.assertEqual(r["text"], expected)
            self.assertEqual(r["exit_code"], 0)
            self.assertEqual(r["role_card_attached"], first)
        self.dispatch("新批首条", batch="batch-b")
        self.assertTrue(self.logs("batch-b")[-1]["role_card_attached"])

    def test_dispatch_concurrency(self):
        self.assertTrue(DISPATCH.is_file(), "EXPECTED_RED dispatch entry point missing")
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda i: self.dispatch(f"并发独立输入 {i}"), range(16)))
        rows = [r for r in self.logs() if r["phase"] == "completed"]
        self.assertEqual(sorted(r["sequence"] for r in rows), list(range(1, 17)))
        self.assertEqual(sum(r["role_card_attached"] for r in rows), 1)
        self.assertEqual(sorted(r["text"] for r in rows), sorted(a[3] for a in self.receipts()))

    def test_dispatch_failure_transparency_and_no_retry(self):
        self.assertTrue(DISPATCH.is_file(), "EXPECTED_RED dispatch entry point missing")
        env = dict(self.env, FAKE_EXIT="7")
        p = self.dispatch("失败输入", code=7, env=env, extra=("--wait", "--timeout", "1234"))
        self.assertEqual(p.stdout, "fake stdout sentinel\n")
        self.assertEqual(p.stderr, "agent_blocked\n")
        self.assertEqual(len(self.receipts()), 1)
        self.assertEqual(self.receipts()[0][4:], ["--wait", "--timeout", "1234"])
        self.assertEqual(self.logs()[-1]["exit_code"], 7)
        empty = self.root / "empty-path"
        empty.mkdir()
        self.dispatch("命令缺失", code=127, env=dict(self.env, PATH=str(empty)))
        self.assertEqual(self.logs()[-1]["exit_code"], 127)
        self.assertEqual(len(self.receipts()), 1)

    def test_body_file_preserves_crlf_and_claude_bytes(self):
        self.assertTrue(DISPATCH.is_file(), "EXPECTED_RED dispatch entry point missing")
        self.assertTrue(COPY.is_file(), "EXPECTED_RED session-copy entry point missing")
        source = self.root / "opaque.txt"
        content = '文件输入 "\r\n⟦⟧\r\n'.encode("utf-8")
        source.write_bytes(content)
        self.run_cli(DISPATCH, ["--batch", "batch-a", "--agent", "file-sentinel", "--role", "worker",
                                "--body-file", str(source)])
        self.assertEqual(self.receipts()[0][3], '⟦主控 #1⟧\n'+content.decode()+"\n\n独立角色卡 worker café\n")
        self.run_cli(COPY, ["--batch", "batch-a", "--provider", "claude", "--session-id", "claude-sentinel",
                            "--source", str(source)])
        row = self.manifest()[0]
        self.assertEqual(row["provider"], "claude")
        self.assertEqual((self.root / "evidence/batch-a/sessions" / row["copy_file"]).read_bytes(), content)

    def test_copy_concurrent_requests_do_not_duplicate_range(self):
        self.assertTrue(COPY.is_file(), "EXPECTED_RED session-copy entry point missing")
        source = self.root / "concurrent-native"
        payload = b'opaque concurrent bytes\xff' * 8192
        source.write_bytes(payload)
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(lambda i:self.copy(source, batch=f"batch-{i}"), range(6)))
        paths = list((self.root / "evidence").glob("*/sessions/manifest.jsonl"))
        self.assertEqual(len(paths), 1)
        rows = [json.loads(line) for line in paths[0].read_text(encoding="utf-8").splitlines()]
        self.assertEqual([(r["start_byte"], r["end_byte"]) for r in rows], [(0, len(payload))])

    def test_dispatch_unwritable_or_damaged_log_prevents_send(self):
        self.assertTrue(DISPATCH.is_file(), "EXPECTED_RED dispatch entry point missing")
        batch = self.root / "evidence/batch-a"
        batch.mkdir(parents=True)
        (batch / "dispatch.jsonl").mkdir()
        self.dispatch("不能记录就不能发送", code=1)
        self.assertEqual(self.receipts(), [])
        (batch / "dispatch.jsonl").rmdir()
        (batch / "dispatch.jsonl").write_bytes(b'{"broken":')
        self.dispatch("损坏记录", code=1)
        self.assertEqual(self.receipts(), [])
        self.assertEqual((batch / "dispatch.jsonl").read_bytes(), b'{"broken":')

    def test_copy_incremental_cross_batch_and_git(self):
        self.assertTrue(COPY.is_file(), "EXPECTED_RED session-copy entry point missing")
        source = self.root / "opaque-native.jsonl"
        initial = b'\x00not-json\xff\n' + "中文 字节\n".encode()
        added = '新段 " ⟦⟧\n'.encode()
        source.write_bytes(initial)
        self.copy(source)
        source.write_bytes(initial+added)
        self.copy(source)
        self.copy(source)  # no newly added bytes: no duplicate range
        source.write_bytes(initial+added+b'next-batch\x80')
        self.copy(source, batch="batch-b")
        rows = self.manifest()+self.manifest("batch-b")
        self.assertEqual([(r["start_byte"], r["end_byte"]) for r in rows],
                         [(0, len(initial)), (len(initial), len(initial+added)),
                          (len(initial+added), len(initial+added+b'next-batch\x80'))])
        for batch, row, expected in zip(("batch-a", "batch-a", "batch-b"), rows,
                                        (initial, added, b'next-batch\x80')):
            chunk = self.root / "evidence" / batch / "sessions" / row["copy_file"]
            self.assertEqual(chunk.read_bytes(), expected)
            self.assertEqual(row["size_bytes"], len(expected))
            self.assertEqual(row["source_path"], str(source.resolve()))
            self.assertEqual(row["session_id"], "native-sentinel")
            self.assertIn("cutoff_at", row)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / ".gitignore").write_bytes((REPO / ".gitignore").read_bytes())
        manifest = self.root / "evidence/batch-a/sessions/manifest.jsonl"
        chunk = manifest.parent / rows[0]["copy_file"]
        ignored = subprocess.run(["git", "-C", str(self.root), "check-ignore", str(chunk)], capture_output=True, text=True)
        self.assertEqual(ignored.returncode, 0)
        visible = subprocess.run(["git", "-C", str(self.root), "status", "--short", "--untracked-files=all"], capture_output=True, text=True, check=True)
        self.assertIn("evidence/batch-a/sessions/manifest.jsonl", visible.stdout)
        self.assertNotIn(rows[0]["copy_file"], visible.stdout)
        subprocess.run(["git", "-C", str(self.root), "add", "evidence/batch-a/sessions/manifest.jsonl"], check=True)
        tracked = subprocess.run(["git", "-C", str(self.root), "ls-files"], capture_output=True, text=True, check=True)
        self.assertIn("evidence/batch-a/sessions/manifest.jsonl", tracked.stdout)
        COMMANDS.append(dict(git_check_ignore=ignored.stdout, git_status=visible.stdout, git_ls_files=tracked.stdout))

    def test_copy_rejects_truncation_rotation_missing_and_corrupt_manifest(self):
        self.assertTrue(COPY.is_file(), "EXPECTED_RED session-copy entry point missing")
        source = self.root / "native.jsonl"
        source.write_bytes(b'opaque initial content\xff')
        self.copy(source)
        directory = self.root / "evidence/batch-a/sessions"
        before = {p.name:p.read_bytes() for p in directory.iterdir()}
        source.write_bytes(b'short')
        self.copy(source, code=1)
        self.assertEqual(before, {p.name:p.read_bytes() for p in directory.iterdir()})
        source.rename(self.root / "rotated-original")
        source.write_bytes(b'replacement longer than original source')
        self.copy(source, code=1)
        self.assertEqual(before, {p.name:p.read_bytes() for p in directory.iterdir()})
        self.copy(self.root / "missing", sid="absent", code=1)
        manifest = directory / "manifest.jsonl"
        row = self.manifest()[0]
        row["end_byte"] += 1
        manifest.write_text(json.dumps(row)+"\n", encoding="utf-8")
        damaged = manifest.read_bytes()
        self.copy(source, code=1)
        self.assertEqual(manifest.read_bytes(), damaged)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", required=True)
    args, remaining = parser.parse_known_args()
    ARTIFACTS = Path(args.artifacts).resolve()
    ARTIFACTS.mkdir(parents=True, exist_ok=False)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Contract)
    if remaining:
        suite = unittest.defaultTestLoader.loadTestsFromNames(remaining, module=sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    (ARTIFACTS / "commands.json").write_text(json.dumps(COMMANDS, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    sys.exit(0 if result.wasSuccessful() else 1)
