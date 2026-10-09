---
from: "worker:s11-t056"
to: "executor"
kind: "needs-decision"
reply_to: ""
refs: ["ticket:T-056", "file:evidence/2026-10-09-batch11/T-056/needs-decision-02.md"]
created_at: "2026-10-09T13:16:29.092116Z"
schema: 1
title: "T-056 来源探针触发新停止条件，父修订红态已保留"
id: "20261009T131629Z-worker:s11-t056-needs-decision-001"
---

# T-056：来源字段不足，退出恢复路径绕过观测入口

状态：**BLOCKED**。已遵照决定 01 跑父修订红态，并执行所要求的窄来源探针。fork 仍为 `a2a@2330534b2cf906b9d8f0a0b643adb370683d7fe0`，产品代码未改，未 submit。上一轮目录外接入问题已解决，本次是新的来源与观测范围问题。

## 事实与证据

真实隔离服务经唯一 HTTP 门禁建立 worker、reviewer attach、controller attach；普通 thread 经真实 engine 建立。全部 10 个用户 RPC 经 WS `orchestration.dispatchCommand` 接受，且都有域事件。受管 worker 消息已有 1 条记录；attach、普通、controller 的消息，异步答复、结构化答复、批准、拒绝、停止、中断这 9 项都无记录。合同用例按预期退出 1：[summary](red-matrix-02/summary.json)、[域事件](red-matrix-02/domain-events.json)、[用户输入](red-matrix-02/user-inputs.json)。这是父修订覆盖缺项红态，不是候选通过结论。

来源窄探针执行真实 UI 传给 `dispatchCommand` 的对象表达式，并使用真实 `ClientOrchestrationCommand` codec 解码。只固定 UUID、时间、同一目标 thread，两组 RPC 输入完全相同：[origin-probe-02.json](origin-probe-02.json)。实际随机 UUID 和时间不携带来源信息，两条路径可以针对相同 thread/session/project 状态，不能靠状态或内容猜来源。

| 用户明确操作 | 界面自动派生 | 共同字段 |
| --- | --- | --- |
| `ChatView.tsx:3564`，用户中断 | `RunningChatsQuitCoordinator.tsx:62`，退出时的批量中断 | type、commandId、threadId、createdAt |
| `ChatView.tsx:3133`，用户停止会话 | `useTemporaryThreadLifecycle.ts:100`，临时线程清理 | type、commandId、threadId、createdAt |

另外，退出时勾选“Resume chats automatically”，`RunningChatsQuitCoordinator.tsx:78` 调用的是 `orchestration.prepareQuitResume`。成功分支不会再由界面发 interrupt；`wsRpc.ts:1424` 把它送入 `prepareQuitResume`，经服务端 `dispatchOrchestrationCommand` 直接派发中断。它**绕过 `dispatchCommand` RPC handler**，当前批准的单点接入抓不到。原始片段与 exact argv 在 [bypass-source-02.json](bypass-source-02.json)。这是源码核对，未声称真实桌面退出验收。

## 为什么必须停

ticket/spec 第 3 节要求自动派生命令记录为 `channel: ui-derived`，并明确规定发现界面绕过该入口就停下发 needs-decision。决定 01 也要求：“若窄探针证明现有字段不足以区分且需要改契约或加字段，再停下上报，不自行添加 origin 字段。”

仅在批准的 `wsRpc.ts` import 与 `dispatchCommand` 入口调用，无法凭现有字段区分两组来源，也无法覆盖 `prepareQuitResume` 入口。把它们全部记成用户 action 会违反反例；把全部中断或停止标 ui-derived 又会丢失用户明确操作。没有实施这些绕过。

## 最小决定选项

- 按 spec 预留方向，批准为相关命令加入明确来源字段，并在自动派发点传来源；同时明确 `prepareQuitResume` 的输入记录接入。需要执行主控给出范围与语义，必要时交构思主控确认；worker 不自行扩写合同。
- 若保持现有批准范围，则挂起本票，先由前置 ticket 补齐权威来源和绕过路径，再继续 T-056。若减少本票反例或覆盖条件，属于验收变更，须用户决定。

请决定所选方向及必要的上游文件范围。不请求操作正式数据或重启正式工作台。

## 红态与保留边界

provider 全部禁用，真实模型 turn 为 0。异步问题由真实 internal command 建立，结构化/审批请求使用隔离哨兵；本次证明 RPC 接受且父修订没记录，**不证明原生 provider 产生或接收这些交互**。原始命令、回执、域事件、SQLite 与 Git 夹具保留。[setup-failures-02.txt](setup-failures-02.txt) 是脚本准备失败，不计作合同红态。

只核对并停止本次创建的 PID 86814；正式工作台、用户 Herdr、用户配置、dist、依赖未动。现场归档为 [retained-red-matrix-02.tar.gz](retained-red-matrix-02.tar.gz)，无 auth.json；外置盘原目录保留，[cleanup-02.json](cleanup-02.json) 保存身份与退出核对。

重放使用新 label，避免覆盖现场：先 `python3 evidence/2026-10-09-batch11/T-056/start-server-02.py red-replay-03`，再 `python3 evidence/2026-10-09-batch11/T-056/red-matrix-02.py red-replay-03`，预期后者退出 1。完成后只对 launch 记录的 PID 核对身份再停止。来源探针：在 fork 执行 `A2A_SYNARA_SLOT=t056-origin-replay-03 ./a2a/scripts/bun run /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch11/T-056/origin-probe-02.ts origin-replay-03`，预期退出 1、两组 identicalRPC 为 true。
