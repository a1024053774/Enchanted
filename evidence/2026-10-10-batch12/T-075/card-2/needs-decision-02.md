# T-075-2 needs-decision 02：第二轮探针的退出码预期过窄

状态：**BLOCKED**。本轮原始结果为 INCOMPLETE，分类为 **fixture-error**；不是 Git 新协议失效，也不是产品红态。执行主控决定 02 第 3 条要求“新协议的探针失败或结果不明时，再次停下”，因此保留失败后没有修探针重跑，没有开始产品实现。

## 已取得的事实

本机仍为 Git 2.52.0。第二轮先单独运行 `symref-verify HEAD refs/heads/main`，prepare/abort 均成功，并观察到 linked worktree 的 `HEAD.lock`；该探针前后的 refs、HEAD、索引、文件原文、reflog 一致。

随后运行决定 02 方案 (a)：在夹具的 SQLite 操作锁内核对 symbolic HEAD，Git 事务只更新 `refs/heads/main`，不另排 `symref-verify`。prepare 成功，文件系统里实际出现两个 Git 锁：

```text
repo/.git/refs/heads/main.lock
repo/.git/worktrees/linked-main/HEAD.lock
```

并发更新工作分支被拒，退出 128。并发 `git symbolic-ref HEAD refs/heads/other` 也被拒，stderr 为 `cannot lock ref 'HEAD'`，退出 **1**。

## 探针自身的错误

`probe-git-rev2.py:235` 把后一个命令的合法拒绝退出码误写成只有 128。需求只要求该次并发写入被拒，并未规定 Git CLI 必须退出 128。后面的业务断言本来也是 `returncode != 0`，但过窄的前置退出码检查先失败了。

因此，这次看到的是预期中的锁拒绝被错误标成夹具失败。应由 worker 承担这个探针错误；不能把它报告成 Git 不支持锁，也不能用此次失败证明业务缺陷。

失败后 with 清理关闭事务 stdin，Git 对未提交事务正常 abort；没有终止进程、删锁、reset 或 stash。其余正常快进、脏文件、CAS 竞争与全部中断窗口尚未运行。HEAD reflog 的隐式追加尚未验证，不能把“发现 HEAD.lock”替代这一项证据。

## 最小请求

请允许只修正本处夹具的退出状态判断：接受 Git 的非零拒绝结果，并继续核对 HEAD/分支及原文件状态不变；不改真实事务、业务预期或批准的集成协议。使用新标签重新运行剩余探针。需要 ps/信号的中断窗口仍交执行主控执行；任何实际协议失败仍立即停止。

这不是请求弱化锁检查：正确的独立预期来自 PLAN 的“prepare 后对方不能改被锁 ref”，不是从实际输出反推 1 为业务答案。

## 原始证据与重现

- 首轮脚本与失败现场未改；第二轮脚本为 [probe-git-rev2.py](probe-git-rev2.py)。
- [独立 symref-verify 实际锁](probe-git-normal-02/symref-standalone-prepared-locks.json)。
- [分支事务实际锁](probe-git-normal-02/branch-update-locks-prepared-locks.json)。
- [完整命令及协议 I/O](probe-git-normal-02/commands.json)、[断言](probe-git-normal-02/assertions.json)、[结果与 traceback](probe-git-normal-02/result.json)。
- [完整夹具归档](probe-git-normal-02/artifacts.tar.gz)，原目录仍在 `/tmp/a2a-t075-2-git-txg0dl4t`。

本轮精确命令：

```sh
/opt/homebrew/bin/python3.11 -B evidence/2026-10-10-batch12/T-075/card-2/probe-git-rev2.py probe-git-normal-02
```

重现须换新标签，如 `probe-git-normal-repro-03`；现有目录拒绝覆盖。

当前共享 checkout HEAD 为 `fc6d2bab8490a8b6e00e04b38cee21de2167447d`；任务原始起点仍为 `e5e7dbb841131935aac0bd061649a55e7a1e7d20`。本轮未修改产品和 acceptance，未提交。
