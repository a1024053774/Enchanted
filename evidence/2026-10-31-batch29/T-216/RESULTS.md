# T-216 结果（主控记录，2026-11-01）

结论：**PASS**。worker 上报的问题（含 blocking）先经收件箱、由后台用 hc 送进执行主控终端；送法只在主控可接收时送、不用 force、送入确认不了的记未知不重发。主控终端里的提交按我们自己的派发标记认领来源：等于一条已写下送入意图、还没被认领的派发全文，就记为系统，只认领一次；其余提交是用户输入，一次提交记一条。项目终端里的 Codex 关掉换模型提示。

## 候选与提交

- 基线 `9c0e26212`，分支 `t216-issues-controller-first`，worktree 提交 `137ea70dd`，cherry-pick 到 main 为 `889033ef8`，没有冲突。
- 前六轮由侧边栏 Codex worker 写；第七轮按用户 2026-11-01 改的分工由 Claude Code 主控在会话里写（“antigravity 换用里面的 4 argon 模型可以做一些小任务, gpt 做审核,work 的工作由你在当前会话中做.”）。提交内容与冻结的 `round7-candidate.patch` 一致（逐字节比较）。
- 合入后在 main 上复跑 Codex 来源用例与 T-216 主路径 `--gui`，都退出 0。

## 第七轮做了什么

1. **来源规则**（执行主控决定，不是用户裁定）。第六轮两份审查分别复现了两侧错误：只凭送入意图会吞掉没送出的用户输入；要求 hc 成功返回已落库，又会把已送进去、但返回落库前后台崩溃的系统派发记成用户输入。第七轮改为按自己的标记认领：每条派发以唯一的 `⟦主控 #序号⟧` 开头并带收件箱条目 UUID，提交全文等于已写下意图、未认领的派发即认领为系统，只一次；最新事件是 `hc_send_rejected` 时不认领。已接受的代价：意图写下后、RPC 之前后台崩溃，正文没进终端，之后用户逐字提交同一段（含序号与 UUID）会被认领为系统。
2. **真实 Codex 丢通知**。第六轮真实供应商 Codex INCOMPLETE 的原因从现场查明：回合结束时 Codex 弹出“Approaching rate limits / Switch to gpt-6-luna?”选择框，OSC 仍报 done；通知被粘进选择框，回车选中第一项，主控模型被换成 GPT-6-Luna。修法：`terminal/bin/codex` 加 `-c notice.hide_rate_limit_model_nudge=true`，与受管 worker（T-167）相同；额度横幅仍显示，用户自己传的 `-c` 在后面，仍能覆盖。

## 验收条目

| 条目 | 状态 | 依据 |
| --- | --- | --- |
| 修前红态：主控终端收不到投递；blocking 一上报就计入“等你决定” | PASS | 第一轮原始红态，见 REPORT 第一轮 |
| 修后：两类问题各一条投递，含编号与原文，不进用户输入 | PASS | T-216 主路径第七轮复跑与 main 复跑；来源用例 history、completion、provenance（Claude、Codex）；迟到钩子绿态 `late_system_not_user` 通过；never-sent 新期望三项通过 |
| 四家 CLI 都收到、各只实际提交一次；忙、权限框、问答框、草稿时不送；确认不了记未知、不重发 | PASS | 真实 Claude、本地 Codex、真实供应商 Codex（第七轮补跑）、真实 agy、opencode（第六轮，第七轮改动不经过它们）；送法矩阵、未知恢复、跨重启恢复第六轮全过，第七轮复跑 recover、recover-restart、unknown 通过 |
| 主控答复送达 worker、记为主控回答、显示“主控已答” | PASS | T-216 主路径、T-133 Codex |
| 交给用户：计入“等你决定”、显示理由；用户答复 `reply_to` 该问题 | PASS | T-216 主路径、T-132、T-133（第六轮）；T-216、T-133 第七轮复跑 |
| 反例：没有执行主控时排队不丢，15 分钟后计入“等你决定” | PASS | r2 routing-offline（第六轮）；门禁时钟依赖，没有实际等 15 分钟 |
| 角色卡与命令说明写明只交用户的类别 | PASS | `roles/executor.md`、`roles/worker.md`、a2a skill、`AGENTS.md` |
| 独立审查（GPT 只读，新开干净会话）无未处理的阻塞意见 | PASS | [ROUND7-REVIEW-01.md](ROUND7-REVIEW-01.md) PASS、无意见；主控逐条核对引用（[核对记录](ROUND7-REVIEW-01-controller-check.md)）。第六轮两份审查的 FAIL 都已在第七轮处理 |

## 第七轮的红态与变异

| 运行 | 结果 |
| --- | --- |
| `--quota-warning` 修前（本地 Responses 回 92% 周额度头） | 退出 1，收件超时；画面有选择框与 luna |
| `--quota-warning` 修后 | 退出 0；额度横幅 5 次，选择框 0 次 |
| 变异 `require-hc-return`（恢复第六轮条件），迟到钩子 | 退出 1，`late_system_not_user` 失败 |
| 变异 attach-only（Claude、Codex） | 退出 1，`history_user_recorded_twice` |
| T-133 变异 reply-as-message | 退出 1，`only_approved_prompts_recorded` |
| r2 duplicate-submit 反例 | 退出 1，`cli_actual_submission_count_is_one`，与第六轮相同 |

## 没做或没证明的

- 主控回答 worker 提问仍经旧的 node-pty 窗格，随受管窗格切到 hc 一起改（MAP 待切项）。
- worker 窗格里的用户输入还带按键记录，另开 T-229。
- 真实供应商 Codex 补跑那次没有出额度横幅，额度预警路径只由本地复现证明。
- 已接受代价那一种情形（意图后、RPC 前崩溃，用户再逐字提交同一段派发）没有专门的端到端用例，由 never-sent 用例的“意图只认领一次、第二次同文记用户”覆盖相邻行为。

## 证据归档（T-088）

| 清单 | 内容 |
| --- | --- |
| [archive/worker-evidence.archive.json](archive/worker-evidence.archive.json) | `a2a-worktrees/T-216-evidence`：七轮全部 JSON、日志、补丁、现场摘要 |
| [archive/fixtures.archive.json](archive/fixtures.archive.json) | `/private/tmp/t216-*` 测试现场 |

归档在 `/Volumes/WD-Elements/a2a-evidence/2026-10-31-batch29/T-216/`，每个来源的文件数、字节数与副本一致，核对后删除原件。仓库里只留各轮报告、审查、命令和本记录；报告里指向 JSON 和日志的相对链接，对应归档 `worker-evidence/T-216-evidence/` 下的同名文件。
