#!/bin/bash
# T-093 验收证据修正复验 02：派生自只读审查 OUTSIDE-02，旧脚本原样保留。
# 保留首个业务失败；清理另列并继续等待。支持 --check-only 的无 PTY 驱动检查。
# 不启动供应商 CLI，不读真实凭据，不访问真实上游，不修改仓库或全局配置。
# 真实 HOME 只调用 inventory 读取四个既定范围的文件名和元数据。
set -u
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1
/usr/bin/python3 -B - "${1:-/Users/luckye/Documents/Code/a2a-wt-t093}" "${2:-}" "${3:-}" <<'PY'
import io
import json
import os
import re
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time

REPO = Path(sys.argv[1]).resolve()
CANDIDATE = sys.argv[2]
CHECK_ONLY = sys.argv[3] == "--check-only"
if not re.fullmatch(r"[0-9a-f]{40}", CANDIDATE) or sys.argv[3] not in ("", "--check-only"):
    raise SystemExit("usage: script REPO FULL_FROZEN_SHA [--check-only]")
NODE = "/opt/homebrew/bin/node"
OUT = Path(tempfile.mkdtemp(prefix="t093-evidence-02-", dir="/private/tmp"))
print("输出目录：" + str(OUT), flush=True)
results = []


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], check=True,
                          capture_output=True, timeout=45)


def save(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def section(name, directory):
    print("\n段名：" + name + "；输出目录：" + str(directory), flush=True)


def run(name, args, cwd, env, seconds=180):
    section(name, OUT)
    start = time.monotonic()
    stdout = OUT / (name + ".stdout")
    stderr = OUT / (name + ".stderr")
    timed_out = False
    with stdout.open("x", encoding="utf-8") as out, stderr.open("x", encoding="utf-8") as err:
        child = subprocess.Popen(args, cwd=cwd, env=env, stdout=out, stderr=err,
                                 start_new_session=True)
        try:
            code = child.wait(timeout=seconds)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            timed_out = True
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=5)
            code = 124
    row = {"name": name, "command": args, "cwd": str(cwd), "exit_code": code,
           "hard_timeout_seconds": seconds, "timed_out": timed_out,
           "elapsed_seconds": round(time.monotonic() - start, 2),
           "stdout": str(stdout), "stderr": str(stderr)}
    results.append(row)
    print("退出码：" + str(code) + "；硬超时：" + str(seconds) + " 秒", flush=True)
    return row


def archive(name):
    directory = OUT / name
    directory.mkdir()
    # 只导出完成条件所需的 workbench；不展开历史的大型证据或创建 worktree。
    data = git("archive", CANDIDATE, "workbench").stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as stream:
        stream.extractall(directory)
    (directory / "workbench/node_modules").symlink_to(REPO / "workbench/node_modules", target_is_directory=True)
    return directory


def replace_once(path, before, after):
    text = path.read_text(encoding="utf-8")
    if text.count(before) != 1:
        raise RuntimeError("变异或驱动定位不唯一：" + str(path))
    path.write_text(text.replace(before, after), encoding="utf-8")


