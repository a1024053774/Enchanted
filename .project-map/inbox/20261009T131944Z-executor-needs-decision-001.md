---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: ["ticket:T-056"]
created_at: "2026-10-09T13:19:44.258689Z"
schema: 1
title: "T-056 命令来源字段（契约变更）与退出恢复路径"
id: "20261009T131944Z-executor-needs-decision-001"
---

# T-056 需要决定：命令来源字段（契约变更）与退出恢复路径

**问题**：T-056 要把界面里"用户明确操作"与"界面自动派生"的命令分开记录（spec 第 3 节：后者 `channel: ui-derived`，不算用户决定）。worker 用真实 UI 表达式与真实 codec 证明：用户点停止/中断（`ChatView.tsx:3133/3564`）与退出时的批量中断、临时线程清理（`RunningChatsQuitCoordinator.tsx:62`、`useTemporaryThreadLifecycle.ts:100`）发出的 RPC 字段完全相同（type、commandId、threadId、createdAt），无法区分。另外退出时勾选"Resume chats automatically"走 `orchestration.prepareQuitResume`（`wsRpc.ts:1424`），绕过已批准的 `dispatchCommand` 入口。证据：evidence/2026-10-09-batch11/T-056/needs-decision-02.md、origin-probe-02.json、bypass-source-02.json、red-matrix-02/。

**选项**：
- A（推荐）：给相关客户端命令加一个可选来源字段（例如 `origin: "ui-derived"`），只由这几个自动派生点设置；缺省视为用户明确操作，旧客户端行为不变。同时在 `wsRpc.ts` 的 `prepareQuitResume` 入口也接一次记录（标 ui-derived）。涉及上游文件：contracts 的命令 schema、上述两个 web 调用点、`wsRpc.ts` 再加一处挂接。属于契约扩展，按"通用修复"整理便于回馈上游。
- B：挂起 T-056，先开前置 ticket 只做来源字段与绕过路径，再恢复 T-056。
- C：缩小验收，暂不区分自动派生（把所有停止/中断都记成用户 action 或都记 ui-derived）——属于验收变更，代价是记录失真。

**最小选择**：A，并在 T-056 升 ready_rev 时写明允许改动的上游文件清单。

**当前处置**：T-056 暂停（父修订红态已保留，产品代码未改）；先派与之不冲突的 T-057。
