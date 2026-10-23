---
id: T-151
title: 迁移 test_t078_claude_signals.ts 到现行契约（Claude 信号去重）
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

来源：用户 2026-10-23 在构思主控 session（Claude 62cb7357，pane wG:p1）的选择题里逐字选“C 先迁守护安全边界的 4 个 (Recommended)”，构思主控转达见 `.project-map/inbox/20261023T185657Z-ideation-answer-001.md`（授权：把 4 个文件的过时断言改到现行契约、保留有效检查；这是对修改这些受保护验收文件的授权；每个迁移须在现行代码上取得红态与绿态）。

对象：`workbench/tests/test_t078_claude_signals.ts`。过时：夹具缺少现在非 controller 角色要读取的 transcript/模型事实（ENOENT），以及据此的旧期望。保留：已登记 active submission 的 UserPromptSubmit/Stop 关联、重复 Stop 不重复产生 pane_idle、异会话拒收。

T-149 的调查见 `evidence/2026-10-23-batch23/T-149/DISPOSITION.md`（本文件一行），索引 `workbench/tests/HISTORICAL.md`。

## Acceptance

- [x] 过时断言逐条改到现行契约（依据现行规格/ticket/产品代码，写出来源），仍有效的检查全部保留，不删检查来换绿。
- [x] 在当前 main 上绿态通过。
- [x] 红态：至少一个已知坏实现或变异被抓住，且落在保留的有效检查上（不能只靠被改的断言）。
- [x] 改动逐条写入 RESULTS（原断言、新断言、依据）。

## 不做

不改产品代码；不为迎合测试改产品；不碰其他测试；不改 `workbench/tests/HISTORICAL.md`（由 T-154 统一更新）。

## Resolution

2026-10-23 关闭，PASS。

- 迁移 `workbench/tests/test_t078_claude_signals.ts`（候选 `9de85967a`，合并 `b058e3a75`）：原 7 条断言全部保留；过时的是夹具（缺非 controller 角色在 Stop 时要读的 transcript/模型事实），按现行 `panes.ts` 的 `claudeTurnFacts` 前提补合成 transcript 与 Stop effort，另加 prompt id 与 pane_idle.submission 绑定两条断言。
- 红绿态：绿态 exit 0；`duplicate-stop-idle` 变异 exit 1，失败于保留的“重复 Stop 不重复 pane_idle”（2 !== 1）。执行主控复跑一致。领域状态测试，不证明真实 CLI hook 格式。
- 独立审查 agy PASS，无发现（首次报告缺结论行，同会话追问得到 PASS）。合并后回归 09 PASS。
