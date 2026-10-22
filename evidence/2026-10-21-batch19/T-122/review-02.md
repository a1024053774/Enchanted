# T-122 独立审查 02（候选 c6120a562，文档 3cf6e2c8d）

审查者：本 session 新开的只读审查子会话（Claude，干净上下文），2026-10-21。中途遇到用户每周额度上限，恢复后完成。探针脚本见 `review-02-probe/`，现场原在 `/private/tmp/t122-review02/`。探针用本地脚本化接口驱动真实 Claude Code 2.1.306（`-p`），参数按 c6120a562 的 `claudeArgv` 与 `workerGitDenied` 复现，所有 ref 已打包，并在 worker 启动后新建一个 attempt worktree。原始输出见 `review-02-probe/run-results.txt`。

**总体结论：需修复。** 逐 ref 的 denyWrite 清单堵不住 `.git`。

## 发现

1. **N1 高：worker 能建 `refs/replace/*`**（run-results 第 06 项 rc=0）。这会改写整个仓库读到的对象；门禁的 git 调用没有设 `GIT_NO_REPLACE_OBJECTS`。
2. **N2 高：能覆盖 `objects/` 里已有的对象文件**（第 07 项 rc=0）。
3. **N3 中：`info/exclude`、`info/attributes`、`info/grafts`、`shallow` 可写**（第 08～11 项）。
4. **N4 中：denyWrite 是启动时快照。**
   - 启动后才建的 ref 与 worktree 仍可写：第 04 项能移动后来的 attempt 分支，第 13 项能写后来 worktree 的 HEAD。
   - 能建 `main.lock`（第 12 项），可挡住集成。
   - 能预建下一次 attempt 的分支（第 05 项）。
5. **N5 中：`git -c core.hooksPath=/dev/null commit` 能做无尾注提交**（第 17 项 rc=0），门禁会把它记成用户本人提交。
6. **N6 低：Effort 尾注的放宽条件看的是 `delivery.cli` 是否以 “(Claude Code)” 结尾**，应看启动记录的 CLI；也没有变异覆盖。
7. **N7 低：`reviewLaunch` 有几处没核对。**
   - 不查 `argv[0]`。
   - 不查 `argv[4]`、`argv[6]` 是否等于 worker 的模型与强度。
   - 钩子命令用 `includes` 判断，带前缀的命令也能通过。
8. **N8 低：README 里“新分支名不影响集成”不成立**（见 N4）。
9. **未覆盖**：
   - `/clear` 与自动压缩换会话号后，既不修正也不记录。
   - 启动期限与“启动后不再代按信任”没有测试。

## 审查者核实无问题的点

- 写主仓库 main 与之前 attempt 的分支：被拒（第 02、03 项）。
- 写其他 worktree 的 gitdir、`.git/config`、本 worktree 的 commondir：被拒（第 14～16 项）。
- shell 写出 worktree：被拒（第 19 项）；Write 工具写外面：被拒。
- 用户、项目与本地设置里的钩子都没有执行（夹具里三个 marker 都没出现）。

## 处理（候选 3）

用户选“git add/commit 走沙箱外”：
- 整个 Git common dir 对沙箱 deny（probe-05 另 deny 了 worktree 的 `.git` 文件；e2e 07 的红态与变异显示 Claude 沙箱本身就拒写它，实现里去掉了这一项）。
- 只有单独的 `git add`、`git commit` 列入 `sandbox.excludedCommands`，与 Codex 那两条前缀规则相同。
- `probe-05` 先确认了 Claude 的匹配规则。

以上处理覆盖 N1～N5。N1 的根因在 worker 能写 refs，所以门禁不另加 `GIT_NO_REPLACE_OBJECTS`。N6、N7、N8 与未覆盖项的处理见 `RESULTS.md`。
