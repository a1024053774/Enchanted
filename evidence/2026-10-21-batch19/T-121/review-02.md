# T-121 复审 02（候选 fa3ee8c67）

**结论：不可合并（NO_GO）。** B1 没有关闭：在请求里加一个本项目的 `task` 字段，就能绕过新加的项目限制，我用真实后台复现了。另外 `create` 被写成允许的命令，实际却用不了；S1 只在进程收到可捕获的信号时才撤回申请。

我全程只读，仓库里的文件一个都没改。临时文件都在 `/private/tmp/t121-rev02/` 下。审查期间实现方在改工作区：`workbench/tests/test_t121_role_request_e2e.py` 多了未提交的 `role_refusals_recorded` 检查和 `refusal-unrecorded` 变异体，RESULTS.md 和 ui-05、green-06 也是未提交状态。`workbench/src` 和 `workbench/terminal` 与 fa3ee8c67 一致。

## 阻塞

**B1（未修好）：加上本项目的 `task` 字段，inbox 和 stop 就能越过项目边界**
- 位置：`workbench/src/daemon.ts:186-192`。只要请求带了 `task`，并且这个 task 属于本项目，任何命令都会被放行。门禁在 `workbench/src/gates/core.ts:3174` 只按命令名把请求转到 `inboxCall` 或 `emergencyStop`，而 `A2AInboxRequest`、`A2AStopRequest`（Effect Schema）解码时会悄悄丢掉多出来的 `task` 字段。这一点我单独验证过：`decodeUnknownSync(A2AStopRequest)({..., task:"own"})` 返回的结果里没有 `task`。
- 复现：探针 `/private/tmp/t121-rev02/probe/probe.py`，结果在 `/private/tmp/t121-rev02/probe-result.json`。步骤是：真实后台，在 `proj` 里开一个终端，经 socket 申请执行主控并由操作员批准；再往夹具库插入任务 `own-task`（proj）、`other-task`（other），以及一条发给 executor、引用 `task:other-task` 的收件箱条目。
  - `inbox_list`（不带 task）返回 `role_command_not_scoped`。这正是现有测试覆盖的情形。
  - `inbox_list` 加上 `task:"own-task"` 返回 ok，**列出了另一个项目的条目**，正文是 "OTHER PROJECT SECRET"。
  - `inbox_ack` 加上 `task:"own-task"`、`id:"entry-other"` 返回 ok，**确认了另一个项目的条目**。
  - `inbox_send` 加上 `task:"own-task"` 返回 ok，可以以 executor 身份发消息给任意收件人。
  - `stop` 加上 `task:"own-task"` 时，后台的项目限制已经放行，请求进入了 `emergencyStop`（返回 `stop_entry_required`，原因只是没有合适的 stop 条目）。`emergencyStop` 本身不比对 `actor.project`，只要存在一条引用了别的项目 worker 的 stop 条目，就能中断那个 worker。
- 现有测试没有覆盖这种写法：`commands_without_project_refused` 只测了不带 task 的写法（测试第 226-232 行）。
- 修法方向：先按命令名拒绝，凡是 `inbox_*`（`inbox_ready` 除外）和 `stop`，不管带不带 task 一律返回 `role_command_not_scoped`；或者改成按命令名列允许清单。还要补一个"带本项目 task 的 inbox_list、inbox_ack、stop 被拒绝"的检查，并用 fa3ee8c67 作已知坏版本，证明这个检查在修前会失败。

## 应修

**N1：`create` 被写成允许的命令，实际用不了**
- 位置：`daemon.ts:166`、`186-192`。
  - `create` 带 `task` 时，会先走 `status` 预检。新任务还不存在，于是返回 `unknown_task`。
  - 不带 `task` 时，门禁解码报 `Missing key ["task"]`，返回 `gate_failure`。
- 探针里两种写法都失败了。但 `a2a help`（`terminalCli.ts:10-12`）、SKILL.md 第 12 行和 README 都写着可以用"带本项目 project 的 create"。
- 要么让 `create` 绕过任务存在性预检，只核对 project；要么从文档里删掉。

**S1（部分修好）：撤回只在 SIGINT、SIGTERM、SIGHUP 时发生**
- 位置：`workbench/src/terminalCli.ts:41-44`。
  - 进程被 SIGKILL 杀掉时不会撤回，申请会一直待批准，之后照样能被批准，也就是 S1 的原问题。我推断 Codex 的命令超时很可能就是这样处理的：默认超时较短，到时间强杀。这一点我没有实测。另外 Codex 拿到的 `developer_instructions`（`workbench/terminal/bin/codex`）也没有告诉它要把超时设长。
  - 收到信号时撤回可能失败，因为批准刚好抢在前面。失败后代码仍然直接退出，退出码是 130 或 143，不输出也不 release，终端就在 agent 不知情的情况下成了主控。只有超时路径（第 54-60 行）处理了这种竞争。
  - 第 49 行：轮询时 `terminal_whoami` 返回失败，代码直接返回，不撤回申请。
  - 第 37-42 行之间如果来了信号，申请已经建好，但处理函数还没装上，申请留着不撤回。这个窗口很窄。
- 后台内部的批准与撤回不会交错（同一个事件循环里同步写入），这部分没有问题。
- 建议：信号路径上撤回失败时，查一次状态；如果已经批准，就 release 或输出结果。更根本的修法是让后台在申请者的连接断开时自己撤回（长轮询），这样也能覆盖 SIGKILL。现有测试只测了 SIGTERM。

## 建议

