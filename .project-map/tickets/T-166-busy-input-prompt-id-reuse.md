---
id: T-166
title: F01 残余：普通工作回合中用户输入，UPS 复用原 prompt_id 被判重复，原 Stop 被拒
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

来源：T-164 真实使用重跑（`findings/2026-10-24-real-user-dogfood-rerun.md` F01 复验“仍在”），执行主控事后只读核对实例 `/private/tmp/t164-dogfood-xn9_oslt` 的 orchestration_events（launch `5b38f79e-ac64-4cad-89de-f6308daa099a`，Haiku worker A）。属 T-157 已批准范围（F01 blocker；用户原则“我在 agent 工作过程中输入内容这个他自己 cli 会处理的吧……这个不用我们处理吧”）的缺陷级残余，执行主控按 T-004 自建。

现场：A 第一回合运行中（工具执行期，**不是** Stop 交付批次），用户在窗格粘贴一句话并回车（seq 280～286，06:26:12）。CLI 随即发来的 UserPromptSubmit 仍带运行中回合的 prompt_id，被记 `native_question_unverified`（`claude_prompt_id_reused`，seq 290），当前回合因此不可信；1 秒后该回合真实的 Stop 被拒（`current_turn_untrusted`，seq 295），随后 `stop_not_matched`。worker 停在侧栏“未知”、窗格“忙”，候选已提交但门禁未接受交付。T-157/T-165 只处理了 Stop 批次期间的排队输入，普通工作回合中的输入仍走旧的“prompt_id 复用即不可信”路径。

目标：普通工作回合中用户输入时，复用原 prompt_id 的 UPS 按排队输入处理（与 T-157 同一语义：记录排队事实与人工介入，保留原身份），不让原回合变得不可信；原回合的 Stop 照常匹配并完成交付；CLI 随后处理这句输入的新回合由原生转录登记（含 T-165 的早到 Stop 暂存）。门禁核对不放松；真正伪造或无对应输入的 prompt_id 复用仍拒绝。

## Acceptance

- [x] 红态：当前 main 上，用真实 daemon/PTY/Claude CLI/Electron（脚本化 Messages）在普通工具执行期输入，复现 `claude_prompt_id_reused` → `current_turn_untrusted` → 停在未知。
- [x] 绿态：同一序列下原回合交付被门禁接受、worker 回到空闲；输入原样送达 CLI 并记人工介入；输入引起的新回合完成后回到空闲。
- [x] 反例：没有对应用户输入的 prompt_id 复用仍判不可信；T-157、T-165 全部场景与 T-159/T-160/T-133 回归通过。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-24 关闭，PASS。写入者为执行主控本人（构思主控 answer 20261024T070244Z-ideation-answer-001 转述用户决定）。根因：用户输入发生在原回合仍在工作时（早于其 Stop），CLI 以运行中回合的 prompt_id 发 UserPromptSubmit；T-157 只在 `stopInProgress` 时把这种复用记为排队输入，工作中的复用被判 `claude_prompt_id_reused`，回合不可信，原 Stop 随后以 `current_turn_untrusted` 被拒。修复在 `workbench/src/panes.ts`：排队输入分支去掉 `stopInProgress` 条件（仍要求当前回合、同 prompt_id、此前有该窗格真实写入的 Enter、转录一致）；`scan()` 在原回合未结束时不登记排队回合。README 同步。门禁核对未放松。
证据（0 个真实模型回合，真实 Electron/后台/PTY/Claude CLI）：修前红态 2/2 与 T-164 事件序列一致；绿态 3/3；主机级反例（无 Enter 的复用仍拒）与两个坏实现各自只在对应场景失败；回归 14 项符合预期。独立审查 agy PASS（两条 P3 观察，无需改动）。合并 b7d57b40f；合并后 T-166 端到端与主机级、T-157 stop-input、T-165 ordered 4/4 PASS。证据 `evidence/2026-10-23-batch24/T-166/RESULTS.md`。
