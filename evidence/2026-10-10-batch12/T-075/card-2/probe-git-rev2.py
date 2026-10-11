"""真实 Git 协议探针；不调用或修改门禁，不终止进程。"""
import argparse
import base64
import datetime
import json
import os
from pathlib import Path
import selectors
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import traceback


REF = "refs/heads/main"
BASE = Path(__file__).resolve().parent


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Probe:
    def __init__(self, label, root=None):
        self.out = BASE / label
        self.out.mkdir(exist_ok=False)
        self.root = root or Path(tempfile.mkdtemp(prefix="a2a-t075-2-git-", dir="/tmp"))
        self.git = shutil.which("git")
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith("GIT_") and not key.startswith("A2A_")}
        self.env.update({
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0", "GIT_AUTHOR_NAME": "Git probe fixture",
            "GIT_AUTHOR_EMAIL": "probe@example.invalid",
            "GIT_COMMITTER_NAME": "Git probe fixture",
            "GIT_COMMITTER_EMAIL": "probe@example.invalid",
            "GIT_CONFIG_COUNT": "2", "GIT_CONFIG_KEY_0": "core.hooksPath",
            "GIT_CONFIG_VALUE_0": os.devnull,
            "GIT_CONFIG_KEY_1": "commit.gpgsign", "GIT_CONFIG_VALUE_1": "false",
        })
        self.commands = []
        self.assertions = []
        self.cases = []
        self.sequence = 0

    def save(self, name, value):
        with (self.out / name).open("x", encoding="utf-8") as out:
            json.dump(value, out, ensure_ascii=False, indent=2)
            out.write("\n")

    def run(self, cwd, args, *, allowed=(0,), stdin=None):
        argv = [self.git, "-C", str(cwd), *args]
        record = {"argv": argv, "cwd": str(cwd), "stdin": stdin, "started": now()}
        self.commands.append(record)
        p = subprocess.run(argv, env=self.env, input=stdin, capture_output=True, text=True)
        record.update(exit=p.returncode, stdout=p.stdout, stderr=p.stderr, ended=now())
        self.check(p.returncode in allowed, "命令退出状态", list(allowed), record)
        return p

    def check(self, value, claim, expected, observed):
        record = {"claim": claim, "expected": expected, "observed": observed, "pass": bool(value)}
        self.assertions.append(record)
        if not value:
            raise AssertionError(json.dumps(record, ensure_ascii=False))

    def oid(self, cwd, ref=REF):
        return self.run(cwd, ["rev-parse", "--verify", ref]).stdout.strip()

    def fixture(self, name, location="main"):
        root = self.root / name
        repo = root / "repo"
        repo.mkdir(parents=True)
        self.run(repo, ["init", "-b", "main"])
        for name_, content in (("change.txt", "G: original\n"),
                               ("staged.txt", "staged original\n"),
                               ("unstaged.txt", "unstaged original\n")):
            (repo / name_).write_text(content, encoding="utf-8")
        self.run(repo, ["add", "."])
        self.run(repo, ["commit", "-m", "Fixture G"])
        g = self.oid(repo)
        candidate = root / "candidate"
        self.run(repo, ["worktree", "add", "--detach", str(candidate), g])
        (candidate / "change.txt").write_text("M: candidate\n", encoding="utf-8")
        (candidate / "new.txt").write_text("M: new file\n", encoding="utf-8")
        self.run(candidate, ["add", "."])
        self.run(candidate, ["commit", "-m", "Fixture M"])
        m = self.oid(candidate, "HEAD")
        target = repo
        if location != "main":
            self.run(repo, ["switch", "--detach", g])
            if location == "linked":
                target = root / "linked main"
                self.run(repo, ["worktree", "add", str(target), "main"])
            else:
                target = None
        case = {"name": name, "repo": str(repo), "target": str(target) if target else None,
                "candidate": str(candidate), "G": g, "M": m, "state": "running"}
        self.cases.append(case)
        return case

    def snapshot(self, case, name):
        repo = Path(case["repo"])
        target = Path(case["target"]) if case["target"] else repo
        contents = {}
        for p in target.iterdir():
            if p.is_file() and p.name != ".git":
                contents[p.name] = base64.b64encode(p.read_bytes()).decode("ascii")
        result = {
            "ref": self.oid(repo), "head": self.oid(target, "HEAD"),
            "index": self.run(target, ["ls-files", "--stage", "-z"]).stdout,
            "status": self.run(target, ["status", "--porcelain=v1", "-z", "--untracked-files=all"]).stdout,
            "contents_base64": contents,
            "reflog": self.run(repo, ["reflog", "show", "--format=%H %gs", REF]).stdout,
            "head_reflog": self.run(target, ["reflog", "show", "--format=%H %gs", "HEAD"]).stdout,
            "worktrees": self.run(repo, ["worktree", "list", "--porcelain", "-z"]).stdout,
        }
        self.save(case["name"] + "-" + name + ".json", result)
        return result

    def transaction(self, case, symref_only=False):
        return Transaction(self, case, symref_only)

    def lock_snapshot(self, case, label):
        target = Path(case["target"] or case["repo"])
        common = Path(self.run(target, ["rev-parse", "--path-format=absolute", "--git-common-dir"]).stdout.strip())
        gitdir = Path(self.run(target, ["rev-parse", "--absolute-git-dir"]).stdout.strip())
        locks = sorted(str(p) for p in common.rglob("*.lock") if p.is_file())
        result = {"common_dir": str(common), "git_dir": str(gitdir), "locks": locks,
                  "branch_lock": str(common / "refs/heads/main.lock"), "head_lock": str(gitdir / "HEAD.lock")}
        self.save(case["name"] + "-" + label + "-locks.json", result)
        return result

    def advance(self, case, conflict=False):
        cwd = Path(case["target"] or case["repo"])
        self.run(cwd, ["merge-base", "--is-ancestor", case["G"], case["M"]])
        with self.transaction(case) as tx:
            tx.prepare()
            if case["target"]:
                preflight = self.run(cwd, ["read-tree", "-n", "-m", "-u", case["G"], case["M"]],
                                     allowed=(0, 128))
                if conflict:
                    self.check(preflight.returncode != 0, "覆盖型修改必须拒绝", "nonzero", preflight.returncode)
                    tx.abort()
                    return
                self.check(preflight.returncode == 0, "安全快进预检通过", 0, preflight.returncode)
                self.run(cwd, ["read-tree", "-m", "-u", case["G"], case["M"]])
            tx.commit()

    def positive(self, name, location="main", dirty=False):
        case = self.fixture(name, location)
        target = Path(case["target"]) if case["target"] else None
        if dirty:
            (target / "staged.txt").write_text("User staged content\n", encoding="utf-8")
            self.run(target, ["add", "staged.txt"])
            (target / "unstaged.txt").write_text("User unstaged content\n", encoding="utf-8")
            (target / "local.txt").write_text("User untracked content\n", encoding="utf-8")
        before = self.snapshot(case, "before")
        self.advance(case)
        after = self.snapshot(case, "after")
        self.check(after["ref"] == case["M"], "工作分支推进至 M", case["M"], after["ref"])
        if target:
            self.check(after["head"] == case["M"], "检出目录 HEAD 为 M", case["M"], after["head"])
            for name_, expected in (("change.txt", "M: candidate\n"), ("new.txt", "M: new file\n")):
                self.check((target / name_).read_text() == expected, "文件内容匹配独立预期", expected,
                           (target / name_).read_text())
                self.check(self.run(target, ["show", ":" + name_]).stdout == expected,
                           "索引内容匹配独立预期", expected, name_)
            if dirty:
                self.check(before["status"] == after["status"], "无冲突的脏状态保留",
                           before["status"], after["status"])
                for name_ in ("staged.txt", "unstaged.txt", "local.txt"):
                    self.check(before["contents_base64"][name_] == after["contents_base64"][name_],
                               "无冲突的用户文件原文保留", before["contents_base64"][name_],
                               after["contents_base64"][name_])
                self.check(self.run(target, ["show", ":staged.txt"]).stdout == "User staged content\n",
                           "用户暂存内容保留", "User staged content\n", "index readback")
            else:
                self.check(after["status"] == "", "快进后检出目录干净", "", after["status"])
        else:
            self.check(before["head"] == after["head"] and before["index"] == after["index"] and
                       before["contents_base64"] == after["contents_base64"],
                       "未检出的分支不改别的目录", "unchanged", after)
        self.check(len(after["reflog"].splitlines()) == len(before["reflog"].splitlines()) + 1,
                   "集成只产生一次工作分支 reflog", 1,
                   len(after["reflog"].splitlines()) - len(before["reflog"].splitlines()))
        if target:
            self.check(len(after["head_reflog"].splitlines()) == len(before["head_reflog"].splitlines()) + 1,
                       "更新被检出分支隐式追加其 HEAD reflog", 1,
                       len(after["head_reflog"].splitlines()) - len(before["head_reflog"].splitlines()))
        case["state"] = "PASS"

    def conflict(self, mode):
        case = self.fixture("conflict-" + mode, "linked")
        target = Path(case["target"])
        name = "new.txt" if mode == "untracked" else "change.txt"
        (target / name).write_text("User content must survive\n", encoding="utf-8")
        if mode == "staged":
            self.run(target, ["add", name])
        before = self.snapshot(case, "before")
        self.advance(case, conflict=True)
        after = self.snapshot(case, "after")
        self.check(before == after, "拒绝后引用、文件、索引、reflog 全部保留", before, after)
        case["state"] = "PASS"

    def symref_support(self):
        case = self.fixture("symref-standalone", "linked")
        before = self.snapshot(case, "before")
        with self.transaction(case, symref_only=True) as tx:
            tx.prepare()
            locks = self.lock_snapshot(case, "prepared")
            self.check(locks["head_lock"] in locks["locks"], "独立 symref-verify 实际锁定 HEAD",
                       locks["head_lock"], locks["locks"])
            tx.abort()
        after = self.snapshot(case, "after")
        self.check(before == after, "独立 symref-verify 不产生写入", before, after)
        case["state"] = "PASS"

    def support_and_locks(self):
        case = self.fixture("branch-update-locks", "linked")
        target = Path(case["target"])
        before = self.snapshot(case, "before")
        with self.transaction(case) as tx:
            tx.prepare()
            locks = self.lock_snapshot(case, "prepared")
            self.check(locks["branch_lock"] in locks["locks"], "实际锁定工作分支", locks["branch_lock"], locks["locks"])
            self.check(self.oid(target) == case["G"], "prepare 尚未更新工作分支", case["G"], self.oid(target))
            writer = self.run(target, ["update-ref", REF, case["M"], case["G"]], allowed=(128,))
            self.check(writer.returncode != 0, "prepare 后工作分支被 Git 锁保护", "nonzero", writer.returncode)
            # Record observed HEAD locking; the approved protocol relies on
            # readback, not an invented universal guarantee about this lock.
            if locks["head_lock"] in locks["locks"]:
                head = self.run(target, ["symbolic-ref", "HEAD", "refs/heads/other"], allowed=(128,))
                self.check(head.returncode != 0, "本次分支事务的隐含 HEAD 锁拒绝并发写入", "nonzero", head.returncode)
            tx.abort()
        after = self.snapshot(case, "after")
        self.check(before == after, "能力探针 abort 没有 Git 副作用", before, after)
        case["state"] = "PASS"

    def changed_old_value(self):
        case = self.fixture("cas-external-X")
        repo = Path(case["repo"])
        (repo / "external.txt").write_text("External X\n", encoding="utf-8")
        self.run(repo, ["add", "external.txt"])
        self.run(repo, ["commit", "-m", "External X"])
        before = self.snapshot(case, "before")
        self.check(before["ref"] not in (case["G"], case["M"]), "外部写入已产生第三值", "X", before["ref"])
        with self.transaction(case) as tx:
            tx.prepare(expected_failure=True)
        after = self.snapshot(case, "after")
        self.check(before == after, "CAS 失败保留 X 及目录状态", before, after)
        case["state"] = "PASS"

    def main(self):
        version = subprocess.check_output([self.git, "--version"], text=True).strip()
        self.check(version == "git version 2.52.0", "按决定使用已核对 Git 版本", "git version 2.52.0", version)
        self.symref_support()
        self.support_and_locks()
        self.positive("clean-main")
        self.positive("clean-linked", "linked")
        self.positive("no-checkout", "none")
        self.positive("dirty-nonconflicting", "linked", True)
        for mode in ("staged", "unstaged", "untracked"):
            self.conflict(mode)
        self.changed_old_value()

    def finish(self, error=None):
        self.save("commands.json", self.commands)
        self.save("assertions.json", self.assertions)
        self.save("result.json", {
            "status": "INCOMPLETE" if error else "PASS", "scope": "Git 正常/拒绝协议；中断窗口尚未运行",
            "command": [sys.executable, "-B", str(Path(__file__).resolve()), self.out.name],
            "git": self.git, "root": str(self.root), "cases": self.cases,
            "error": error, "pending": ["before-worktree-update", "after-worktree-before-CAS", "after-CAS-before-bookkeeping"],
        })
        with tarfile.open(self.out / "artifacts.tar.gz", "w:gz") as out:
            out.add(self.root, arcname=self.root.name)
        print(json.dumps({"status": "INCOMPLETE" if error else "PASS", "evidence": str(self.out),
                          "retained_fixture": str(self.root), "error": error}, ensure_ascii=False))


