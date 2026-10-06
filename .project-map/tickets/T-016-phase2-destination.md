---
id: T-016
title: 第二阶段目的地与 M1
type: decide
status: closed
blocked_by: []
claimed_by:
supersedes:
---

## Question

把 a2a 的下一阶段定成什么，第一个里程碑做到什么算完成？

## Resolution

2026-10-06 grilling 确认（[ledger](../../.grilling/a2a-gui-client.md) 的 D0、D1、D10、D12）。

目的地是 a2a 多 Agent 工作台：自建的类 Herdr GPUI 应用，agent 仍以各自的 CLI 运行在终端 pane 中；每个项目一个窗口，任务是项目窗口里的标签页，一个任务里有多个 pane 供 agent 分工。

M1：工作台完全接替 Herdr，承担 a2a 的日常工作。包括引擎在后台持久运行并能恢复窗口；项目窗口、任务页、pane 与四种状态；Codex 与 Claude Code 端到端实测；`coop.py` 改接工作台，三套验收与一次真实 `run` 通过；Codex、Synara 式外观，窗口级玻璃质感和可选强调色。M1 只面向 macOS。完整内容见 [intent.md](../../intent.md)。

被否决：评估中提议的"GPUI 作为已安装 Herdr 的客户端"，以及"以对话投影为主"的形态。
