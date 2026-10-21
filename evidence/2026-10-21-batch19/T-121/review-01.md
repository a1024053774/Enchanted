# T-121 独立审查 01（候选 b5feeae24）

审查方式：新开的只读 Claude 子会话（general-purpose），没有看过实现时的对话；只读代码，并重跑后台级 e2e（绿态、两个变异体、修前版本）。用户 2026-10-21 说“codex 太慢了”之后，本票的审查改由 Claude 做。

结论：**不可合并**。

## 阻塞

- **B1** inbox 与 stop 不受项目限制。已批准的终端主控能列出、确认别的项目的收件箱条目，也能对别的项目的 worker 发 stop（`daemon.ts:177-184` 只核对 `input.project`、`input.task`；`core.ts:2939/2957` 只按角色地址区分条目；`emergencyStop` 不比对 `actor.project`）。README 写的“限定本项目”与实现不符。

## 应修

- **S1** `a2a request` 等待超时或被杀后，申请仍待批准，之后批准会让终端在 agent 不知情的情况下成为主控。
- **S2** 用户在 `.zshenv` 里设的 `ZDOTDIR`（XDG 写法）在启动结束后被清掉。
- **S3** RESULTS 没有总状态；“不写 `~/.claude`、`~/.codex`”“拒绝留下记录”“`a2a whoami` 与界面一致”“status 0 问题”缺读回。
- **S4** RESULTS 的威胁模型说法偏强：终端环境导出 `A2A_STATE`，同一用户的进程能读到其中的操作员凭据，能读文件的 agent 可以自己批准自己。
- **S5** 术语：侧栏缺口文字用了“认领”，横幅 `aria-label` 用了“身份申请”，注释与测试 docstring 也混用。

## 建议

1. `window_identity_cannot_approve` 名不副实（窗口身份先被 `window_command_forbidden` 拦下）。
2. `sidebarSnapshot` 的角色申请参数是可选的，流程页不传；`cli` 把展示文字“未知”存进库。
3. Codex 包装命令：参数里任何位置出现 `developer_instructions` 字样都不加说明；用户配置文件里设了这一项时会被 `-c` 覆盖；没有测试。
4. `real-cli.sh` 的 `for dir in $PATH` 会做通配符展开。
5. 批准失败时侧栏不刷新；未命名窗格在横幅里显示为“一个终端”。
6. 终端关闭、后台重启导致的结束只靠推导，不写 `role_request_ended`。
7. （T-122 范围）终端主控收不到收件箱唤醒；它派出的 worker 会显示为未归属。

## 审查员实际运行

- 绿态 PASS（29 项）；`--mutant=pending-authority` 失败于 `pending_request_has_no_authority`；`--mutant=history-in-zdotdir` 失败于 `history_goes_to_user_home`；`--revision=48d4da01b` 失败于 `a2a_command_first_on_path`。审查员核对过变异体确实替换了源码，后台确实从变异源码启动。
- 第一轮变体命令的参数写错，argparse 退出码 2，测试没有执行；审查员删除了 `/private/tmp` 下那几次的 `.out` 输出文件后改正重跑。

## 处理（实现方，2026-10-21）

| 项 | 处理 |
| --- | --- |
| B1 | 采用审查给的第二种修法：终端角色只能调用能在本层核对项目的命令（带本项目 task，或带本项目 `project` 的 `inbox_ready`、`create`）；其他返回 `role_command_not_scoped`；未知 task 在进门禁前拒绝。收件箱按项目区分留给后续通信票 |
| S1 | 超时与 SIGINT/SIGTERM/SIGHUP 时 `role_request_withdraw` 撤回仍待批准的申请；撤回与批准同时发生时如实报告；skill 写明 Bash 超时设 600000 毫秒 |
| S2 | `.zlogin` 在用户环境或用户启动文件设了 `ZDOTDIR` 时恢复它 |
| S3 | 补读回：拒绝事件、XDG 场景、GUI 前后的用户配置文件事实、`!a2a whoami`；RESULTS 写总状态 |
| S4 | RESULTS 如实改写；凭据位置是范围外的决定，交用户 |
| S5 | 统一为“角色申请” |
| 建议 1 | 拆成 `window_identity_cannot_decide`（`window_command_forbidden`）与 `pending_terminal_cannot_decide`；已批准终端调用 decide 由 `commands_without_project_refused` 覆盖 |
| 建议 2 | 参数改为必传，流程页也传；`cli` 未知存 null，显示时再处理 |
| 建议 3 | 只认 `developer_instructions=…`、`--config=developer_instructions=…` 与用户 Codex 配置文件里的该项 |
| 建议 4 | `set -f` |
| 建议 5 | 批准或拒绝后无论成败都刷新侧栏；窗格命名未改 |
| 建议 6 | 未改：结束由终端是否存活推导，`shell_closed` 事件已有时间 |
| 建议 7 | 写进 T-122 |