class Transaction:
    def __init__(self, probe, case, symref_only=False):
        self.probe = probe
        self.case = case
        self.proc = None
        self.record = None
        self.ended = False
        self.symref_only = symref_only
        self.operation_lock = None

    def __enter__(self):
        # Model the existing OS-released operation lock while probing Git.
        # This is a fixture lock, not a substitute for gate recovery acceptance.
        lockfile = Path(self.case["repo"]).parent / "operation-lock.sqlite3"
        self.operation_lock = sqlite3.connect(lockfile, isolation_level=None, timeout=0)
        self.operation_lock.execute("BEGIN IMMEDIATE")
        cwd = self.case["target"] or self.case["repo"]
        argv = [self.probe.git, "-C", cwd, "update-ref", "--stdin"]
        self.record = {"argv": argv, "cwd": cwd, "stdin": [], "stdout": [], "started": now()}
        self.probe.commands.append(self.record)
        self.proc = subprocess.Popen(argv, env=self.probe.env, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self.record["pid"] = self.proc.pid
        self.send("start\n")
        self.response("start: ok\n")
        return self

    def check_head(self, phase):
        if not self.case["target"]:
            return
        value = self.probe.run(Path(self.case["target"]), ["symbolic-ref", "HEAD"]).stdout.strip()
        self.probe.check(value == REF, "操作锁内 symbolic HEAD 核对：" + phase, REF, value)
        self.record.setdefault("head_readbacks", []).append({"phase": phase, "symbolic_head": value})

    def send(self, value):
        self.record["stdin"].append(value)
        self.proc.stdin.write(value)
        self.proc.stdin.flush()

    def response(self, expected):
        with selectors.DefaultSelector() as selector:
            selector.register(self.proc.stdout, selectors.EVENT_READ)
            if not selector.select(5):
                raise RuntimeError("Git transaction response is unknown after 5 seconds")
        line = self.proc.stdout.readline()
        self.record["stdout"].append(line)
        self.probe.check(line == expected, "Git 事务协议应答", expected, line)

    def prepare(self, expected_failure=False):
        self.check_head("before-prepare")
        if self.symref_only:
            self.send("option no-deref\nsymref-verify HEAD " + REF + "\n")
        else:
            self.send("update " + REF + " " + self.case["M"] + " " + self.case["G"] + "\n")
        self.send("prepare\n")
        if expected_failure:
            self.close_input()
            self.probe.check(self.proc.returncode != 0, "CAS 旧值不符必须失败", "nonzero", self.record)
        else:
            self.response("prepare: ok\n")

    def abort(self):
        self.send("abort\n")
        self.response("abort: ok\n")
        self.close_input()
        self.probe.check(self.proc.returncode == 0, "正常 abort 完成", 0, self.record)

    def commit(self):
        self.check_head("before-commit")
        self.send("commit\n")
        self.response("commit: ok\n")
        self.close_input()
        self.probe.check(self.proc.returncode == 0, "正常 commit 完成", 0, self.record)

    def close_input(self):
        if self.ended:
            return
        stdout, stderr = self.proc.communicate()
        self.record["stdout"].append(stdout)
        self.record.update(stderr=stderr, exit=self.proc.returncode, ended=now())
        self.ended = True

    def __exit__(self, exc_type, exc, tb):
        # EOF makes an uncommitted Git transaction abort; no process signals.
        try:
            self.close_input()
        finally:
            if self.operation_lock is not None:
                self.operation_lock.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("label")
    args = parser.parse_args()
    if Path(args.label).name != args.label or not args.label.startswith("probe-git-"):
        parser.error("label must be a fresh probe-git-* directory name")
    probe = Probe(args.label)
    error = None
    try:
        probe.main()
    except Exception:
        error = traceback.format_exc()
    finally:
        probe.finish(error)
    return 1 if error else 0


if __name__ == "__main__":
    raise SystemExit(main())
