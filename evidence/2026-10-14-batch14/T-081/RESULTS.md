# T-081 结果

## 第 7 项结论

用户决定（answer `20261015T044138Z-ideation-answer-001`，2026-10-15，会话「a2a-构思主控」，逐字）：「记为已知行为，不改 (Recommended)」。选项原文：「生产布局下 worker 碰不到主分支；钩子是我方脚本，路径也不在 worker 可写处。T-081 结果里写明结论和未覆盖项（objects 未逐字节清点、pre-commit 钩子在 --no-verify 下未测），然后合并。」按该决定，CAS 重验行为不改。6e 不在本节，等 T-084 合入后再派。

### run-04 是 /tmp 夹具的误报

run-04 观察到 worker 移动共享分支并 push：两条命令各一次 exit 0，共享 `refs/heads/main` 从 G 到 T，本地裸仓库出现 `t081-probe`。夹具在 `/private/tmp/t081-capability-01/run-04/`，见 [capability-run-04/actual-command-results.json](capability-run-04/actual-command-results.json)。`workspace-write` 默认可写 `/tmp`，所以这次成功不能当成生产布局下 worker 碰得到主分支。

生产布局复测在外置盘夹具上，原件 [CAPABILITY-RECHECK-03/run.json](CAPABILITY-RECHECK-03/run.json)（[CAPABILITY-RECHECK.md](CAPABILITY-RECHECK.md) A 节）。同一 `codex sandbox --permission-profile :workspace`：`git update-ref` exit 128（`main.lock`：Operation not permitted），`git push` exit 1（不能创建临时对象目录，远端拒绝 unpacker error）。读回 `main` 仍为 G，裸仓库没有 `t081-probe`。对照夹具 `/tmp/t081-capability-recheck-02` 上两条都是 exit 0，`main` 变为 T，裸仓库新增 `t081-probe`。

### 沙箱外 git commit 的实际范围

要点来自 [COMMIT-SCOPE.md](COMMIT-SCOPE.md)，原件 [commit-scope-run-01/run.json](commit-scope-run-01/run.json)。夹具在外置盘。19 步都是 `MEASURED`，没有模型回合。

`prefix_rule` 判为 `allow` 的 `git commit`，包括其后的 `--template`、`-F`、`--fixup`、`--amend`、`--no-verify`、`--trailer`、`--cleanup`，在沙箱外、cwd 为检出 `main` 的 worker worktree 时 exit 0，并推进共享 `refs/heads/main`。基线 `post-commit` 调用的 `git update-ref refs/heads/hook-side` 也成功。这些命令没有改 `packed-refs`、`config`（含 `core.hooksPath` 与 `include.path`）、钩子脚本、他人分支 `other`、`packed-keep`，以及另一个 worktree 的 `.git/worktrees/<name>/`。

不匹配 allow 的 argv 在 `codex sandbox --permission-profile :workspace` 里运行：`commit` 前的 `-c`、`--git-dir`、`--work-tree`、`-C`，以及 `GIT_DIR`、`GIT_WORK_TREE`、`GIT_INDEX_FILE`、`GIT_CONFIG_PARAMETERS`、`GIT_CONFIG_COUNT`/`KEY`/`VALUE` 的 shell 前缀。它们在创建 `index.lock` 时得到 Operation not permitted，exit 128，指定读回与命令前相同。`git config core.hooksPath` exit 255，不能锁定 `config`，随后那条 allow 的 `git commit` 仍走原来的钩子目录。

生产启动把 `core.hooksPath` 指到编排方自己的目录，不在 worker worktree 里：

- [`workbench/src/panes.ts:172`](../../../../workbench/src/panes.ts:172) 对非审查会话设置 `GIT_CONFIG_COUNT=1`、`GIT_CONFIG_KEY_0=core.hooksPath`，`GIT_CONFIG_VALUE_0` 为 `fileURLToPath(new URL("../hooks/", import.meta.url))`，即本仓库 `workbench/hooks/`。
- [`scripts/launch-worker:46`](../../../../scripts/launch-worker:46) 取 `scripts/git-hooks`，[`scripts/launch-worker:90`](../../../../scripts/launch-worker:90) 把它写入 `GIT_CONFIG_VALUE_0`。

### CAS 外部移动

[CAPABILITY-RECHECK.md](CAPABILITY-RECHECK.md) C 节的代码事实：门禁第一次发现工作分支已经移动时不立即拒绝。它清除集成意图，重新验收并重新审查；前三次 miss 重验，第四次进入 `paused`。若重验与审查通过，被移入的提交可以作为新 G 的祖先留在工作分支上，并且不出现在审查 diff（`attempt.base_commit..C`）里。用户决定这条行为不改。

### 未覆盖项

- `objects/` 未逐字节清点。`rev-parse` 能解析新提交，只说明引用指向它。
- `--no-verify` 下的 `pre-commit` 与 `commit-msg` 未测。commit-scope 夹具只装了 `post-commit`，该钩子在 `--no-verify` 下仍然运行。本机 `git commit -h` 写明 `--no-verify` 绕过的是 `pre-commit` 和 `commit-msg`。
- [`panes.ts:160`](../../../../workbench/src/panes.ts:160) 的三个动态 `-c`（`hooks.UserPromptSubmit`、`hooks.Stop`、`hooks.PermissionRequest`）未进入这次沙箱包装。

### 注意事项

测试夹具不要放在 `/tmp` 或 `$TMPDIR`。`workspace-write` 默认可写这些位置，沙箱拒绝会被测成允许。