def instrument(directory, injected):
    path = directory / "workbench/tests/test_t093_login_chain.ts"
    replace_once(path, 'import assert from "node:assert/strict";',
        'import assert from "node:assert/strict";\nimport fs from "node:fs";\nimport { syncBuiltinESMExports } from "node:module";')
    replace_once(path, 'import { join, resolve } from "node:path";',
        'import { dirname, join, resolve } from "node:path";')
    # 只在审查驱动登记自己创建的私有根，用于超时后的精确收尾；不改变生产路径。
    replace_once(path, 'const root = realpathSync(mkdtempSync("/private/tmp/t093-chain-")), state = join(root, "state");',
        '''const originalMkdtemp = fs.mkdtempSync;
fs.mkdtempSync = ((prefix: any, options: any) => {
  const result = originalMkdtemp(prefix, options);
  if (prefix === "/private/tmp/a2a-claude-login-") fs.appendFileSync(output + ".owned-homes", String(result) + "\\n");
  return result;
}) as typeof fs.mkdtempSync;
syncBuiltinESMExports();
const root = realpathSync(mkdtempSync(join(dirname(output), "f-"))), state = join(root, "state");
writeFileSync(output + ".owned-root", root + "\\n", { flag: "wx" });
assert(Buffer.byteLength(join(state, "control.sock")) <= 103, "reviewer fixture socket path must fit Unix limit");''')
    replace_once(path, 'let upstreamReceived = 0;', 'let upstreamReceived = 0;\nlet boundaryFailure: string | null = null;\nconst cleanupFailures: { phase: string; error: string }[] = [];')
    replace_once(path, 'const upstream = createServer((req, res) => {', 'const upstream = createServer((req, res) => { try {')
    replace_once(path, '});\nasync function wait',
        '''} catch (error) { boundaryFailure = error instanceof Error ? error.message : "independent_boundary_failed"; req.resume(); res.writeHead(502).end("{}"); }
});
async function wait''')
    replace_once(path, 'async function wait(test: () => boolean, name: string, timeout = 20_000) {',
        'async function wait(test: () => boolean, name: string, timeout = 20_000, observeBoundary = true) {')
    replace_once(path, 'while (!test()) { if (Date.now() > until)',
        'while (!test()) { if (observeBoundary && boundaryFailure) throw new Error("independent_upstream_assertion: " + boundaryFailure); if (Date.now() > until)')
    replace_once(path, 'await wait(() => !existsSync(join(state, "daemon.pid")), "cleanup deadline");',
        'await wait(() => !existsSync(join(state, "daemon.pid")), "cleanup deadline", 20_000, false);')
    replace_once(path, 'catch { failure = "daemon_cleanup_unconfirmed"; }',
        'catch { cleanupFailures.push({ phase: "daemon_shutdown", error: "daemon_cleanup_unconfirmed" }); }')
    replace_once(path, 'if (launch?.env?.HOME) assert.equal(existsSync(launch.env.HOME), false, "private HOME cleanup must finish");',
        'if (launch?.env?.HOME) { try { await wait(() => !existsSync(launch.env.HOME), "private HOME cleanup deadline", 5_000, false); } catch { cleanupFailures.push({ phase: "private_home", error: "private_home_cleanup_unconfirmed" }); } }')
    replace_once(path, 'status: failure ? "INCOMPLETE" : "PASS",',
        'status: failure || cleanupFailures.length ? "INCOMPLETE" : "PASS",')
    replace_once(path, 'checks, failure,', 'checks, failure, cleanup_failures: cleanupFailures,')
    replace_once(path, 'rmSync(root, { recursive: true }); result.fixture_removed = !existsSync(root);',
        'try { rmSync(root, { recursive: true }); result.fixture_removed = !existsSync(root); } catch (error) { cleanupFailures.push({ phase: "fixture_remove", error: error instanceof Error ? error.message : "fixture_cleanup_failed" }); result.status = "INCOMPLETE"; }')
    replace_once(path, 'process.exitCode = failure ? 2 : 0;', 'process.exitCode = result.status === "PASS" ? 0 : 2;')
    replace_once(path, 'assert.equal(req.headers.authorization, "Bearer " + token);',
        'assert(req.headers.authorization === "Bearer " + token, "upstream bearer must match the copied login");')
    replace_once(path, 'launch = started.launch;',
        'launch = started.launch; writeFileSync(output + ".owned-pty", String(panes.panes.get(launch.thread).pty.pid) + "\\n", { flag: "wx" });')
    if not injected:
        return
    # 输入来自票据的三项反例，答案不导入 credentialVariants/credentialHits。
    replace_once(path, '"确定性正常登录链路测试。\\n"',
        '"独立审查 HOME 路径哨兵：" + sourceHome + "/private-sentinel\\n"')
    replace_once(path, 'const stopped = await request(state, { command: "daemon_stop" }, operator);',
        '''writeFileSync(join(state, "reviewer-credential-injection.txt"), token, { flag: "wx", mode: 0o600 });
  const stopped = await request(state, { command: "daemon_stop" }, operator);''')
    replace_once(path, 'assert.equal(facts.credential_scan.hits, 0);',
        '''assert(facts.credential_scan.hits > 0, "reviewer raw synthetic credential injection must be detected");
  assert(facts.launch_home_references.some((row: any) => row.field === "launch.role_text" && row.occurrences === 1), "reviewer HOME path in role/argv must be reported");''')
    replace_once(path, 'assert.equal(JSON.parse(checked.stdout).counts.model_requests, upstreamReceived);',
        '''const publicFacts = JSON.parse(checked.stdout);
  assert.equal(publicFacts.counts.model_requests, upstreamReceived);
  assert(publicFacts.credential_scan.hits > 0, "fact entry must publish credential hit");
  assert(publicFacts.launch_home_references.some((row: any) => row.field.startsWith("launch.argv[") && row.occurrences === 1), "fact entry must publish injected argv HOME path");''')
    replace_once(path, 'assert.equal(countForwarderRecords(ledger, upstreamReceived).counts_match, false);',
        '''const damaged = await exec(process.execPath, [resolve("workbench/src/claudeLoginCheck.ts"), audit]);
  assert.equal(JSON.parse(damaged.stdout).counts.counts_match, false, "fact entry must report a dropped request row");''')
    # 凭据注入属于反例，不是零命中绿态；摘要只保留命中数，不保留该原值。
    replace_once(path, '"fact command recounts all attempts; private HOME removed; inventory unchanged; credential scan zero"',
        '"reviewer fact entry: raw credential and argv HOME injections detected; all attempts counted; private HOME removed; synthetic inventory unchanged"')


