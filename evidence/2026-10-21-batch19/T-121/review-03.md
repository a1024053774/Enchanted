# T-121 复审 03（候选 99c3c9fba，对比 fa3ee8c67）

**结论：不可合并（NO_GO），但范围很小。** review-02 的 B1 和 N1 都修好了；S1 大体修好，SIGKILL 和 daemon_stop 两种情况我都实测过。不过新的按命令放行清单里，`card_*`/`create` 对"还不存在的 task id"放行，这类 id 没有项目归属。我用真实后台复现了：一个终端主控能读到、追加、抢占另一个项目尚未创建任务的任务卡。这和 B1 是同一条项目边界。除非用户决定把它列为已知边界，否则按 B1 的标准算阻塞。另外，提交里的 RESULTS.md 还停在 fa3ee8c67 的状态。

我全程只读，没有改仓库。临时文件都在 `/private/tmp/t121-rev03/` 下。工作区里有一个未提交的 `evidence/2026-10-21-batch19/T-121/ui-06/`，不是我写的，我没动。`workbench/` 与 99c3c9fba 一致。

## review-02 各项核对

- **B1 已修好。** 后台在 `workbench/src/daemon.ts:205-219` 按命令名放行：
  - inbox_* 与 stop 不论带不带 task，都返回 `role_command_not_scoped`。green 的 `task_field_errors` 四项都是这个错误码。
  - 变异体 `task-widens-scope` 恢复第 1 版的规则后，失败在 `task_field_does_not_widen_scope`，其中 `inbox_list` 返回 ok。变异体确实生效：`path_first` 是变异后的源码副本路径。
  - 门禁里的任务命令我逐个看过（`gates/core.ts:3196-3500`）：`issues`/`events`/`status` 按 taskId 查；`reclaim` 核对 attachment.task_id 与 attempt.task_id；`revise`/`revoke`/`dispatch`/`claim`/`verify`/`integrate` 都作用在 load(taskId) 上。没有找到作用到另一个项目已存在任务的路径。ideation 角色的写操作会在 `core.ts:3229` 返回 `controller_required`。
- **N1 已修好。** 终端能在本项目创建任务（`terminal_controller_creates_task_in_own_project`）。另一个项目、或 repo 不符时会被拒绝（`other_project_task_and_repo_refused`）。
- **S1 大体修好。** 改为后台在连接上等待，`daemon.ts:178-198`、`621`：
  - SIGKILL 后撤回，原因记为 `asker_gone`。变异体 `no-withdraw` 失败在"被杀的申请没有撤回"。
  - 连接关闭的检测可靠：服务端 allowHalfOpen 是默认值 false，客户端（`transport.ts`）收到响应前不会半关闭。
  - daemon_stop 的行为我实测过：等待中的申请 0.11 秒内被撤回，原因 `daemon_stopping`，shutdown 不被 10 分钟的等待拖住。轮询间隔 200ms，`activeRequests` 能正常清零。
  - 剩下的缺口见 S1' 和 S2'。

## 阻塞

**B2：还不存在的 task id 上的 card_* 与 create 没有项目归属，能读、写、抢占另一个项目的任务卡草稿**

- 位置：`daemon.ts:170`、`214`。status 返回 `unknown_task` 时，`card_template`/`card_validate`/`card_save`/`card_show`/`create` 都放行；而 `task_card_versions` 表（`core.ts:157`、`3281-3304`）只按 task 记录，不记项目。
- 复现：探针 `/private/tmp/t121-rev03/probe/probe.py`，结果在 `/private/tmp/t121-rev03/probe-result.json`。步骤：真实后台，`proj` 里的终端申请执行主控并获批；操作员（扮演 other 项目的主控）为 `other-2` 执行 card_save，但不 create。
  - 终端 `card_show other-2` 返回 ok，**读到了 other 项目的任务卡**（`card_show_foreign_pending`）。
  - 终端 `card_save other-2 expected_version=1` 返回 ok，**给它追加了第 2 版**。
  - 终端 `create other-2 project=proj card_version=1` 返回 ok，**用 other 的卡在 proj 建出了这个任务**；other 随后的 create 返回 `task_exists`。
  - 反过来，终端先给 `future-1` 存卡，other 项目随后 `card_save expected_version=0` 会返回 `card_version_conflict`。
- 两种情况下都会发生：id 恰好重复（task id 全局唯一），或者有意为之。按 RESULTS 的威胁模型，后者本来就不在防范范围内；前者属于正常使用。
- 另有一个检查与执行之间的时间差（TOCTOU）：status 预检返回 `unknown_task` 之后、card_save/card_show 执行之前，如果另一个项目恰好 create 了同名任务，就会写到或读到那个已存在任务的卡。窗口很窄，属于同一类问题。
- 最小选项：
  - (a) card_save 记下保存者的项目；card_show/card_save/create 遇到别的项目的草稿时拒绝；或者
  - (b) 未知 task 只放行无状态的 `card_template`/`card_validate`，card_save 只在该 id 还没有任何卡版本时放行，并在后台登记归属；或者
  - (c) 用户接受为已知边界，写进 RESULTS。
- 现有测试只覆盖了"已存在的 other 任务上的 card_save"（`test_t121_role_request_e2e.py:399-400`），没有覆盖未创建任务的情况。

## 应修

**S1'：不带 `wait_seconds` 的 role_request 路径还在，申请可以在没人等的情况下一直挂着、之后照样能被批准**

- 位置：`daemon.ts:180`。`a2a call '{"command":"role_request","role":"ideation"}'` 会经 `terminalCli.ts:43-50` 原样转发。
- 实测：申请返回 `pending`，连接关闭 1 秒后操作员批准，返回 ok，状态是 `approved`（`nowait_late_decide`）。这正是 S1 原来的问题。
- 产品代码里唯一的调用方（`terminalCli.ts:41`）总是带 600 秒，这条不等待的路径只有测试在用。按项目规则应删掉：要求必须带 `wait_seconds`，否则拒绝。

