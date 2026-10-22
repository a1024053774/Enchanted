# T-124 验收结果（2026-10-22）

结论：**INCOMPLETE**。除原生提问一条外，其余验收项都有真实入口的绿态与反例；原生提问在现有 worker 配置下发不出来，待用户裁定（见“未完成”）。独立审查（agy，gemini-3.8-flash-high）结果另见 `review-01.md`。

## 场景

`workbench/tests/test_t124_controller_e2e.py`：真实编排后台、真实 zsh 项目终端与 `a2a`、门禁、真实安装的 Claude Code（worker、reviewer、monitor；`--monitor-cli codex` 时 monitor 为真实 Codex），模型接口是本地脚本化的 Messages / Responses API。步骤：

1. 终端以 Claude Code 的会话环境发 `a2a request executor`，界面批准，终端成为执行主控。
2. 夹具会话日志写入一次额度用完、再恢复，核对侧栏 `controller_quota` 与事件。
3. 主控写任务卡、`create`，在后台线程里 `run`。
4. 主控 `attach` 一个 monitor，核对只读（写项目被拒）和启动记录。
5. worker 用 `issue` 提两个问题：主控回答第 1 个，界面（管理凭据）回答第 2 个。
6. 审查通过后，主控还在时 run 等主控打分。
7. 主控 `a2a release`；这个终端再发 `dispatch`、`run`、`attach` 被拒并记录；然后关闭终端（`--end quota` 变体改为写额度用完，不 release）。
8. run 自己经门禁集成，评分记为未评分并写明原因；monitor 仍在运行。

## 结果

命令：`evidence/2026-10-22-batch20/T-124/e2e/commands.sh green red1 red2 red3 red4`（在 `workbench/` 下运行），退出码见 `e2e/exits.txt`。

| 运行 | 结果 | 停在 |
| --- | --- | --- |
| green-01-release | PASS，22 项 | — |
| green-02-quota（`--end quota`） | PASS，20 项 | — |
| green-03-codex-monitor（`--monitor-cli codex`） | PASS，22 项 | — |
| red-01-parent（`--revision b25d44045`） | 失败 | 超时：额度用完通知（修前没有额度读取，第一步即失败） |
| mutant-01-answer-as-user | 失败 | `controller_answer_recorded_as_controller`：回答 `from: user` |
| mutant-02-run-waits-for-score | 失败 | `run_integrates_after_role_ends`：任务停在 verified |
| mutant-03-run-ignores-active | 失败 | `run_waits_for_active_controller_score`：主控在时已写 `run_initiator_ended` |
| mutant-04-unscored-without-reason | 失败 | `integration_recorded_unscored`：评分缺原因 |
| mutant-05-quota-unread | 失败 | 超时：额度用完通知 |
| mutant-06-monitor-writable | 失败 | `monitor_launch_recorded_read_only` |
| mutant-07-issue-provider-codex | 失败 | 超时：第一个问题（Claude worker 的 `issue` 被拒） |
| mutant-08-snapshot-denies-privileged | 失败 | 超时：审查通过（run 停在 `run_external_unknown`，EPERM） |
| mutant-09-codex-monitor-unbound | 失败 | `restore_cli_unsupported` |

修前版本在第一步就失败，没有走到回答记录那一步；“回答记成用户输入”这一条由 mutant-01 单独证明。

单元证据（`unit/commands.sh`）：

- `test_t124_quota_notice.mjs`：新代码 PASS（6 项）；HEAD 的 `notificationCenter.ts` 失败。
- `test_t093_process_snapshot.py`：PASS（26 项），含 `privileged`、同用户被拒仍失败、ShortInfo ABI 静态断言。
- `test_t121_role_request_e2e.py`：PASS；`answer_and_run_commands_open_to_terminals` 核对四个命令不再返回 `role_command_not_scoped`。

回归（同一工作树，开发期运行）：T-122 e2e PASS（23 项），T-127 e2e PASS（19 项），t112_execution、t110_snapshot PASS。

## 验收项

| 验收项 | 状态 | 依据 |
| --- | --- | --- |
| 终端主控回答 worker 的问题，记为主控的回答，`user_inputs` 不增 | PASS | green-01～03；mutant-01 |
| 界面回答仍记为用户输入 | PASS | green-01～03 第 2 个问题 |
| `run` 中途 release 并关闭终端，任务经门禁做到集成，记录发起者身份已结束 | PASS | green-01；mutant-02、04 |
| 身份结束后这个终端的 `run`、`attach`、派发被拒并留记录 | PASS | green-01 `new_work_refused_after_release` |
| 额度用完时工作台内出现通知，worker 不受影响 | PASS（数据与通知逻辑）；未在真实应用里目视核对 | green-02；quota-notice 单元；mutant-05 |
| 终端主控回答 worker CLI 自己弹出的提问 | **INCOMPLETE**，待用户裁定 | 见下文 |
| 身份结束后 run 自己集成记未评分；主控在时仍等主控 | PASS | green-01、02；mutant-03 |
| `attach` 起挂在任务下的会话，侧栏可见，argv 记入启动记录，身份结束后照常运行 | PASS | green-01～03；mutant-06、09 |
| 修前版本跑同一场景失败 | PASS | red-01、mutant-01 |
| `project_map.py status` 0 问题 | PASS | 提交前运行 |

## 未完成与已知限制

- **原生提问发不出来。** Claude Code worker 以 `dontAsk` 运行，AskUserQuestion 直接被拒，allow 规则与 PreToolUse 钩子都不能放行；Codex 0.163.0 默认模式下 `request_user_input` 返回 “unavailable in Default mode”；`request_user_input_async` 不阻塞，现有回答路径不支持。已写的 `question_answer` 撤回。可选：(a) 保持只经 `issue`；(b) 支持回答 Codex 的异步提问；(c) 改 Claude worker 的权限模式（削弱 dontAsk）。另：PreToolUse 会把被拒的提问登记为“等主控回答”，侧栏短暂显示一个答不了的提问。
- **进程快照偶发“身份变化”。** 第三轮证据（`e2e/run-03-before-wait-check/`）的 green-01-release 一次失败：run 停在 `run_external_unknown`，`process_identity_changed_during_query`。之后 release 变体连跑 9 次与最后一轮都通过，未复现。失败当时 worker 刚开始新一轮、钩子进程在启动；原因未确认。报错现在带出 pid 与变化前后的值。T-093 规定身份变化即拒绝、不重试，改这条超出本票，留给用户决定。
- 后台重启时进程内的 run 停下（supervised-run 规格），monitor 不恢复。
- 工作台界面没有回答 issue 的面板（管理凭据的 `answer_issue` 可用）。
- 额度通知没有在真实应用窗口里目视核对。

## 中途停下的运行

- `e2e/aborted-01/`：测试改为“release 后立即关闭终端”之前的部分运行。
- `e2e/aborted-02/`：`controllerQuota.ts` 去掉逐行 catch 之前的部分运行。
- `e2e/run-03-before-wait-check/`：加强 `run_waits_for_active_controller_score` 之前的完整一轮，含上述偶发失败。

夹具目录在 `/private/tmp/t124-*`，不入库。
