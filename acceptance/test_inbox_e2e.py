"""T-053 contract evidence through the real CLI and filesystem (Python stdlib).

Run: python3 -B acceptance/test_inbox_e2e.py --artifacts <new-directory>
INBOX_SCRIPT selects a frozen candidate/mutant. No product module is imported.
Fixtures and expected lists were authored from T-053 rev 1 / spec sections 3–5.
Each run retains fixture files and every command/output, including failures.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import unittest


REPO = Path(__file__).resolve().parents[1]
SCRIPT = Path(os.environ.get("INBOX_SCRIPT", str(REPO / "scripts/inbox"))).resolve()
NOW = "2026-10-09T12:00:00Z"
COMMANDS = []
ARTIFACTS = None


def fixture_entry(directory, ident, sender="worker:sentinel", recipient="executor",
                  kind="report", created="2026-10-09T11:00:00Z", reply="", **extra):
    # Fixture serializer belongs to the oracle, not production code.
    values = dict(id=ident, **{"from": sender}, to=recipient, kind=kind,
                  reply_to=reply, refs=[], created_at=created, schema=1, **extra)
    text = "---\n" + "".join(f"{key}: {json.dumps(value, ensure_ascii=False)}\n"
                               for key, value in values.items()) + "---\n\n正文：独立夹具\n"
    (directory / (ident + ".md")).write_text(text, encoding="utf-8")


def output_ids(stdout):
    # Public record heading: ENTRY <id> <kind> <from> → <to> [status].
    return [line.split()[1] for line in stdout.splitlines() if line.startswith("ENTRY ")]


class InboxCLI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not SCRIPT.is_file():
            raise AssertionError("EXPECTED_RED missing feature: CLI entry point does not exist: " + str(SCRIPT))

    def setUp(self):
        self.root = ARTIFACTS / self._testMethodName
        self.root.mkdir()
        self.map = self.root / ".project-map"
        self.inbox = self.map / "inbox"
        self.roles = self.map / "roles"
        self.tickets = self.map / "tickets"
        for directory in (self.inbox, self.roles, self.tickets):
            directory.mkdir(parents=True)
        for role in ("ideation", "executor"):
            (self.roles / (role + ".md")).write_text("角色卡 sentinel " + role + "\n", encoding="utf-8")
        self.env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")

    def argv(self, *args, now=NOW):
        return [str(SCRIPT), "--root", str(self.root), "--now", now, *args]

    def record(self, argv, p):
        COMMANDS.append(dict(argv=argv, cwd=str(self.root), exit_code=p.returncode,
                             stdout=p.stdout, stderr=p.stderr))
        return p

    def cli(self, *args, code=0, now=NOW):
        argv = self.argv(*args, now=now)
        p = subprocess.run(argv, cwd=self.root, env=self.env, text=True,
                           capture_output=True, timeout=20)
        self.record(argv, p)
        self.assertEqual(p.returncode, code, p.stdout + p.stderr)
        return p

    def send(self, *args, code=0, now=NOW):
        return self.cli("send", "--from", "worker:sentinel", "--to", "executor",
                        "--kind", "report", "--body", "正文：引号\" / 多行\n⟦⟧ café", *args, code=code, now=now)

    def snapshot(self):
        return {p.name: p.read_bytes() for p in self.inbox.iterdir()}

    def test_tracer_bullet_and_immutable_duplicate(self):
        p = self.send("--id", "slice", "--title", "输入 nonce café")
        self.assertIn("slice", p.stdout)
        before = self.snapshot()
        listed = self.cli("list", "--role", "executor")
        self.assertTrue(listed.stdout.startswith("角色卡 sentinel executor\n"))
        self.assertEqual(output_ids(listed.stdout), ["slice"])
        self.assertIn('正文：引号" / 多行\n⟦⟧ café', listed.stdout)
        self.send("--id", "slice", code=1)
        self.assertEqual(before, self.snapshot())
        self.cli("ack", "--role", "executor", "--id", "slice")
        self.assertEqual(before["slice.md"], (self.inbox / "slice.md").read_bytes())
        self.assertEqual(output_ids(self.cli("list", "--role", "executor").stdout), [])
        after = self.snapshot()
        self.cli("ack", "--role", "executor", "--id", "slice")
        self.assertEqual(after, self.snapshot(), "重复确认应无副作用")

    def test_recipient_ack_and_dangling_reply(self):
        for ident in ("a", "b", "c", "d"):
            fixture_entry(self.inbox, ident)
        fixture_entry(self.inbox, "e", recipient="ideation")
        for ident, target, role in (("aa", "a", "executor"), ("ab", "b", "ideation"),
                                    ("ac1", "c", "ideation"), ("ac2", "c", "executor")):
            fixture_entry(self.inbox, ident, sender=role, recipient="worker:sentinel", kind="ack", reply=target)
        self.assertEqual(output_ids(self.cli("list", "--role", "executor").stdout), ["b", "d"])
        self.assertEqual(output_ids(self.cli("list", "--role", "ideation").stdout), ["e"])
        before = self.snapshot()
        self.cli("ack", "--role", "ideation", "--id", "d", code=1)
        self.cli("send", "--from", "ideation", "--to", "worker:sentinel", "--kind", "ack",
                 "--reply-to", "d", "--body", "伪造", code=1)
        self.send("--reply-to", "missing", code=1)
        self.assertEqual(before, self.snapshot())
        self.cli("ack", "--role", "executor", "--id", "b")
        self.assertEqual(before["b.md"], (self.inbox / "b.md").read_bytes())
        self.assertEqual(output_ids(self.cli("list", "--role", "executor").stdout), ["d"])
        fixture_entry(self.inbox, "dangling", reply="absent")
        fixture_entry(self.inbox, "chain", reply="dangling")
        p = self.cli("list", "--role", "executor", code=1)
        self.assertEqual(output_ids(p.stdout), ["d"])
        self.assertIn("dangling.md", p.stderr)
        self.assertIn("chain.md", p.stderr)

    def test_concurrent_twenty_and_clock_rollback(self):
        handles = []
        launcher = "import os,sys; sys.stdin.buffer.read(1); os.execv(sys.argv[1], sys.argv[1:])"
        for i in range(20):
            argv = self.argv("send", "--from", "worker:parallel", "--to", "executor",
                             "--kind", "report", "--body", "nonce-" + str(i))
            p = subprocess.Popen([sys.executable, "-B", "-c", launcher, *argv], stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=self.root, env=self.env)
            handles.append((argv, p))
        for _, p in handles:
            p.stdin.write("x")
            p.stdin.flush()
        results = []
        for argv, p in handles:
            stdout, stderr = p.communicate(timeout=20)
            self.record(argv, subprocess.CompletedProcess(argv, p.returncode, stdout, stderr))
            results.append((p.returncode, stdout, stderr))
        self.assertEqual([code for code, _, _ in results], [0] * 20, repr(results))
        files = sorted(self.inbox.glob("*.md"))
        self.assertEqual(len(files), 20)
        ids = [stdout.strip() for _, stdout, _ in results]
        self.assertEqual(len(set(ids)), 20)
        self.assertEqual({p.read_text(encoding="utf-8").split("---\n", 2)[2].strip() for p in files},
                         {"nonce-" + str(i) for i in range(20)})
        self.assertEqual(len(output_ids(self.cli("list", "--role", "executor").stdout)), 20)
        self.send(now=NOW)
        self.send(now="2026-10-09T11:59:00Z")
        self.send(now=NOW)
        self.assertEqual(len(list(self.inbox.glob("*.md"))), 23)

    def test_kill_during_write_never_publishes_partial_entry(self):
        # Fault-injection only in this owned child: stop after a real short write.
        # The candidate's main, O_EXCL creation and atomic publication run unchanged.
        launcher = '''import os,runpy,sys,time
original = os.write
def short_write(fd, data):
    result = original(fd, data[:17])
    original(2, b"REAL_PARTIAL_WRITE\\n")
    time.sleep(60)
    return result
os.write = short_write
script = sys.argv.pop(1)
sys.argv[0] = script
runpy.run_path(script, run_name="__main__")
'''
        argv = [sys.executable, "-B", "-c", launcher, *self.argv("send", "--from", "worker:kill",
                "--to", "executor", "--kind", "report", "--body", "x" * 5000)]
        p = subprocess.Popen(argv, cwd=self.root, env=self.env, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            import select
            self.assertTrue(select.select([p.stderr], [], [], 10)[0], "未到实际文件写入边界")
            marker = p.stderr.readline()
            self.assertEqual(marker, "REAL_PARTIAL_WRITE\n")
            p.kill()
            stdout, stderr = p.communicate(timeout=10)
            self.record(argv, subprocess.CompletedProcess(argv, p.returncode, stdout, marker + stderr))
            self.assertEqual(p.returncode, -signal.SIGKILL)
            staged = list((self.map / ".inbox-staging").glob("*.tmp"))
            self.assertEqual(len(staged), 1)
            self.assertEqual(staged[0].stat().st_size, 17)
            self.assertEqual(list(self.inbox.glob("*.md")), [])
            self.assertEqual(output_ids(self.cli("list", "--role", "executor").stdout), [])
            self.send("--id", "after-kill")
        finally:
            if p.poll() is None:
                p.kill()
                p.wait(timeout=5)

    def test_path_refs_utf8_and_long_body(self):
        before = self.snapshot()
        for ref in ("missing.md", "file:missing.md#L2", "../outside.md", "file:../outside.md#L1", "ticket:T-absent"):
            self.send("--ref", ref, code=1)
        for body in ("missing.txt", "../outside.txt", ""):
            self.cli("send", "--from", "worker:sentinel", "--to", "executor", "--kind", "report",
                     "--body-file", body, code=1)
        (self.root / "bad.txt").write_bytes(b"\xff\xfe")
        self.cli("send", "--from", "worker:sentinel", "--to", "executor", "--kind", "report",
                 "--body-file", "bad.txt", code=1)
        self.assertEqual(before, self.snapshot())
        self.send("--id", "", code=1)
        (self.root / "safe.txt").write_text("valid", encoding="utf-8")
        (self.root / "escape").symlink_to(self.root.parent, target_is_directory=True)
        self.send("--ref", "escape/ORACLE.md", code=1)
        text = "长正文é\n" * 200000
        (self.root / "long.txt").write_text(text, encoding="utf-8")
        self.cli("send", "--from", "worker:sentinel", "--to", "executor", "--kind", "report",
                 "--body-file", "long.txt", "--ref", "file:safe.txt#L1", "--id", "long")
        self.assertEqual((self.inbox / "long.md").read_text(encoding="utf-8").split("---\n", 2)[2], "\n" + text)
        for command in ("edit", "delete"):
            self.cli(command, code=1)

    def test_issue_statuses_and_user_view(self):
        def issue(ident, created="2026-10-09T11:46:00Z", blocking=False):
            fixture_entry(self.inbox, ident, kind="issue", recipient="triage", created=created,
                          title="标题-" + ident, blocking=blocking)
        for ident in ("pending", "close", "dismiss", "forward", "snooze", "reopen", "needs", "answered", "delivered"):
            issue(ident)
        issue("expired", created="2026-10-09T11:44:00Z")
        issue("blocking", blocking=True)
        for target, action in (("close", "close"), ("dismiss", "dismiss"), ("forward", "forward"),
                               ("snooze", "snooze"), ("reopen", "reopen"), ("needs", "needs-user")):
            fixture_entry(self.inbox, "disp-" + target, sender="user" if action == "dismiss" else "executor",
                          recipient="triage", kind="disposition", reply=target,
                          created="2026-10-09T11:55:00Z", action=action, reason="独立理由", basis="独立依据")
        for target in ("answered", "delivered"):
            fixture_entry(self.inbox, "answer-" + target, sender="ideation", recipient="executor", kind="answer",
                          reply=target, created="2026-10-09T11:56:00Z", certainty="relayed", bundle_id="fixture-bundle")
        fixture_entry(self.inbox, "disp-delivered", sender="executor", recipient="triage", kind="disposition",
                      reply="delivered", created="2026-10-09T11:57:00Z", action="delivered")
        p = self.cli("list", "--role", "executor")
        expected = dict(pending="待判断", expired="等你决定", blocking="等你决定", close="已关闭",
                        dismiss="已关闭", forward="已转交", snooze="稍后", reopen="等你决定",
                        needs="等你决定", answered="已答复", delivered="已送达")
        for ident, status in expected.items():
            heading = next(line for line in p.stdout.splitlines() if line.startswith("ENTRY " + ident + " "))
            self.assertTrue(heading.endswith("[" + status + "]"), heading)
        self.assertEqual(set(output_ids(self.cli("list", "--role", "user").stdout)), {"expired", "blocking", "reopen", "needs"})
        late = self.cli("list", "--role", "user", now="2026-10-09T12:55:00Z")
        self.assertEqual(set(output_ids(late.stdout)), {"pending", "expired", "blocking", "forward", "snooze", "reopen", "needs"})
        self.assertIn("独立理由", p.stdout)
        # Sender restrictions, required evidence, and blocking close are mechanical.
        before = self.snapshot()
        for target, actor, action in (("blocking", "executor", "close"), ("pending", "executor", "dismiss"),
                                       ("pending", "worker:sentinel", "close")):
            self.cli("send", "--from", actor, "--to", "triage", "--kind", "disposition", "--reply-to", target,
                     "--action", action, "--reason", "理由", "--basis", "依据", "--body", "", code=1)
        self.cli("send", "--from", "executor", "--to", "triage", "--kind", "disposition", "--reply-to", "pending",
                 "--action", "close", "--body", "理由写在正文不等于结构字段", code=1)
        self.assertEqual(before, self.snapshot())
        self.cli("send", "--from", "executor", "--to", "triage", "--kind", "disposition", "--reply-to", "pending",
                 "--action", "close", "--reason", "确已解决", "--basis", "证据 nonce", "--body", "")
        self.assertNotIn("pending", output_ids(self.cli("list", "--role", "user", now="2026-10-09T13:00:00Z").stdout))

    def test_answer_metadata_contract(self):
        fixture_entry(self.inbox, "question", recipient="triage", kind="issue", title="独立问题", blocking=True)
        for ident, extra in (("answer-auto", []), ("answer-explicit", ["--bundle-id", "sentinel-bundle", "--certainty", "relayed"])):
            self.cli("send", "--from", "ideation", "--to", "executor", "--kind", "answer", "--reply-to", "question",
                     "--ref", "issue:question", "--ref", "worker:sentinel", "--id", ident,
                     "--body", "问题 1：独立问题\n用户答复：逐字 café Ω", *extra)
            text = (self.inbox / (ident + ".md")).read_text(encoding="utf-8")
            fields = {key: json.loads(raw.strip()) for key, raw in (line.split(":", 1) for line in text.split("---\n", 2)[1].splitlines())}
            self.assertEqual(fields.get("certainty"), "relayed")
            self.assertTrue(fields.get("bundle_id"))
            if extra:
                self.assertEqual(fields["bundle_id"], "sentinel-bundle")
            self.assertEqual(text.split("---\n", 2)[2], "\n问题 1：独立问题\n用户答复：逐字 café Ω")
        self.send("--bundle-id", "not-an-answer", code=1)

    def test_envelope_typed_refs(self):
        refs = ["task:task-nonce", "thread:thread-nonce", "turn:turn-nonce", "message:message-nonce",
                "request:request-nonce", "input:input-nonce", "commit:abcdef123456"]
        arguments = [argument for ref in refs for argument in ("--ref", ref)]
        self.send("--id", "with-typed-refs", *arguments)
        listed = self.cli("list", "--role", "executor")
        for ref in refs:
            self.assertIn(ref, listed.stdout)

    def test_offset_timestamps(self):
        self.send("--id", "with-typed-refs")
        fixture_entry(self.inbox, "offset-earlier", created="2026-10-09T07:59:00-04:00")
        self.assertEqual(output_ids(self.cli("list", "--role", "executor").stdout), ["offset-earlier", "with-typed-refs"])
        self.send("--id", "offset-now", now="2026-10-09T14:01:00+02:00")
        text = (self.inbox / "offset-now.md").read_text(encoding="utf-8")
        self.assertIn('created_at: "2026-10-09T12:01:00Z"', text)

    def test_ready_contract(self):
        cases = [
            ("T-001", {}), ("T-002", {"ready": "no"}),
            ("T-003", {"ready_by": ""}), ("T-004", {"ready_rev": ""}),
            ("T-005", {"blocked_by": ["T-001"]}), ("T-006", {"claimed_by": "other"}),
            ("T-007", {"status": "closed"}), ("T-008", {"status": "superseded"}),
            ("T-009", {"status": "out-of-scope"}), ("T-010", {"type": "decide"}),
            ("T-011", {}), ("T-012", {"type": "task"}), ("T-013", {"type": "research"}),
            ("T-014", {"blocked_by": ["T-007", "T-008"]}),
        ]
        for ident, overrides in cases:
            values = dict(id=ident, title="sentinel-" + ident, type="build", status="open",
                          blocked_by=[], claimed_by="", ready="yes", ready_by="ideation", ready_rev=1)
            if ident == "T-001":
                values.pop("ready")
            values.update(overrides)
            for field in ("ready_by", "ready_rev"):
                if values.get(field) == "":
                    values.pop(field)
            text = "---\n" + "".join(key + ": " + (json.dumps(value) if isinstance(value, list) else str(value)) + "\n"
                                     for key, value in values.items()) + "---\n"
            (self.tickets / (ident + "-case.md")).write_text(text, encoding="utf-8")
        p = self.cli("ready", code=1)
        ids = [line.split()[1] for line in p.stdout.splitlines() if line.startswith("READY ")]
        self.assertEqual(ids, ["T-011", "T-012", "T-013", "T-014"])
        for ident in ("T-001", "T-003", "T-004"):
            self.assertIn(ident, p.stderr)

    def test_missing_card_and_session_copy_reminder(self):
        # Missing-card fixture removal only; product has no deletion entry point.
        (self.roles / "executor.md").unlink()
        self.cli("list", "--role", "executor", code=1)
        (self.roles / "executor.md").write_text("卡片\n", encoding="utf-8")
        self.assertNotIn("提醒", self.cli("list", "--role", "executor").stdout)
        folder = self.root / "evidence/batch/sessions"
        folder.mkdir(parents=True)
        manifest = folder / "manifest.jsonl"
        manifest.write_text(json.dumps({"cutoff_at": "2026-10-02T11:59:59Z", "session_id": "fixture"}) + "\n", encoding="utf-8")
        self.assertIn("提醒", self.cli("list", "--role", "executor").stdout)
        with manifest.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"cutoff_at": "2026-10-08T12:00:00Z", "session_id": "fixture"}) + "\n")
        self.assertNotIn("提醒", self.cli("list", "--role", "executor").stdout)

    def test_malformed_entries_fail_visibly(self):
        fixture_entry(self.inbox, "valid")
        (self.inbox / "broken.md").write_text("---\nfrom: bad\n", encoding="utf-8")
        (self.inbox / "nonutf.md").write_bytes(b"\xff")
        before = self.snapshot()
        p = self.cli("list", "--role", "executor", code=1)
        self.assertEqual(output_ids(p.stdout), ["valid"])
        self.assertIn("broken.md", p.stderr)
        self.assertIn("nonutf.md", p.stderr)
        self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("tests", nargs="*")
    opts = parser.parse_args()
    ARTIFACTS = opts.artifacts.resolve()
    ARTIFACTS.mkdir(parents=True, exist_ok=False)
    suite = unittest.defaultTestLoader.loadTestsFromNames(opts.tests, module=sys.modules[__name__]) if opts.tests else unittest.defaultTestLoader.loadTestsFromTestCase(InboxCLI)
    with (ARTIFACTS / "output.txt").open("x", encoding="utf-8") as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (ARTIFACTS / "commands.json").write_text(json.dumps(COMMANDS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ARTIFACTS / "run.json").write_text(json.dumps(dict(script=str(SCRIPT), python=sys.version,
        argv=sys.argv, tests=result.testsRun, failures=len(result.failures), errors=len(result.errors)), indent=2) + "\n", encoding="utf-8")
    print((ARTIFACTS / "output.txt").read_text(encoding="utf-8"))
    sys.exit(0 if result.wasSuccessful() else 1)
