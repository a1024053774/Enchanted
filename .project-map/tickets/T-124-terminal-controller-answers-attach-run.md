---
id: T-124
title: 终端主控能回答问题、接管会话、自动运行：回答记为主控的话，已派出的工作做完为止
type: build
status: closed
blocked_by: [T-122]
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 2
---

## What to build

来源：T-121 第 3 轮审查（`evidence/2026-10-21-batch19/T-121/review-03.md` 建议 1、2）与用户 2026-10-21 的决定。用户逐字：“现在都不开放,那也要解决啊,不解决我这软件怎么用呢.”

T-121 暂时不让终端角色调用四个门禁命令，原因各不相同：

- `answer_issue`、`answer_issues`：门禁把回答一律记成用户输入（`from: "user"`、`user_inputs`、`dispatch_origin: "user"`），主控回答也会被当成用户说的话，违反“主控发出的提示词不算用户输入”。
- `attach`：把已有会话接到任务上。
- `run`：自动运行内部的派发与验收只在开头核对一次调用者。

用户 2026-10-21 对“身份结束后运行是否停下”的决定（逐字）：“主控身份结束算什么?主控一般不会退出,额度到了的话,之前的 worker该执行应该还能继续执行,到完成该任务,不然很影响进度,因为每次拍的任务其实也不大,也不用太担心它做的很多偏离轨迹”。所以已经派出去的工作不因主控身份结束而停下。

要做的：

- 回答按调用者记录：主控回答记为该主控的回答，不进用户输入；用户在界面里的回答仍记为用户输入。
- `attach`、`run` 在主控身份结束（release、终端关闭、后台重启、主控额度用完）后，已开始的任务照常做到完成：worker 继续执行，交付、审查、验收、集成仍走门禁检查串。身份结束只是不再接受这个终端发起新的派发或新的运行；运行记录里写明发起它的主控身份已结束。
- 这四个命令对已批准的终端主控开放，仍受 T-121 的项目边界约束。
- 2026-10-22 读代码后发现的事实与用户裁定：
  - `integrate` 必须带主控评分，`run` 审查通过后停在 `waiting_executor` 等主控。用户选“run 自己集成，记未评分 (Recommended)”：主控身份已结束时，`run` 自己经门禁集成，评分记为“主控身份已结束，未评分”，指标里单独计；主控还在时照旧由主控带分集成。
  - 工作台运行时没有实现 `createAttachedThread`，`attach` 只会返回 `runtime_required`。用户选“本票一起实现”。
  - 工作台运行时也没有实现 `sendUserAnswer`，`answer_issue` 在工作台里投递不了；本票补上。
  - worker 的 CLI 自己弹出的提问（AskUserQuestion、request_user_input）在侧栏标“等主控回答”，但主控没有命令能回答。用户选“本票一起做 (Recommended)”：终端主控可以回答，写回 worker 窗格，记为主控的回答、不进用户输入；用户在界面回答仍记为用户输入。
- 主控额度用完：在工作台内部发通知（不用系统通知），已派出的工作照常继续。用户 2026-10-22 逐字：“额度用完做个通知就行，我们软件内部的通知”；其余按执行主控的方案（“其余的就按你说的来”）。

## 实现中发现（2026-10-22）

- **worker 的原生提问在现有配置下发不出来，`question_answer` 没有可答的对象，已撤回，待用户裁定。** Claude Code worker 以 `--permission-mode dontAsk` 运行，`AskUserQuestion` 直接被拒（“Permission to use AskUserQuestion has been denied because Claude Code is running in don't ask mode”）；加 allow 规则、PreToolUse 钩子返回 allow 都没用（e2e 开发运行 03、04）。Codex 0.163.0 的 `request_user_input` 在默认模式下返回 “request_user_input is unavailable in Default mode”（探针，原生日志 function_call_output），只在 Plan 模式可用；`request_user_input_async` 不阻塞，现有回答路径（`nativeAnswerKeys`）不支持。worker 要问只能经 `issue`，这条本票已打通。另：PreToolUse 已把这类被拒的提问登记为“等主控回答”，侧栏会短暂显示一个答不了的提问；开发运行 03 中对它写入的两个 Enter 进了 worker 的输入框。
- 门禁把没有附加会话的线程一律当成 Codex：Claude Code worker 的 `issue` 和 run 回收 worker 都被拒（`identity_conflict`）。改为按任务卡的 CLI 判断。
- Claude Code 在 worker 进程树里跑 setuid-root 的 `/bin/ps aux`，进程快照对它读 `PROC_PIDTBSDINFO` 得到 EPERM，run 中途停在 `run_external_unknown`。改为：被拒且属于别的用户的进程用 `PROC_PIDT_SHORTBSDINFO` 记录，标 `privileged`，不认作 CLI 主进程；属于本用户的进程被拒仍失败。
- Codex monitor 绑定原生会话时记录续接 argv，旧代码只认 worker、reviewer，monitor 每次读原生记录都失败。
- 后台重启时进程内的 run 停下（supervised-run 规格），monitor 不会被恢复。候选 2 按用户裁定 4 改掉，见下节。

## 用户裁定（2026-10-22，候选 1 之后）

