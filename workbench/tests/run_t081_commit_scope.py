#!/usr/bin/env python3
"""Measure what an allowed or sandboxed git commit can change in a shared repo.

No model, daemon, or user ~/.codex access. Allow runs directly with cwd at the
worker worktree. Every other decision runs through codex sandbox.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tarfile
import tempfile
import time

ROOT = Path("/Volumes/WD-Elements/a2a-evidence/2026-10-14-batch14/T-081/commit-scope-01")
EVIDENCE = Path("/Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081")
HOME = Path("/tmp/t081-commit-scope-codex-home-01")
RULES = (
    'prefix_rule(pattern=["git", "add"], decision="allow")\n'
    'prefix_rule(pattern=["git", "commit"], decision="allow")\n'
)
OVERRIDES = [
    'model_reasoning_effort="xhigh"',
    'service_tier="default"',
    'check_for_update_on_startup=false',
    'tui.notifications=false',
    'sandbox_workspace_write.network_access=false',
    'features.network_proxy=false',
]
COMPARE_DIRS = ("refs/heads", "worktrees/other-wt", "worktrees/worker")


def run(argv, *, cwd, env, timeout=90):
    started = time.time()
    proc = subprocess.Popen(
        argv, cwd=str(cwd), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        code = proc.returncode
        outcome = None
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            stdout, stderr = proc.communicate(timeout=5)
        code = None
        outcome = "timeout"
    return {
        "argv": argv, "cwd": str(cwd), "exit": code, "stdout": stdout or "",
        "stderr": stderr or "", "outcome": outcome, "seconds": round(time.time() - started, 3),
    }


def require(row, label):
    if row["exit"] != 0:
        raise RuntimeError(label + ": " + json.dumps(row, ensure_ascii=False)[:2000])
    return row["stdout"].strip()


def git(env, *args, cwd):
    return run(["git", *args], cwd=cwd, env=env)


def snapshot(root: Path):
    git_dir = root / "repo/.git"
    files = {}

    def add(path: Path, key: str):
        if not path.exists() and not path.is_symlink():
            files[key] = None
            return
        if path.is_symlink():
            files[key] = {"kind": "symlink", "target": os.readlink(path)}
            return
        if path.is_dir():
            files[key] = {"kind": "dir"}
            return
        data = path.read_bytes()
        item = {"kind": "file", "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        if len(data) <= 12000:
            item["text"] = data.decode("utf-8", "replace")
        files[key] = item

    heads = git_dir / "refs/heads"
    if heads.is_dir():
        for path in sorted(heads.rglob("*")):
            add(path, "refs/heads/" + str(path.relative_to(heads)))
    else:
        files["refs/heads"] = None
    add(git_dir / "packed-refs", "packed-refs")
    add(git_dir / "config", "config")
    for folder, prefix in ((root / "hooks", "hooks"), (root / "hooks-alt", "hooks-alt")):
        if folder.is_dir():
            for path in sorted(folder.rglob("*")):
                add(path, prefix + "/" + str(path.relative_to(folder)))
    add(root / "include.config", "include.config")
    add(root / "custom-index", "custom-index")
    for name in ("other-wt", "worker"):
        meta = git_dir / "worktrees" / name
        if meta.is_dir():
            for path in sorted(meta.rglob("*")):
                if path.is_file() or path.is_symlink():
                    add(path, "worktrees/" + name + "/" + str(path.relative_to(meta)))
    add(root / "hook-log.txt", "hook-log.txt")
    return files


def diff_snapshots(before, after):
    changes = []
    for key in sorted(set(before) | set(after)):
        old, new = before.get(key), after.get(key)
        if old == new:
            continue
        if key.startswith("worktrees/") and "/logs/" in key:
            kind = "changed"
        else:
            kind = "added" if old is None else "removed" if new is None else "changed"
        changes.append({
            "path": key, "change": kind,
            "before": None if old is None else {k: old[k] for k in old if k != "text"},
            "after": None if new is None else {k: new[k] for k in new if k != "text"},
            "before_text": None if not old else old.get("text"),
            "after_text": None if not new else new.get("text"),
        })
    return changes


def incomplete(row):
    text = (row.get("stdout", "") + "\n" + row.get("stderr", "")).lower()
    if row.get("exit") is None or row.get("outcome") in ("timeout", "spawn_error"):
        return True
    if "sandbox_apply" in text or "usage: codex sandbox" in text or "required arguments were not provided" in text:
        return True
    if row.get("exit") == 129 or "\nusage: git " in ("\n" + text):
        return True
    return False


def policy_check(codex, rules, env, argv):
    row = run([codex, "execpolicy", "check", "--pretty", "--rules", str(rules), "--", *argv],
              cwd=ROOT, env=env, timeout=30)
    parsed = None
    if row["exit"] == 0:
        try:
            parsed = json.loads(row["stdout"])
        except json.JSONDecodeError:
            parsed = None
    decision = None if not isinstance(parsed, dict) else parsed.get("decision")
    return {"command": row, "parsed": parsed, "decision": decision,
            "allow": decision == "allow", "incomplete": incomplete(row) or parsed is None}


def sandbox_command(codex, worker, cmd):
    argv = [codex, "sandbox", "--permission-profile", ":workspace", "--cd", str(worker)]
    for item in OVERRIDES:
        argv.extend(["-c", item])
    argv.append("--")
    argv.extend(cmd)
    return argv


def stage(env, worktree: Path, name: str):
    target = worktree / ("probe-" + name + ".txt")
    target.write_text(name + "\n", encoding="utf-8")
    require(git(env, "add", "--", target.name, cwd=worktree), "stage " + name)


def restore(archive: Path):
    for name in ("repo", "worker", "other-wt", "hooks", "hooks-alt"):
        path = ROOT / name
        if path.is_symlink() or path.exists():
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
    for name in ("include.config", "template.txt", "message.txt", "hook-log.txt", "custom-index"):
        path = ROOT / name
        if path.exists() or path.is_symlink():
            path.unlink()
    with tarfile.open(archive, "r") as stream:
        stream.extractall(ROOT)
    for name in ("hooks", "hooks-alt"):
        os.chmod(ROOT / name / "post-commit", 0o755)
    log = ROOT / "hook-log.txt"
    log.write_text("", encoding="utf-8")


def build_fixture(env, codex):
    if ROOT.exists():
        raise SystemExit("fixture exists, not overwriting: " + str(ROOT))
    if HOME.exists():
        raise SystemExit("CODEX_HOME exists, not reusing: " + str(HOME))
    if not Path("/Volumes/WD-Elements").is_mount():
        raise SystemExit("external volume is not mounted")
    HOME.mkdir(mode=0o700)
    (HOME / "config.toml").write_text("[permissions]\n", encoding="utf-8")
    (HOME / "rules").mkdir(mode=0o700)
    rules = HOME / "rules/default.rules"
    rules.write_text(RULES, encoding="utf-8")
    ROOT.mkdir(parents=True)
    repo, worker, other = ROOT / "repo", ROOT / "worker", ROOT / "other-wt"
    require(git(env, "init", "-b", "main", str(repo), cwd=ROOT), "init")
    require(git(env, "config", "user.name", "T-081 commit scope", cwd=repo), "name")
    require(git(env, "config", "user.email", "t081-commit-scope@example.invalid", cwd=repo), "email")
    hooks, alt = ROOT / "hooks", ROOT / "hooks-alt"
    hooks.mkdir()
    alt.mkdir()
    log = ROOT / "hook-log.txt"
    (hooks / "post-commit").write_text(
        "#!/bin/sh\n"
        f"printf 'primary %s\\n' \"${{T081_VARIANT:-unset}}\" >> {log}\n"
        f"git update-ref refs/heads/hook-side HEAD >> {log} 2>&1 || printf 'primary-ref-failed\\n' >> {log}\n"
        "exit 0\n", encoding="utf-8")
    (alt / "post-commit").write_text(
        "#!/bin/sh\n"
        f"printf 'alt %s\\n' \"${{T081_VARIANT:-unset}}\" >> {log}\n"
        f"git update-ref refs/heads/hook-side-alt HEAD >> {log} 2>&1 || printf 'alt-ref-failed\\n' >> {log}\n"
        "exit 0\n", encoding="utf-8")
    os.chmod(hooks / "post-commit", 0o755)
    os.chmod(alt / "post-commit", 0o755)
    include = ROOT / "include.config"
    include.write_text("[t081]\n\tincluded = yes\n", encoding="utf-8")
    (ROOT / "template.txt").write_text("template body\n", encoding="utf-8")
    (ROOT / "message.txt").write_text("message from file\n", encoding="utf-8")
    require(git(env, "config", "core.hooksPath", str(hooks), cwd=repo), "hooksPath")
    require(git(env, "config", "include.path", str(include), cwd=repo), "include")
    require(git(env, "config", "t081.marker", "baseline", cwd=repo), "marker")
    (repo / "README.txt").write_text("seed\n", encoding="utf-8")
    require(git(env, "add", "README.txt", cwd=repo), "add seed")
    require(git(env, "commit", "-m", "seed", cwd=repo), "seed commit")
    require(git(env, "branch", "other", cwd=repo), "branch other")
    require(git(env, "branch", "packed-keep", cwd=repo), "branch packed")
    require(git(env, "checkout", "--detach", cwd=repo), "detach primary")
    require(git(env, "worktree", "add", str(worker), "main", cwd=repo), "add worker")
    require(git(env, "worktree", "add", str(other), "other", cwd=repo), "add other")
    require(git(env, "pack-refs", "--all", cwd=repo), "pack-refs")
    archive = ROOT / "baseline.tar"
    with tarfile.open(archive, "w") as stream:
        for name in ("repo", "worker", "other-wt", "hooks", "hooks-alt", "include.config", "template.txt", "message.txt"):
            stream.add(ROOT / name, arcname=name)
    return rules, archive


def variant_commands(env):
    worker, other, repo = ROOT / "worker", ROOT / "other-wt", ROOT / "repo"
    common = repo / ".git"
    alt = ROOT / "hooks-alt"
    template, message = ROOT / "template.txt", ROOT / "message.txt"
    index = ROOT / "custom-index"

    def shell(script):
        return ["/bin/zsh", "-lc", script]

    return [
        {"id": "plain_on_work_branch", "stage": worker,
         "argv": ["git", "commit", "-m", "plain on work branch"],
         "question": "worker worktree 检出 main 时，普通 commit 是否推进共享 refs/heads/main，以及基线钩子是否运行"},
        {"id": "template", "stage": worker,
         "argv": ["git", "commit", "--template", str(template), "-m", "template flag"],
         "question": "commit --template 是否改到共享引用或配置"},
        {"id": "message_file", "stage": worker,
         "argv": ["git", "commit", "-F", str(message)],
         "question": "commit -F 是否改到共享引用或配置"},
        {"id": "fixup", "stage": worker,
         "argv": ["git", "commit", "--fixup=HEAD"],
         "question": "commit --fixup 是否改到共享引用或配置"},
        {"id": "amend", "stage": None,
         "argv": ["git", "commit", "--amend", "-m", "amend flag"],
         "question": "commit --amend 是否改写共享工作分支"},
        {"id": "no_verify", "stage": worker,
         "argv": ["git", "commit", "--no-verify", "-m", "no verify"],
         "question": "commit --no-verify 是否跳过钩子，同时是否仍推进工作分支"},
        {"id": "trailer", "stage": worker,
         "argv": ["git", "commit", "-m", "trailer flag", "--trailer", "Example: probe"],
         "question": "commit --trailer 是否改到共享引用或配置"},
        {"id": "cleanup", "stage": worker,
         "argv": ["git", "commit", "-m", "cleanup flag\n\n", "--cleanup=strip"],
         "question": "commit --cleanup 是否改到共享引用或配置"},
        {"id": "dash_c_hooks_path", "stage": worker,
         "argv": ["git", "-c", "core.hooksPath=" + str(alt), "commit", "-m", "dash c hooksPath"],
         "question": "commit 前的 -c core.hooksPath 是否改写配置文件，以及是否改跑另一套钩子"},
        {"id": "git_dir", "stage": worker,
         "argv": ["git", "--git-dir", str(common), "commit", "-m", "git dir"],
         "question": "commit 前的 --git-dir 指向共享 git 目录时能否写引用"},
        {"id": "work_tree", "stage": other,
         "argv": ["git", "--work-tree", str(other), "commit", "-m", "work tree"],
         "question": "commit 前的 --work-tree 指向另一个 worktree 时写哪里"},
        {"id": "dash_C_other", "stage": other,
         "argv": ["git", "-C", str(other), "commit", "-m", "dash C other"],
         "question": "commit 前的 -C 指向另一个 worktree 时能否推进那个分支"},
        {"id": "env_git_dir", "stage": worker,
         "argv": shell(f"GIT_DIR={common} git commit -m 'env GIT_DIR'"),
         "question": "GIT_DIR 前缀是否被 execpolicy 当成 git commit，以及沙箱内能否写共享 git 目录"},
        {"id": "env_git_work_tree", "stage": worker,
         "argv": shell(f"GIT_WORK_TREE={other} git commit -m 'env GIT_WORK_TREE'"),
         "question": "GIT_WORK_TREE 前缀的判定和实际写入"},
        {"id": "env_git_index_file", "stage": worker, "copy_index": index,
         "argv": shell(f"GIT_INDEX_FILE={index} git commit -m 'env GIT_INDEX_FILE'"),
         "question": "GIT_INDEX_FILE 前缀的判定和实际写入"},
        {"id": "env_git_config_parameters", "stage": worker,
         "argv": shell("GIT_CONFIG_PARAMETERS=\"'core.hooksPath=" + str(alt) + "'\" git commit -m 'env GIT_CONFIG_PARAMETERS'"),
         "question": "GIT_CONFIG_PARAMETERS 前缀能否把本次 commit 指到另一套钩子或改配置文件"},
        {"id": "env_git_config_count", "stage": worker,
         "argv": shell(
             "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath "
             f"GIT_CONFIG_VALUE_0={alt} git commit -m 'env GIT_CONFIG_COUNT'"),
         "question": "GIT_CONFIG_COUNT/KEY/VALUE 前缀能否改本次钩子路径或配置文件"},
        {"id": "config_then_commit", "stage": worker, "steps": [
            {"argv": ["git", "config", "core.hooksPath", str(alt)],
             "question": "先执行 git config core.hooksPath"},
            {"argv": ["git", "commit", "-m", "after config hooksPath"],
             "question": "改过 hooksPath 之后的 git commit"},
        ]},
    ]


def measured_run(codex, env, worker, decision_allow, argv):
    if decision_allow:
        row = run(argv, cwd=worker, env=env)
        row["via"] = "direct-outside-sandbox"
        return row
    wrapped = sandbox_command(codex, worker, argv)
    row = run(wrapped, cwd=worker, env=env)
    row["via"] = "codex-sandbox"
    row["sandbox_argv"] = wrapped
    return row


def refs(env):
    listed = git(env, "-C", str(ROOT / "repo"), "show-ref", cwd=ROOT)
    main = git(env, "-C", str(ROOT / "repo"), "rev-parse", "refs/heads/main", cwd=ROOT)
    other = git(env, "-C", str(ROOT / "repo"), "rev-parse", "refs/heads/other", cwd=ROOT)
    hooks_path = git(env, "-C", str(ROOT / "repo"), "config", "--local", "--get", "core.hooksPath", cwd=ROOT)
    include = git(env, "-C", str(ROOT / "repo"), "config", "--local", "--get", "include.path", cwd=ROOT)
    return {
        "show_ref_exit": listed["exit"], "show_ref": listed["stdout"],
        "main_exit": main["exit"], "main": main["stdout"].strip(),
        "other_exit": other["exit"], "other": other["stdout"].strip(),
        "hooks_path_exit": hooks_path["exit"], "hooks_path": hooks_path["stdout"].strip(),
        "include_exit": include["exit"], "include": include["stdout"].strip(),
        "hook_log": (ROOT / "hook-log.txt").read_text(encoding="utf-8") if (ROOT / "hook-log.txt").is_file() else None,
    }


def main():
    codex = shutil.which("codex")
    if not codex:
        raise SystemExit("codex not on PATH")
    env = {key: os.environ[key] for key in ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "USER", "LOGNAME") if key in os.environ}
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "T-081 commit scope", "GIT_AUTHOR_EMAIL": "t081-commit-scope@example.invalid",
        "GIT_COMMITTER_NAME": "T-081 commit scope", "GIT_COMMITTER_EMAIL": "t081-commit-scope@example.invalid",
    })
    out = EVIDENCE / "commit-scope-run-01"
    if out.exists():
        raise SystemExit("evidence output exists: " + str(out))
    out.mkdir()
    rules, archive = build_fixture(env, codex)
    env["CODEX_HOME"] = str(HOME)
    env["T081_HOOK_LOG"] = str(ROOT / "hook-log.txt")
    help_row = run([codex, "execpolicy", "check", "--help"], cwd=ROOT, env=env, timeout=30)
    version = run([codex, "--version"], cwd=ROOT, env=env, timeout=30)
    examples = {
        "inner_git_commit": ["git", "commit", "-m", "inner"],
        "leading_assignment_token": ["GIT_DIR=/tmp/example.git", "git", "commit", "-m", "assigned"],
        "zsh_lc_env": ["/bin/zsh", "-lc", "GIT_DIR=/tmp/example.git git commit -m assigned"],
        "bash_lc_env": ["/bin/bash", "-lc", "GIT_DIR=/tmp/example.git git commit -m assigned"],
        "git_config": ["git", "config", "core.hooksPath", "/tmp/example-hooks"],
    }
    example_checks = {name: policy_check(codex, rules, env, argv) for name, argv in examples.items()}
    report = {
        "status": "INCOMPLETE", "task": "T-081", "model_turns_started": 0,
        "codex": codex, "codex_version": version, "execpolicy_check_help": help_row,
        "codex_home": str(HOME), "rules": RULES, "fixture": str(ROOT),
        "harness_env": {key: env[key] for key in env if key.startswith(("GIT_", "T081_"))},
        "policy_examples": example_checks, "variants": [],
        "citation": {
            "execpolicy_check_help": "Command tokens to check against the policy",
            "rules_doc": "https://learn.chatgpt.com/docs/agent-configuration/rules",
            "rules_behavior": "When a script uses an environment assignment (FOO=bar), Codex does not split it. The invocation is treated as [\"bash\", \"-lc\", \"<full script>\"] and rules apply to that single invocation.",
        },
    }
    try:
        for spec in variant_commands(env):
            restore(archive)
            env["T081_VARIANT"] = spec["id"]
            if spec.get("stage") is not None:
                stage(env, spec["stage"], spec["id"])
            if spec.get("copy_index"):
                index_path = Path(require(git(env, "-C", str(ROOT / "worker"), "rev-parse", "--git-path", "index", cwd=ROOT), "index path"))
                if not index_path.is_absolute():
                    index_path = (ROOT / "worker" / index_path).resolve()
                shutil.copyfile(index_path, spec["copy_index"])
            steps = spec.get("steps") or [{"argv": spec["argv"], "question": spec["question"]}]
            recorded_steps = []
            for step in steps:
                before = snapshot(ROOT)
                before_refs = refs(env)
                checked = policy_check(codex, rules, env, step["argv"])
                if checked["incomplete"]:
                    executed = {"via": None, "exit": None, "stdout": "", "stderr": "execpolicy check incomplete", "argv": step["argv"]}
                    status = "INCOMPLETE"
                else:
                    executed = measured_run(codex, env, ROOT / "worker", checked["allow"], step["argv"])
                    status = "INCOMPLETE" if incomplete(executed) else "MEASURED"
                after = snapshot(ROOT)
                recorded_steps.append({
                    "question": step["question"], "argv": step["argv"],
                    "policy": checked, "run": executed, "status": status,
                    "before_refs": before_refs, "after_refs": refs(env),
                    "byte_diff": diff_snapshots(before, after),
                })
            report["variants"].append({"id": spec["id"], "steps": recorded_steps})
        bad = [step for variant in report["variants"] for step in variant["steps"] if step["status"] != "MEASURED"]
        report["status"] = "INCOMPLETE" if bad else "PASS"
    finally:
        (out / "run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        home_files = [str(path.relative_to(HOME)) for path in HOME.rglob("*")] if HOME.exists() else []
        report["codex_home_files_before_delete"] = home_files
        allowed = {"config.toml", "rules", "rules/default.rules"}
        unexpected = [item for item in home_files if item not in allowed and not item.startswith("tmp/")]
        if report["status"] == "PASS" and not unexpected:
            shutil.rmtree(HOME)
            report["codex_home_deleted"] = not HOME.exists()
        else:
            report["codex_home_deleted"] = False
            report["codex_home_unexpected"] = unexpected
        (out / "run.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "variants": [
        {"id": item["id"], "steps": [{"status": step["status"], "decision": step["policy"]["decision"],
                                      "via": step["run"].get("via"), "exit": step["run"].get("exit")}
                                     for step in item["steps"]]}
        for item in report["variants"]
    ]}, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
