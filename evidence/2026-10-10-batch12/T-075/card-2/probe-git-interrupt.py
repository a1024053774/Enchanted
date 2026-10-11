"""仅由执行主控在沙箱外运行的 Git 协议中断探针。

只终止本探针启动、经 ps 核对的 owner CLI；不向 Git 子进程发送信号。
这里验证真实 Git 协议窗口，不替代后续真实门禁的恢复验收。
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tarfile
import time
import traceback
import uuid


BASE = Path(__file__).resolve().parent
SCRIPT = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("git_probe_rev3", BASE / "probe-git-rev3.py")
normal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(normal)
PHASES = ("before-worktree", "after-worktree-before-CAS", "after-CAS-before-bookkeeping")


def write_new(path, value):
    with path.open("x", encoding="utf-8") as out:
        json.dump(value, out, ensure_ascii=False, indent=2)
        out.write("\n")


def read_manifest(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    root = Path(value["fixture_root"]).resolve()
    if not str(root).startswith("/private/tmp/a2a-t075-2-git-"):
        raise ValueError("夹具根目录不是本卡的 /tmp 目录")
    for key in ("repo", "target", "candidate"):
        resolved = Path(value["case"][key]).resolve()
        if root not in resolved.parents:
            raise ValueError("夹具路径不属于本轮根目录")
    return value


def persist_owner(probe, path, value):
    # Save the protocol I/O before announcing the kill boundary. SIGKILL must
    # not destroy the only copy of the pre-interruption command evidence.
    probe.save("commands-at-barrier.json", probe.commands)
    probe.save("assertions-at-barrier.json", probe.assertions)
    write_new(path, value)


def owner(args):
    manifest = read_manifest(args.manifest)
    case = manifest["case"]
    phase = manifest["phase"]
    probe = normal.Probe(manifest["owner_label"], Path(manifest["fixture_root"]))
    probe.cases.append(case)
    cwd = Path(case["target"])
    probe.run(cwd, ["merge-base", "--is-ancestor", case["G"], case["M"]])
    with probe.transaction(case) as tx:
        tx.prepare()
        if phase != "before-worktree":
            probe.run(cwd, ["read-tree", "-n", "-m", "-u", case["G"], case["M"]])
            probe.run(cwd, ["read-tree", "-m", "-u", case["G"], case["M"]])
        if phase == "after-CAS-before-bookkeeping":
            tx.commit()
        probe.snapshot(case, "at-barrier")
        persist_owner(probe, Path(manifest["ready"]), {
            "pid": os.getpid(), "ppid": os.getppid(), "argv": sys.argv,
            "git_pid": tx.proc.pid, "phase": phase, "intent_id": manifest["intent_id"],
            "G": case["G"], "M": case["M"], "ref": probe.oid(cwd),
            "operation_lock": str(Path(case["repo"]).parent / "operation-lock.sqlite3"),
        })
        # The parent kills only this owner after checking pid, ppid and argv.
        # A release file lets fixture-error cleanup exit without a signal.
        deadline = time.monotonic() + 40
        while not Path(manifest["release"]).exists():
            if time.monotonic() >= deadline:
                raise RuntimeError("主控未在探针期限内到达中断点")
            time.sleep(0.03)
    return 0


def recover(args):
    manifest = read_manifest(args.manifest)
    case = manifest["case"]
    probe = normal.Probe(args.label, Path(manifest["fixture_root"]))
    probe.cases.append(case)
    before = probe.snapshot(case, "before-recovery")
    if before["ref"] == case["G"]:
        probe.advance(case)
    elif before["ref"] == case["M"]:
        # This probe models the existing bookkeeping-only recovery rule.
        # It does not write a synthetic accepted result to the product DB.
        target = Path(case["target"])
        actual = probe.run(target, ["symbolic-ref", "HEAD"]).stdout.strip()
        probe.check(actual == normal.REF, "仅补记账前仍核对检出目录身份", normal.REF, actual)
    else:
        raise RuntimeError("引用不在原意图 G/M 内，需核对")
    after = probe.snapshot(case, "after-recovery")
    probe.check(after["ref"] == case["M"] and after["head"] == case["M"],
                "恢复后分支与检出目录到达 M", case["M"], [after["ref"], after["head"]])
    target = Path(case["target"])
    for name, content in (("change.txt", "M: candidate\n"), ("new.txt", "M: new file\n")):
        actual = (target / name).read_text(encoding="utf-8")
        probe.check(actual == content, "恢复文件符合独立字面预期", content, actual)
        probe.check(probe.run(target, ["show", ":" + name]).stdout == content,
                    "恢复索引符合独立字面预期", content, name)
    probe.check(after["status"] == "", "恢复后检出目录干净", "", after["status"])
    probe.save("commands.json", probe.commands)
    probe.save("assertions.json", probe.assertions)
    probe.save("result.json", {"status": "PASS", "scope": "Git 协议恢复探针，不是门禁验收",
                               "intent_id": manifest["intent_id"], "G": case["G"], "M": case["M"],
                               "before": before, "after": after})
    return 0


def wait_ready(proc, path):
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
        if proc.poll() is not None:
            raise RuntimeError("owner CLI 在受控中断边界之前退出")
        time.sleep(0.02)
    raise RuntimeError("owner CLI 未到达受控中断边界")


def external_command(probe, argv, cwd, expected=0):
    record = {"argv": argv, "cwd": str(cwd), "started": normal.now()}
    probe.commands.append(record)
    p = subprocess.run(argv, cwd=str(cwd), env=probe.env, text=True, capture_output=True)
    record.update(exit=p.returncode, stdout=p.stdout, stderr=p.stderr, ended=normal.now())
    probe.check(p.returncode == expected, "外部探针命令退出", expected, record)
    return p


def window(probe, phase):
    case = probe.fixture(phase, "linked")
    manifest_path = Path(case["repo"]).parent / "original-intent.json"
    ready_path = manifest_path.parent / "owner-ready.json"
    release = manifest_path.parent / "release-owner"
    manifest = {"schema": 1, "intent_id": str(uuid.uuid4()), "case": dict(case),
                "fixture_root": str(probe.root), "phase": phase,
                "ready": str(ready_path), "release": str(release),
                "owner_label": probe.out.name + "/owner-" + phase}
    write_new(manifest_path, manifest)
    original_bytes = manifest_path.read_bytes()
    before = probe.snapshot(case, "before-owner")
    argv = [sys.executable, "-B", str(SCRIPT), "--owned", "--manifest", str(manifest_path)]
    record = {"argv": argv, "cwd": str(probe.root), "started": normal.now()}
    probe.commands.append(record)
    stdout_path = probe.out / (phase + ".owner.stdout")
    stderr_path = probe.out / (phase + ".owner.stderr")
    with stdout_path.open("x", encoding="utf-8") as stdout, stderr_path.open("x", encoding="utf-8") as stderr:
        proc = subprocess.Popen(argv, cwd=str(probe.root), env=probe.env, stdout=stdout, stderr=stderr,
                                start_new_session=True)
    record.update(pid=proc.pid, stdout_path=str(stdout_path), stderr_path=str(stderr_path))
    try:
        ready = wait_ready(proc, ready_path)
        probe.check(ready["pid"] == proc.pid and ready["ppid"] == os.getpid() and ready["phase"] == phase,
                    "中断目标属于本探针", [proc.pid, os.getpid(), phase], ready)
        at = probe.snapshot(case, "at-interruption")
        expected_ref = case["M"] if phase == "after-CAS-before-bookkeeping" else case["G"]
        probe.check(at["ref"] == expected_ref, "注入点真实引用已读回", expected_ref, at["ref"])
        expected_file = "G: original\n" if phase == "before-worktree" else "M: candidate\n"
        actual_file = (Path(case["target"]) / "change.txt").read_text(encoding="utf-8")
        probe.check(actual_file == expected_file, "注入点真实目录状态已读回", expected_file, actual_file)
        identity = external_command(probe, ["ps", "-p", str(proc.pid), "-o", "pid=,ppid=,command="], probe.root)
        columns = identity.stdout.strip().split(None, 2)
        probe.check(len(columns) == 3 and columns[0] == str(proc.pid) and columns[1] == str(os.getpid())
                    and str(SCRIPT) in columns[2] and str(manifest_path) in columns[2]
                    and "--owned" in columns[2] and proc.poll() is None,
                    "ps 核对唯一自建 owner CLI 后才允许 SIGKILL", argv, identity.stdout)
        lock = sqlite3.connect(ready["operation_lock"], isolation_level=None, timeout=0)
        try:
            try:
                lock.execute("BEGIN IMMEDIATE")
            except sqlite3.OperationalError as error:
                probe.check("locked" in str(error), "活跃 owner 的操作锁拒绝第二执行者", "database locked", str(error))
            else:
                raise AssertionError("中断前未持有预期操作锁")
        finally:
            lock.close()
        write_new(probe.out / (phase + ".signal.json"), {
            "pid": proc.pid, "argv": argv, "signal": "SIGKILL", "at": normal.now(),
            "ps": identity.stdout, "ready": ready,
        })
        proc.send_signal(signal.SIGKILL)
        proc.wait(timeout=8)
        record.update(exit=proc.returncode, ended=normal.now())
        probe.check(proc.returncode == -signal.SIGKILL, "只终止已核对的 owner CLI", -signal.SIGKILL, proc.returncode)
        # Owner pipe EOF must let Git abort naturally. Never remove lockfiles.
        target = Path(case["target"])
        common = Path(probe.run(target, ["rev-parse", "--path-format=absolute", "--git-common-dir"]).stdout.strip())
        gitdir = Path(probe.run(target, ["rev-parse", "--absolute-git-dir"]).stdout.strip())
        locks = (common / "refs/heads/main.lock", gitdir / "HEAD.lock", gitdir / "index.lock")
        deadline = time.monotonic() + 5
        while any(path.exists() for path in locks) and time.monotonic() < deadline:
            time.sleep(0.02)
        probe.check(not any(path.exists() for path in locks), "Git 收到 EOF 后自然释放本次锁",
                    "no locks", [str(path) for path in locks if path.exists()])
        interrupted = probe.snapshot(case, "after-kill")
        probe.check(interrupted["ref"] == expected_ref, "中断本身不推进工作分支", expected_ref, interrupted["ref"])
        for round_number in (1, 2):
            label = probe.out.name + "/recovery-" + phase + "-" + str(round_number)
            command = [sys.executable, "-B", str(SCRIPT), "--recover", "--manifest", str(manifest_path), "--label", label]
            external_command(probe, command, probe.root)
            result = json.loads((BASE / label / "result.json").read_text(encoding="utf-8"))
            delta = len(result["after"]["reflog"].splitlines()) - len(result["before"]["reflog"].splitlines())
            expected_delta = 1 if round_number == 1 and phase != "after-CAS-before-bookkeeping" else 0
            probe.check(delta == expected_delta, "恢复只执行尚未发生的引用副作用", expected_delta, delta)
            head_delta = len(result["after"]["head_reflog"].splitlines()) - len(result["before"]["head_reflog"].splitlines())
            probe.check(head_delta == expected_delta, "HEAD reflog 只补尚未发生的一次写入", expected_delta, head_delta)
            recovery_commands = json.loads((BASE / label / "commands.json").read_text(encoding="utf-8"))
            writes = [r for r in recovery_commands if "update-ref" in r["argv"]]
            probe.check(len(writes) == expected_delta, "CAS 后记账与重放都不再次写 Git", expected_delta, writes)
            probe.check(manifest_path.read_bytes() == original_bytes and result["intent_id"] == manifest["intent_id"],
                        "恢复不改变或更换原意图", manifest["intent_id"], result["intent_id"])
        final = probe.snapshot(case, "final")
        probe.check(len(final["reflog"].splitlines()) == len(before["reflog"].splitlines()) + 1,
                    "包括原调用和重放总共只有一次引用推进", 1,
                    len(final["reflog"].splitlines()) - len(before["reflog"].splitlines()))
        case["state"] = "PASS"
    finally:
        if proc.poll() is None:
            release.write_text("fixture cleanup: release without a signal\n", encoding="utf-8")
            proc.wait(timeout=45)
        record.update(exit=proc.returncode, ended=normal.now(),
                      stdout=stdout_path.read_text(encoding="utf-8"), stderr=stderr_path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--controller-run", action="store_true")
    modes.add_argument("--owned", action="store_true")
    modes.add_argument("--recover", action="store_true")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--label")
    args = parser.parse_args()
    if args.owned:
        return owner(args)
    if args.recover:
        return recover(args)
    if not args.label or Path(args.label).name != args.label or not args.label.startswith("probe-git-"):
        parser.error("主控运行需要一个全新的 probe-git-* 标签")
    probe = normal.Probe(args.label)
    error = None
    try:
        version = external_command(probe, [probe.git, "--version"], probe.root).stdout.strip()
        probe.check(version == "git version 2.52.0", "沙箱外仍使用已核对的 Git", "git version 2.52.0", version)
        for phase in PHASES:
            window(probe, phase)
    except Exception:
        error = traceback.format_exc()
    finally:
        probe.save("commands.json", probe.commands)
        probe.save("assertions.json", probe.assertions)
        receipt = {
            "status": "INCOMPLETE" if error else "PASS", "command": sys.argv,
            "scope": "真实 Git 与 owner CLI 中断探针，不是产品门禁验收", "error": error,
            "cases": probe.cases, "protocol": "controller-decision-02 option (a), decision-03",
            "fixture_root": str(probe.root), "git": probe.git,
        }
        probe.save("interruption-summary.json", receipt)
        with tarfile.open(probe.out / "artifacts.tar.gz", "w:gz") as out:
            out.add(probe.root, arcname=probe.root.name)
        print(json.dumps({"status": receipt["status"], "evidence": str(probe.out),
                          "retained_fixture": str(probe.root), "error": error}, ensure_ascii=False))
    return 1 if error else 0


if __name__ == "__main__":
    raise SystemExit(main())