用户逐字：“1.a  2 放宽 3 也要支持一下 cluade 和 codex 的额度监控 4.这个要解决”。对应：

1. 原生提问选 (a)：worker 只经 `issue` 提问，不做 `question_answer`；原生提问一条验收改为“被拒的原生提问不登记为等主控回答”。
2. 进程快照的“查询中身份变化”放宽：非根进程的身份变化重新取一次快照，不直接拒绝。
3. 主控额度监控覆盖 Claude Code 与 Codex 两种主控，并在真实应用窗口里核对通知。
4. 后台重启后，进程内的 run 接着跑，monitor 恢复。

候选 2 的做法：

- 1：Claude Code 受管会话的启动参数加 `--disallowedTools AskUserQuestion`，模型拿不到这个工具；非主控窗格的原生提问记 `native_question_ignored`，不登记为等主控回答。Codex worker 的 `request_user_input` 在默认模式下本就不可用。
- 2：根进程以外的进程在读取中身份或父进程变化，换新的读取器重取整棵树，最多 3 次；根进程变化和其他错误仍立即失败。输出带 `attempts`。
- 3：Codex 主控从会话日志读 `task_complete` 的 `usage_limit_exceeded`，恢复时间取最近一条 `token_count` 里已满额的窗口；格式对照过用户自己的 Codex 日志。两种主控都在真实工作台窗口里出现、消失过通知并截图。
- 4：后台启动时，状态为 running（或因后台停止而暂停）的 run 接着跑，保留原截止时间。原 attempt 的 worker 进程随后台一起结束的（任务在 claimed、reviewing 或 paused），先经门禁回收再重新派发（同 T-096 裁定 B）；已通过审查的直接继续验收、集成。重启时被打断的 worker、reviewer 窗格在确认进程已退出后登记为已停止。monitor 按原启动记录恢复。这一条取代 supervised-run 规格第 6 条“不自动重新投递”在后台重启场景下的规定。

候选 1 的独立审查（`review-02.md`，agy gemini-3.8-flash-high）四条发现在 28a0550cc 上核对成立，候选 2 都已修复：monitor 回收时停止、归档两处仍按任务仓库比对工作目录（e2e 加 `monitor_reclaimed` 与变异 reclaim-monitor-repo）；额度日志的空行与坏行让读取永久停止（跳过空行，坏行记一次后继续，`torn_log_line_recorded_once` 与变异 quota-stops-at-bad-line）；`--fast` 的错误信息写成 blocking；两条变异注释顺序颠倒。

## Acceptance

证据：`evidence/2026-10-22-batch20/T-124/RESULTS.md`（候选 1）与 `candidate-2/RESULTS.md`（候选 2）。候选 2 各项有绿态与反例，独立审查 PASS。


- [x] 终端主控回答 worker 的问题：worker 收到回答；库里记为该主控的回答，`user_inputs` 没有新增。
- [x] 用户在界面回答同一类问题仍记为用户输入（回归）。
- [x] 终端主控启动 `run`，中途 `a2a release` 并关闭终端：已派出的 worker 继续，任务经门禁做到集成；记录里写明发起者身份已结束。
- [x] 身份结束后，这个终端再发起 `run`、`attach` 或新派发被拒绝并留记录。
- [x] 主控额度用完时，工作台内出现通知；已派出的 worker 不受影响。
- [x] Claude Code 与 Codex 两种主控的额度通知都在真实应用窗口里核对。
- [x] （用户裁定 1 改写）worker 只经 `issue` 提问：受管会话拿不到原生提问工具。（非主控窗格仍出现原生提问时记 `native_question_ignored`、不登记为等主控回答：只有代码，没有直接证据，见候选 2 RESULTS。）
- [x] 进程快照里非根进程的瞬时身份变化不再让 run 停下；根进程变化仍拒绝。
- [x] 后台在 run 进行中重启：run 接着跑到集成（worker 已退出的先回收再重新派发），monitor 恢复。
- [x] 主控身份结束后 `run` 自己集成，评分记为未评分并写明原因；主控在时 `run` 仍等主控带分集成（回归）。
- [x] 终端主控 `attach` 在工作台里起一个挂在任务下的会话，侧栏可见、启动 argv 记入启动记录；主控身份结束后该会话照常运行。
- [x] 修前版本（回答记成用户输入）跑同一场景失败。
- [x] `project_map.py status` 0 问题。

## Resolution

2026-10-22 PASS，最终候选 374a7c924。终端主控回答记为主控的回答；主控身份结束或额度用完后，`run` 经门禁做到集成并记为未评分；`attach` 的 monitor 只读，可经门禁回收。按用户裁定：worker 只经 `issue` 提问，进程快照放宽，Claude Code 与 Codex 两种主控的额度通知都在真实窗口里核对，后台重启后 run 接着跑、monitor 恢复。各项都有真实入口的绿态与反例，见 [候选 2 RESULTS](../../evidence/2026-10-22-batch20/T-124/candidate-2/RESULTS.md)。独立审查：候选 1 由 agy（gemini-3.8-flash-high）审出四条，都已修复；候选 2 复审 PASS，无发现（`candidate-2/review-03.md`）。没有直接证据的一条：非主控窗格仍出现原生提问时记 `native_question_ignored`，这条路径没有被触发过。
