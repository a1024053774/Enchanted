#!/usr/bin/env python3
"""T-249 验收：Git 图面板的无界面入口与 git 本身是否一致。

运行位置是被验收的工作区根目录（`python3 acceptance/T-249/check_git_graph.py`）。
被测入口（任务卡里规定的合同）：

    node workbench/app/panels/gitGraphCli.ts <repo> [--scope all|current]
        → stdout 一个 JSON：{"rows": [{"hash", "parents", "refs", "head", "lane", "segments"}, ...],
                             "uncommitted": {"files": N} 或 null}
          rows 只含提交（不含未提交行），从新到旧；refs 是指向该提交的完整引用名（refs/heads/x、refs/tags/x）；
          segments 是该行的线段 [fromLane, fromY, toLane, toY, colorLane, dashed]。
    node workbench/app/panels/gitGraphCli.ts <repo> --action '<JSON>'
        → 用界面同一份命令代码执行一个写操作；名字非法时非零退出，仓库不变。

期望值全部从 git 读，或按原 mod（herdr-git-graph lanes.js）的泳道规则对本夹具手推，不从实现读。
"""
import json, os, pathlib, subprocess, sys, tempfile

CLI = ["node", "workbench/app/panels/gitGraphCli.ts"]
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def git(repo, *args, env=None):
    return subprocess.run(["git", "-C", repo, *args], check=True, text=True, capture_output=True, env=env).stdout


def commit(repo, name, when, message):
    env = dict(os.environ, GIT_AUTHOR_DATE=f"{when} +0000", GIT_COMMITTER_DATE=f"{when} +0000",
               GIT_AUTHOR_NAME="T", GIT_AUTHOR_EMAIL="t@example.invalid",
               GIT_COMMITTER_NAME="T", GIT_COMMITTER_EMAIL="t@example.invalid")
    pathlib.Path(repo, name).write_text(message + "\n")
    git(repo, "add", name, env=env)
    git(repo, "commit", "-q", "-m", message, env=env)
    return git(repo, "rev-parse", "HEAD").strip()


def build_fixture(repo):
    git(repo, "init", "-q", "-b", "main")
    t = 1700000000
    c1 = commit(repo, "a.txt", t + 1, "c1")
    c2 = commit(repo, "b.txt", t + 2, "c2")
    git(repo, "checkout", "-q", "-b", "feature", c1)
    f1 = commit(repo, "f.txt", t + 3, "f1")
    git(repo, "tag", "v1", f1)  # 轻量标签，直接指向 f1
    git(repo, "checkout", "-q", "main")
    c3 = commit(repo, "c.txt", t + 4, "c3")
    git(repo, "checkout", "-q", "feature")
    f2 = commit(repo, "g.txt", t + 5, "f2")
    git(repo, "checkout", "-q", "main")
    env = dict(os.environ, GIT_AUTHOR_DATE=f"{t + 6} +0000", GIT_COMMITTER_DATE=f"{t + 6} +0000",
               GIT_AUTHOR_NAME="T", GIT_AUTHOR_EMAIL="t@example.invalid",
               GIT_COMMITTER_NAME="T", GIT_COMMITTER_EMAIL="t@example.invalid")
    git(repo, "merge", "-q", "--no-ff", "--no-edit", "feature", env=env)
    m = git(repo, "rev-parse", "HEAD").strip()
    git(repo, "checkout", "-q", "-b", "side", c2)
    s1 = commit(repo, "s.txt", t + 7, "s1")
    git(repo, "checkout", "-q", "main")
    # 两个未提交改动：改一个已跟踪文件，加一个未跟踪文件。
    pathlib.Path(repo, "a.txt").write_text("changed\n")
    pathlib.Path(repo, "new.txt").write_text("new\n")
    return dict(c1=c1, c2=c2, f1=f1, c3=c3, f2=f2, m=m, s1=s1)


def run_cli(*args):
    p = subprocess.run([*CLI, *args], text=True, capture_output=True, timeout=60)
    return p


def read_graph(repo, scope):
    p = run_cli(repo, "--scope", scope)
    if p.returncode != 0:
        check(False, f"入口 --scope {scope} 退出码为 0（实际 {p.returncode}：{p.stderr.strip()[:300]}）")
        return None
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError as e:
        check(False, f"入口 --scope {scope} 输出是 JSON（{e}）")
        return None


def refs_by_commit(repo):
    out = {}
    for line in git(repo, "for-each-ref", "--format=%(objectname) %(refname)", "refs/heads", "refs/tags").splitlines():
        oid, name = line.split(" ", 1)
        out.setdefault(oid, set()).add(name)
    return out