1. `workbench/terminal/zdotdir/.zshrc:1-5`、`.zprofile:1-3`：用户在 `.zprofile` 或 `.zshrc` 里设的 `ZDOTDIR` 不会被记下来，`.zlogin:1` 会把它换回 `.zshenv` 时的值。`.zlogin:5` 只要用户 ZDOTDIR 等于 `$HOME` 就当作没设（`A2A_USER_ZDOTDIR_SET` 的情况除外），效果一样，不算问题。HISTFILE 的修正（`.zshrc:3`）和 PATH 的两次重排（`.zshrc:7`、`.zlogin:3`）我核对过，没问题；Shell 用 `-l -i` 启动，所以 `.zlogin` 一定会执行。
2. `workbench/terminal/bin/codex`：grep 也会命中 `[profiles.x]` 段里的 `developer_instructions`，这时说明不会注入。影响很小。
3. `terminalCli.ts:43`：SIGHUP 的退出码应为 129，现在是 143。
4. RESULTS 里"不写 ~/.claude"的读回只比对了 `settings.json`、`settings.local.json` 和 `~/.codex/config.toml`。表述应限定在这几个文件，不要写成整个目录。

## review-01 各项核对（读的是代码）

- **B1**：没有修好，见上。不带 task 的写法确实被拒绝了，未知 task 会在进门禁前被拒绝（`daemon.ts:188`），project 不一致会返回 `role_project_mismatch`。
- **S1**：部分修好，见上。
- **S2**：修好了。`zdotdir-dropped` 变异体失败在 `user_zdotdir_kept`，证明这条检查有效。
- **S3、S4**：RESULTS 已写总状态（"待复审"），威胁模型已如实改写。S3 要的读回里，"拒绝留下记录"已补上，但对应的检查 `role_refusals_recorded` 还没提交。
- **S5**：代码、界面和测试里已统一为"角色申请"。
- **建议 1、2、4、5（侧栏刷新部分）**：都已按处理表改动。
- **建议 3**：已改为精确匹配 `developer_instructions=*`，并检查用户的配置文件。这一项仍然没有测试。

## RESULTS.md 必须写明的事实

它已部分更新到 green-06 和 ui-05，review-02 一栏还是"待填"。至少还要写：
- 总状态改为 NO_GO 或 INCOMPLETE，并写明 review-02 的结论。
- B1 的 task 字段绕过，附上复现方法，并说明 `approved_role_limited_to_its_project`、`commands_without_project_refused` 两项检查不覆盖带 task 的写法。验收表里"角色、窗格、项目由后台核对"那一行现在的 PASS 不成立。
- `create` 用不了（或删掉相关文档）。
- S1 不覆盖 SIGKILL，也不覆盖"信号与批准同时发生"。Codex 的超时问题是推断，没有实测。
- green-06 跑的测试文件是工作区里未提交的版本，要写明。
- 修好之后，用 fa3ee8c67 跑一次新加的越界检查，作为修前版本的红态证据。

## 我实际运行的命令和结果

1. `python3 workbench/tests/test_t121_role_request_e2e.py --summary /private/tmp/t121-rev02/green-worktree.json`：跑的是工作区里的测试文件，含未提交的检查。结果 PASS，36 项。
2. 用 `git archive fa3ee8c67 workbench/src workbench/terminal workbench/tests` 解到 `/private/tmp/t121-rev02/root`，再跑 `python3 .../root/workbench/tests/test_t121_role_request_e2e.py --summary /private/tmp/t121-rev02/green-commit.json`。结果 PASS，35 项。
3. 先用 `--help` 确认了参数写法。
4. `--mutant no-withdraw --summary .../mutant-no-withdraw.json`：退出码 1，INCOMPLETE。失败在"被杀的申请没有撤回"，即 `killed_request_withdrawn_and_not_approvable` 那一步；它之前最后通过的一项是 `role_free_again_after_close`。
5. `--mutant zdotdir-dropped --summary .../mutant-zdotdir-dropped.json`：退出码 1。失败在 `user_zdotdir_kept`，读到的 zdotdir 是 `<unset>`。
6. 两个变异体确实生效了：
   - 测试会断言替换的位置只出现一次。
   - zdotdir 变异体那次报出的 `path_first` 是 `/private/tmp/t121-…/source/workbench/terminal/bin`，说明后台是从变异后的源码副本启动的。
   - no-withdraw 改的 `terminalCli.ts` 也在同一份副本里，它的路径由后台 `panes.ts` 按自身位置推出来，所以同样生效。
7. `LC_ALL=C node workbench/tests/test_t107_sidebar.mjs /private/tmp/t121-rev02/t107.json`：PASS，12 项。
8. `LC_ALL=C node workbench/tests/test_t109_hierarchy.mjs /private/tmp/t121-rev02/t109.json`：PASS，9 项。
9. `LC_ALL=C python3 workbench/tests/test_t111_counterfactuals.py --summary /private/tmp/t121-rev02/t111.json`：没带 `--daemon`，PASS，5 项。
10. `LC_ALL=C node workbench/tests/test_t111_flow.mjs /private/tmp/t121-rev02/t111flow.json`：PASS。
11. `node /private/tmp/t121-rev02/excess.mts`：确认 Effect Schema 解码时会丢掉多余字段。
12. `python3 -I /private/tmp/t121-rev02/probe/probe.py /private/tmp/t121-rev02/root /private/tmp/t121-rev02/probe-result.json`：复现了 B1 的绕过和 N1。探针结束时已停掉后台，没有报清理错误。

没跑的：`--revision`、`pending-authority`、`history-in-zdotdir`、`refusal-unrecorded` 这几个变异体；打包版 GUI 和真实 Claude、Codex；`project_map.py status`；T-118 回归。