def cleanup(output):
    section("收尾-" + output.stem, OUT)
    errors = []
    pid_file = Path(str(output) + ".owned-pty")
    if pid_file.exists():
        pid = int(pid_file.read_text())
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except OSError as error:
            errors.append(type(error).__name__)
    removed = []
    for suffix in (".owned-root", ".owned-homes"):
        path = Path(str(output) + suffix)
        if not path.exists():
            continue
        for raw in path.read_text().splitlines():
            owned = Path(raw)
            valid = (suffix == ".owned-root" and owned.parent == OUT and owned.name.startswith("f-")) or (
                suffix == ".owned-homes" and owned.parent == Path("/private/tmp") and owned.name.startswith("a2a-claude-login-"))
            if not valid:
                errors.append("unowned_cleanup_path")
                continue
            if owned.exists():
                shutil.rmtree(owned)
            removed.append({"path": raw, "removed": not owned.exists()})
    value = {"errors": errors, "owned_directories": removed}
    save(OUT / (output.stem + ".cleanup.json"), value)
    print("收尾退出码：" + str(0 if not errors else 2), flush=True)
    return not errors


try:
    section("冻结身份核对", OUT)
    head = git("rev-parse", "HEAD").stdout.decode().strip()
    if head != CANDIDATE:
        raise RuntimeError("冻结候选已变化；停止审查")
    gitdir = git("rev-parse", "--absolute-git-dir").stdout.decode().strip()
    print("退出码：0；候选：" + head, flush=True)
    env = dict(os.environ, GIT_DIR=gitdir, GIT_WORK_TREE=str(REPO), PYTHONDONTWRITEBYTECODE="1")
    for key in ("A2A_OPERATOR_CREDENTIAL", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "CLAUDE_CONFIG_DIR"):
        env.pop(key, None)
    # This exact generated driver throws before setup, so it starts no PTY,
    # auth helper, daemon, upstream socket or ps. Both failures must survive.
    legacy_dir = archive("legacy-failure-priority")
    instrument(legacy_dir, False)
    legacy_path = legacy_dir / "workbench/tests/test_t093_login_chain.ts"
    replace_once(legacy_path, 'candidate = (await exec("git", ["rev-parse", "HEAD"])).stdout.trim();',
                 'assert.fail("primary_business_probe");')
    replace_once(legacy_path, 'try { rmSync(root, { recursive: true }); result.fixture_removed = !existsSync(root); } catch (error) { cleanupFailures.push({ phase: "fixture_remove", error: error instanceof Error ? error.message : "fixture_cleanup_failed" }); result.status = "INCOMPLETE"; }',
                 'throw new Error("secondary_cleanup_probe");')
    legacy_output = OUT / "legacy-failure-priority.json"
    legacy_row = run("legacy-failure-priority", [NODE, str(legacy_path), str(legacy_output)], legacy_dir, env, 15)
    legacy_clean = cleanup(legacy_output)
    legacy_stderr = (OUT / "legacy-failure-priority.stderr").read_text()
    legacy_rejected = (legacy_row["exit_code"] != 0 and not legacy_row["timed_out"] and legacy_clean
                       and not legacy_output.exists() and "secondary_cleanup_probe" in legacy_stderr
                       and "primary_business_probe" not in legacy_stderr)
    priority_dir = archive("failure-priority")
    instrument(priority_dir, False)
    priority_path = priority_dir / "workbench/tests/test_t093_login_chain.ts"
    replace_once(priority_path, 'candidate = (await exec("git", ["rev-parse", "HEAD"])).stdout.trim();',
                 'assert.fail("primary_business_probe");')
    replace_once(priority_path, 'rmSync(root, { recursive: true });',
                 'throw new Error("secondary_cleanup_probe");')
    priority_output = OUT / "failure-priority.json"
    priority_row = run("failure-priority", [NODE, str(priority_path), str(priority_output)], priority_dir, env, 15)
    priority_clean = cleanup(priority_output)
    priority_inner = json.loads(priority_output.read_text()) if priority_output.exists() else {}
    priority_ok = (legacy_rejected and priority_row["exit_code"] == 2 and not priority_row["timed_out"] and priority_clean
                   and priority_inner.get("failure") == "primary_business_probe"
                   and any(row["phase"] == "fixture_remove" and row["error"] == "secondary_cleanup_probe"
                           for row in priority_inner.get("cleanup_failures", [])))
    priority_probe = {"status": "PASS" if priority_ok else "INCOMPLETE", "legacy_cleanup_mask_rejected": legacy_rejected, "primary": priority_inner.get("failure"),
                      "cleanup_failures": priority_inner.get("cleanup_failures"), "real_cli_starts": 0,
                      "scope": "exact generated driver; forced failures before setup; no PTY/auth/ps"}
    if not priority_ok:
        save(OUT / "PRIORITY-FAILURE.json", priority_probe)
        raise RuntimeError("driver did not preserve primary and cleanup failures separately")
    if CHECK_ONLY:
        prepared = []
        for name, injected in (("candidate-green", False), ("independent-counterexamples", True), ("omit-first-request", True)):
            directory = archive(name)
            instrument(directory, injected)
            row = run(name + "-syntax", [NODE, "--check", str(directory / "workbench/tests/test_t093_login_chain.ts")], directory, env, 15)
            prepared.append({"name": name, "exit_code": row["exit_code"], "timed_out": row["timed_out"]})
        ok = all(row["exit_code"] == 0 and not row["timed_out"] for row in prepared)
        save(OUT / "CHECKS.json", {"status": "PASS" if ok else "INCOMPLETE", "candidate": CANDIDATE,
                                  "failure_priority": priority_probe, "syntax": prepared,
                                  "scope": "no PTY/auth/ps/model; not an outside chain verdict"})
        print("驱动本地检查：" + ("PASS" if ok else "INCOMPLETE") + "；摘要：" + str(OUT / "CHECKS.json"), flush=True)
        sys.exit(0 if ok else 2)
    verdicts = []
    controls_ok = True
    for name, injected in (("candidate-green", False), ("independent-counterexamples", True)):
        directory = archive(name)
        instrument(directory, injected)
        output = OUT / (name + ".json")
        row = run(name, [sys.executable, "-B", str(directory / "workbench/tests/run_t093_login_chain.py"), "--output", str(output)], directory, env)
        clean = cleanup(output)
        inner = json.loads(output.read_text()) if output.exists() else None
        host_path = output.with_name(output.stem + ".host-home.json")
        host = json.loads(host_path.read_text()) if host_path.exists() else None
        entry_ok = bool(inner and inner["status"] == "PASS" and inner["failure"] is None and clean and not row["timed_out"])
        verdicts.append({"name": name, "entry": "PASS" if entry_ok else "INCOMPLETE", "host_home": host,
                         "exit_code": row["exit_code"], "note": "HOME 差异一律保留；不归因、不忽略。"})
        if not entry_ok:
            controls_ok = False
            break
    mutations = [
        ("omit-first-request", "claudeForwarder.ts", 'this.record({ kind: "request", sequence, method: req.method, path,',
         'if (sequence !== 1) this.record({ kind: "request", sequence, method: req.method, path,'),
        ("hide-home-reference", "claudeLoginFacts.ts", 'if (typeof value === "string") return value.includes(home)',
         'if (typeof value === "string") return false'),
        ("empty-credential-variants", "claudeLoginFacts.ts", 'export function credentialVariants(secrets: readonly string[]) {',
         'export function credentialVariants(secrets: readonly string[]) { return [];'),
        ("hide-count-mismatch", "claudeLoginFacts.ts", 'counts_match: received === requests.length && sequences,',
         'counts_match: true,'),
    ]
    if controls_ok:
        for name, module, before, after in mutations:
            directory = archive(name)
            instrument(directory, True)
            replace_once(directory / "workbench/src" / module, before, after)
            if name == "empty-credential-variants":
                # 特别核对候选已有检查是否也拒绝该单处错误，保留任何漏检。
                old = run(name + "-candidate-oracle", [NODE, str(directory / "workbench/tests/test_t093_forwarder.ts"),
                          str(OUT / (name + "-candidate-oracle.json"))], directory, env, 25)
                old_error = (OUT / (name + "-candidate-oracle.stderr")).read_text()
                valid_rejection = (old["exit_code"] != 0 and not old["timed_out"]
                                   and "AssertionError" in old_error
                                   and "credential injection must be detected" in old_error)
                oracle_result = "accepted_bad_implementation" if old["exit_code"] == 0 else (
                    "vacuous_fixture_failure" if "ENOENT" in old_error and "synthetic-leak.txt" in old_error else (
                        "rejected_behavior" if valid_rejection else "INCOMPLETE"))
                verdicts.append({"name": name + "-candidate-oracle", "exit_code": old["exit_code"],
                                 "valid_business_rejection": valid_rejection,
                                 "oracle_result": oracle_result,
                                 "meaning": "退出 0 或仅由 ENOENT/超时等驱动原因失败，都不证明完成检查拒绝了错误行为。"})
            output = OUT / (name + ".json")
            row = run(name, [sys.executable, "-B", str(directory / "workbench/tests/run_t093_login_chain.py"), "--output", str(output)], directory, env)
            clean = cleanup(output)
            inner = json.loads(output.read_text()) if output.exists() else None
            failure = (inner or {}).get("failure") or (OUT / (name + ".stderr")).read_text()
            expected = {
                "omit-first-request": "independent_upstream_assertion",
                "hide-home-reference": "reviewer HOME path",
                "empty-credential-variants": "reviewer raw synthetic credential injection",
                "hide-count-mismatch": "fact entry must report a dropped request row",
            }[name]
            caught = row["exit_code"] != 0 and not row["timed_out"] and expected in failure and clean
            verdicts.append({"name": name, "mutation": {"file": module, "before": before, "after": after},
                             "entry": "PASS" if caught else "INCOMPLETE", "rejected": caught,
                             "exit_code": row["exit_code"], "failure": failure,
                             "cleanup_failures": (inner or {}).get("cleanup_failures", []),
                             "output": str(output)})
    gap = any(v["name"].endswith("-candidate-oracle") and v["oracle_result"] in (
        "accepted_bad_implementation", "vacuous_fixture_failure") for v in verdicts)
    oracle_observed = all(v.get("oracle_result") != "INCOMPLETE" for v in verdicts)
    complete = controls_ok and all(v.get("rejected", True) for v in verdicts)
    home_unchanged = all(v.get("host_home") and v["host_home"]["status"] == "PASS" for v in verdicts[:2])
    status = "NO_GO" if gap else "PASS" if complete and home_unchanged and oracle_observed else "INCOMPLETE"
    save(OUT / "SUMMARY.json", {"status": status, "candidate": CANDIDATE, "base": "61786370428c3ec5f894ea60acccf2695d54c2dc",
         "controls_ok": controls_ok, "mutants_rejected": complete, "failure_priority": priority_probe, "host_home_unchanged": home_unchanged,
         "candidate_oracle_gap": gap, "verdicts": verdicts, "commands": results,
         "real_vendor_cli_starts": 0, "real_credential_reads": 0, "real_upstream_requests": 0,
         "note": "所有源副本与日志保留在本次 /tmp 输出目录；合成 auth、隔离 HOME、PTY 与运行夹具已按登记路径收尾。"})
    print("审查检查状态：" + status + "；摘要：" + str(OUT / "SUMMARY.json"), flush=True)
    sys.exit(0 if status == "PASS" else 2)
except Exception as error:
    save(OUT / "DRIVER-FAILURE.json", {"status": "INCOMPLETE", "kind": type(error).__name__, "message": str(error), "commands": results})
    print("驱动 INCOMPLETE；退出码：2；输出目录：" + str(OUT), flush=True)
    sys.exit(2)
PY