**S2'：连接关闭和批准几乎同时发生时，批准占先，但 agent 永远收不到结果**

- 位置：`daemon.ts:190-197`。循环先检查 `approved`，再检查 `asker.gone`，每 200ms 轮询一次。
- 实测 5 次：客户端关闭连接后立刻批准，5 次都变成 `approved`，`terminal_whoami` 显示 role=ideation（`close_then_approve`）。我没有区分这是关闭事件晚于批准请求被处理，还是落在了 200ms 的轮询窗口里；两种情况的结果相同。
- 后果：终端在 agent 不知情的情况下成了主控，这正是 S1 要防的情形，只是窗口变窄了。
- 建议：在 `close` 回调里同步撤回仍待批准的申请，不等下一轮轮询；同时让 `role_request_decide` 遇到等待者已离开的申请时拒绝批准。

## 建议

1. `answer_issue`/`answer_issues` 在放行清单里。`answerIssues`（`core.ts:808-930`）不看 actor，会写 `from:"user"`、`user_inputs`（certainty observed）和 `human_intervention dispatch_origin:"user"`，等于让主控的话被记成用户输入。现在后台的 runtime 没有 `sendUserAnswer`，实测返回 `native_runtime_required`，所以暂时调不到。但一旦接上 runtime，就会违反"主控发出的提示词不算用户输入"。建议从终端放行清单里去掉这两个命令（`attach` 同理，现在也缺 runtime），或者在门禁里按 actor 拒绝。
2. `run`（`core.ts:3244`、`2611`、`2655`）内部的 dispatch 和 verify 不带 actor 调用，`assertActive` 只在开头检查一次。终端角色 release 或终端关闭后，正在跑的 run 会继续派发、验收。这是读代码得出的推断，没有实测。
3. `daemon.ts:621` 的注释和 SKILL 里"被杀都会撤回"的说法，在 S1' 和 S2' 修好之前都不完全成立。

## RESULTS.md 必须写明的事实

- 现在提交的版本还写着"候选 fa3ee8c67""总状态：待复审""review-02（待填）"，验收表引用的是 green-06，没有 green-07～09、mutant-*-08/09、regress-*-03/04 这些已提交文件的行。需要补上第 3 版候选 99c3c9fba 一行，以及 review-02 和 review-03 的结论。
- 总状态按本轮写 NO_GO 或 INCOMPLETE。"角色、窗格、项目由后台核对"一行不能写 PASS：B2 已复现，或者经用户同意列为已知边界并引用用户原话。
- B1 修前的红态证据是变异体 `task-widens-scope`。`--revision fa3ee8c67` 失败在更早的 `terminal_controller_creates_task_in_own_project`（返回 unknown_task，即 N1），根本没有跑到 `task_field_does_not_widen_scope`。要如实写出这一点，不能说 fa3ee8c67 被新的越界检查拦下。
- S1 的覆盖范围：带等待的路径，覆盖 SIGKILL（asker_gone）、daemon_stop（daemon_stopping）和超时。没有覆盖：不带 wait_seconds 的申请（S1'），以及关闭与批准同时发生（S2'）。
- answer_issue 和 attach 现在只是因为缺 runtime 而调不到，不是被放行清单挡住的。
- 工作区里的 `ui-06/` 还没有提交。如果要引用，要写明对应哪个构建和哪次提交。
- 原有的已知边界保留：操作员凭据可读，界面批准防不住有意绕过的 agent。

## 我实际运行的命令和结果

1. `python3 workbench/tests/test_t121_role_request_e2e.py --summary /private/tmp/t121-rev03/green.json`：PASS，39 项，退出码 0。
2. `--mutant task-widens-scope --summary /private/tmp/t121-rev03/mutant-task-widens-scope.json`：INCOMPLETE，退出码 1。失败在 `task_field_does_not_widen_scope`（inbox_list 返回 ok，inbox_ack/stop 返回 unknown_inbox_entry，说明已经进了门禁）。path_first 是变异源码副本，变异确实生效。
3. `--mutant no-withdraw --summary .../mutant-no-withdraw.json`：INCOMPLETE，退出码 1。失败在"被杀的申请没有撤回"，前一项通过的是 `role_free_again_after_close`。变异源码副本同样生效。
4. `--revision fa3ee8c67 --summary .../rev-fa3ee8c67.json`：INCOMPLETE，退出码 1。失败在 `terminal_controller_creates_task_in_own_project`（返回 unknown_task）。
5. `python3 -I /private/tmp/t121-rev03/probe/probe.py /Users/luckye/Documents/Code/a2a /private/tmp/t121-rev03/probe-result.json`：第 1 次没跑完，是我的探针缺陷（夹具 issue 缺 issue_id，等待条件写错），修正后第 2 次跑完，退出码 0，结果见上文。探针结束时后台已停止；收尾时的第二次 daemon_stop 返回 daemon_stopping，没有残留进程（pgrep 查过）。
6. `git archive 99c3c9fba workbench` 解到 `/private/tmp/t121-rev03/root`，最后没用上：缺 node_modules。探针改用仓库工作区运行，其 `workbench/` 与提交一致。

没跑的：`pending-authority`、`history-in-zdotdir`、`zdotdir-dropped`、`refusal-unrecorded` 这几个变异体；T-107、T-109、T-111、T-118 回归；打包版 GUI 和真实 Claude、Codex；`project_map.py status`；answer_issue 在接上 runtime 之后的实际效果（只读了代码）；run 在角色结束后继续执行（只读了代码）。