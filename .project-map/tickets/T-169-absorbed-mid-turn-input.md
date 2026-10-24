---
id: T-169
title: T-166 残余：工作中输入被 CLI 并入当前回合后，后台仍等它成为单独回合，worker 停在等待、回执不送、回收被拒
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

来源：T-164 第二轮（`findings/2026-10-24-real-user-dogfood-rerun-2.md` N03，F01“仍在”）。执行主控事后只读核对归档实例（`evidence/2026-10-23-batch24/T-164/t164-dogfood-x339g6dx.archive.json`）与 Claude 原生转录（worker A，launch `c55be686-692e-4059-bf8e-031e1e66c9a1`）。属 T-166 已批准范围的缺陷级残余，执行主控按 T-004 自建；T-166 由执行主控本人写，本票修的是该修复的漏洞。

现场：A 修复回合里模型还有工具调用未完成时，用户输入一句话（08:20:15）。后台按 T-166 记 `claude_prompt_queued`（#674），预期它在原回合结束后成为单独的排队回合。Claude Code 2.1.310 实际把它并入当前回合：原生转录写 `queue-operation`（`operation: remove`，`reason: absorbed_mid_turn`）和 `queued_command` 附件，随下一个工具结果交给模型（“within the running turn … rather than as a separate conversation turn”），之后不会再有这句话的单独回合。原回合 Stop（#728）交付照常受理，但因排队列表非空，后台记 `pane_waiting_native_queue`、窗格保持忙；门禁回执 #8（#733）一直没有写入；之后人工输入的回合结束又停在同一状态（#771）。侧栏未知，应用内主控 revise 后 reclaim 报 `worker_working`。T-166 的端到端测试里输入发生在模型写最终回复时，CLI 把它排成单独回合，所以没有覆盖这条路径。

目标：原生转录记录该输入已被并入当前回合（`absorbed_mid_turn`，同会话、同正文、不早于收到时间）时，该输入不再等待单独回合，并记录这一事实；原回合 Stop 后照常回到空闲并送出待送的门禁回执。仍成为单独回合的输入按 T-166/T-165 不变。门禁核对不放松，不靠超时或猜测清掉排队。

## Acceptance

- [x] 红态：当前 main 上，用真实 daemon/PTY/Claude CLI/Electron（脚本化 Messages）在模型还有工具调用时输入，复现 Stop 后 `pane_waiting_native_queue`、不回空闲、门禁回执不写入。
- [x] 绿态：同一序列下原回合交付受理，输入原样进入 CLI 的下一次模型请求并记人工介入，worker 回到空闲，回执写入一次。
- [x] 反例：T-166 的单独排队回合场景、无 Enter 的复用拒绝、T-157、T-165 场景不变；去掉“并入”判定的坏实现在新场景失败。

## 不做

不按超时清队列；不改 CLI 的并入行为；范围外的问题经问题上报。

## Resolution

2026-10-24 关闭，PASS。写入者为执行主控本人（T-166 残余，按 T-004 自建；用户授权转述见构思主控 answer 20261024T070244Z-ideation-answer-001）。根因：模型还有工具调用时的用户输入被 Claude Code 2.1.310 并入当前回合（原生转录 `queue-operation` remove、`absorbed_mid_turn`），T-166 仍等它成为单独回合，Stop 后停在 `pane_waiting_native_queue`。修复：`workbench/src/panes.ts` 在原回合 Stop 转交后，按同会话、同正文、不早于收到时间、只用一次的并入记录移出等待并记 `claude_prompt_absorbed`；没有并入记录的照旧。不按超时清队列。README 同步。
证据（真实 Electron/后台/PTY/Claude CLI，脚本化 Messages，厂商模型回合 0）：修前红态 2/2 与 T-164 第二轮一致；绿态 2/2；T-166 原场景 PASS；Stop 时清空队列的坏实现在原场景失败；T-157、T-165、T-166 主机级回归 PASS。独立审查 agy PASS（一条 P3：混合序列未单独构造）。合并 e3b14d27b；合并后整批回归 52/52（`evidence/2026-10-23-batch24/merge-wave/README.md`）。未用真实模型复验，留待下一轮 T-164。证据 `evidence/2026-10-23-batch24/T-169/RESULTS.md`。
