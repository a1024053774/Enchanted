---
id: T-166
title: F01 残余：普通工作回合中用户输入，UPS 复用原 prompt_id 被判重复，原 Stop 被拒
type: build
status: open
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

- [ ] 红态：当前 main 上，用真实 daemon/PTY/Claude CLI/Electron（脚本化 Messages）在普通工具执行期输入，复现 `claude_prompt_id_reused` → `current_turn_untrusted` → 停在未知。
- [ ] 绿态：同一序列下原回合交付被门禁接受、worker 回到空闲；输入原样送达 CLI 并记人工介入；输入引起的新回合完成后回到空闲。
- [ ] 反例：没有对应用户输入的 prompt_id 复用仍判不可信；T-157、T-165 全部场景与 T-159/T-160/T-133 回归通过。

## 不做

范围外的问题经问题上报，不顺手改。