def verify_scope(repo, scope, revs, expected_lanes, names):
    graph = read_graph(repo, scope)
    if graph is None:
        return None
    rows = graph.get("rows")
    if not isinstance(rows, list):
        check(False, f"[{scope}] rows 是列表")
        return None
    expected = git(repo, "rev-list", "--date-order", "--parents", *revs).split("\n")
    expected = [line.split() for line in expected if line]
    check([r.get("hash") for r in rows] == [e[0] for e in expected],
          f"[{scope}] 提交顺序与 git rev-list --date-order {' '.join(revs)} 一致")
    check([r.get("parents") for r in rows] == [e[1:] for e in expected], f"[{scope}] 每行父提交与 git rev-list --parents 一致")
    refs = refs_by_commit(repo)
    check(all(set(r.get("refs") or []) == refs.get(r.get("hash"), set()) for r in rows),
          f"[{scope}] 每行的引用与 git for-each-ref refs/heads refs/tags 一致")
    head = git(repo, "rev-parse", "HEAD").strip()
    check([r.get("hash") for r in rows if r.get("head") is True] == [head], f"[{scope}] 恰好 HEAD 那一行标为 head")
    lanes = {names.get(r.get("hash"), r.get("hash")): r.get("lane") for r in rows}
    check(lanes == expected_lanes, f"[{scope}] 泳道与按原 mod 规则手推的一致：期望 {expected_lanes}，实际 {lanes}")
    return graph, rows


def main():
    with tempfile.TemporaryDirectory(prefix="t249-oracle-") as tmp:
        repo = os.path.join(tmp, "repo")
        os.mkdir(repo)
        h = build_fixture(repo)
        names = {v: k for k, v in h.items()}

        # 所有分支（不含远程）：s1、m、f2、c3、f1、c2、c1。手推：s1 占第 0 列并等 c2；m 新开第 1 列，第二个父 f2 占第 2 列；
        # c2 到达时第 0、1 列都在等它，取第 0 列、合并第 1 列；c1 到达时第 0、2 列都在等它，取第 0 列。
        all_lanes = dict(s1=0, m=1, f2=2, c3=1, f1=2, c2=0, c1=0)
        result = verify_scope(repo, "all", ["--branches", "--tags", "--ignore-missing", "HEAD"], all_lanes, names)
        # 当前分支（HEAD 在 main）：m、f2、c3、f1、c2、c1，side 上的 s1 不出现。
        current_lanes = dict(m=0, f2=1, c3=0, f1=1, c2=0, c1=0)
        verify_scope(repo, "current", ["HEAD"], current_lanes, names)

        if result:
            graph, rows = result
            unc = graph.get("uncommitted")
            status = [e for e in git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all").split("\0") if e]
            check(isinstance(unc, dict) and unc.get("files") == len(status),
                  f"未提交行存在，文件数与 git status 一致（期望 {len(status)}，实际 {unc}）")
            m_row = next((r for r in rows if r.get("hash") == h["m"]), {})
            segs = [s[:4] for s in (m_row.get("segments") or []) if isinstance(s, list)]
            check([1, 0.5, 2, 1] in segs, f"merge 那一行有一条从自己的圆点（第 1 列）通向第二个父提交所在第 2 列的线段：{segs}")

        # 写操作：新建分支，再删除；名字以 "-" 开头被拒且仓库不变。
        before = git(repo, "for-each-ref", "--format=%(objectname) %(refname)")
        p = run_cli(repo, "--action", json.dumps({"type": "createBranch", "name": "made-by-panel", "hash": h["c3"]}))
        after = git(repo, "for-each-ref", "--format=%(objectname) %(refname)")
        check(p.returncode == 0 and f"{h['c3']} refs/heads/made-by-panel" in after.splitlines()
              and len(after.splitlines()) == len(before.splitlines()) + 1, "新建分支后多出且只多出 refs/heads/made-by-panel，指向 c3")
        p = run_cli(repo, "--action", json.dumps({"type": "deleteBranch", "name": "made-by-panel"}))
        check(p.returncode == 0 and git(repo, "for-each-ref", "--format=%(objectname) %(refname)") == before, "删除分支后引用回到原样")
        p = run_cli(repo, "--action", json.dumps({"type": "createBranch", "name": "-f", "hash": h["c3"]}))
        check(p.returncode != 0 and git(repo, "for-each-ref", "--format=%(objectname) %(refname)") == before,
              "名字以 - 开头的新建分支被拒（非零退出），引用不变")
        status_before = git(repo, "status", "--porcelain=v1")
        check(status_before.count("\n") == 2, "写操作没有动未提交的改动")

    print("PASS" if not failures else f"FAIL：{len(failures)} 项")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
