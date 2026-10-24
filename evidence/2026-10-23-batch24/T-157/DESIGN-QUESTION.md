# T-157-1 / a1：Stop 批次与人工介入的交付语义

NEEDS-DECISION / BLOCKED（仅交付语义与实现；红态复现 PASS，证据见 RED-01.json 及截图）。

本任务卡明确要求：“交付语义（人工介入后交付是否仍有效、恢复入口做什么）若需选择，先写 DESIGN-QUESTION.md 列证据与最小选项，停下说 NEEDS-DECISION，不自己定。”此处需要执行主控经构思主控裁定，不能把候选方案当作已授权验收条件。

## 已知事实与推断

- observed：T-155 在产品 `f3412fb4ae5cfa3c4983440eb26ea8c5b34b0697` 观察到输入后的“未知/忙”和无恢复入口；停止后的摘要记录同一 attempt 的 submit 被 `worker_not_active` 拒绝。来源：`findings/2026-10-23-real-user-dogfood.md` F01；`evidence/2026-10-23-batch24/T-155/stopped-readback.json` orchestration event 860、gate event 299。
- observed（源码，调查基线 `ef99842b35e17c4cd69e1e58d5afca0689bf88b1`）：`workbench/src/panes.ts:1168` 的人工 Enter 清空 `claudePromptId` 并替换 `active`。`panes.ts:1520` 的 Stop 转交包含 await；`panes.ts:1690` 的 worker `assertActive` 在异步进程核对后要求 prompt_id 仍相同。
- inferred：人工 Enter 落在旧 Stop 的异步核对之间时，旧请求可能得到 `worker_not_active`。拒绝可能发生在 `daemon.ts:801` 的转交前检查，也可能发生在 `gates/core.ts:3997` 或 `4055` 的 submit 核对；不能仅凭旧摘要确定是哪一次。
- observed（源码）：`workbench/src/relay.ts` 把请求和明确结果追加持久化；相同 request_id 只读回原结果，结果缺失才是 `relay_outcome_unknown`。因此不能把明确拒绝与结果未知混称，也不能用同 request_id 重放来恢复。
- observed（源码）：`sidebar.ts` 派生 agent 状态，renderer 的窗格头直接显示 `pane.state`；窗格没有展示交付拒绝的结构化字段或交付恢复动作。
- measured：执行主控按 `RUN-OUTSIDE-01.sh` 在基线 `ef99842b35e17c4cd69e1e58d5afca0689bf88b1` 运行真实 Electron 探针。RED-01.json 记录 Stop seq 93、submit relay_received seq 95、人工提交 seq 99、worker_not_active seq 104、after_transfer 的 stop_not_matched seq 106。人工介入绑定原 attempt，任务仍无候选，侧栏 unknown / 窗格头“忙”；两个界面期望断言失败，red_reproduced=true，errors=[]。测试退出 1，证明修前缺陷，未证明修复。
- unknown：拒绝调用栈未采集，尚不确定是哪一次身份核对；新证据不替代下面的语义裁定。真实供应商模型回合为 0，使用本地脚本化 Messages 接口；无真实模型理解或可靠性结论。

## 需要裁定的最小选项

1. **Stop 批次先处理完**：已经匹配的 Stop 批次继续按原 turn/attempt 做首次门禁处理；新输入先记为人工介入，实际提交顺序排在该批次之后。所有原有门禁检查保留；这不是失败请求自动重试。需要确认是否允许用户输入的提交等待旧批次处理。
2. **交付暂停后重新确认**：新输入的提交使未完成的旧交付暂停；保留旧请求、提交号、明确拒绝/未知结果和原 attempt 绑定。恢复入口让原 worker 在原 attempt 下核对当前合同、代码版本及人工介入后，发出新的显式 submit；不替 worker 直接提交，不复用旧 request_id。

两种方案都不能把明确拒绝的旧请求改写成成功；处理历史拒绝是否统一采用选项 2 的显式确认，也需要裁定。恢复时原 attempt 已失效、合同版本变化、结果未知等情况仍须拒绝或交给现有中断恢复流程，不能接管 current_attempt。

## renderer 协调

尚未修改 `workbench/app/renderer.tsx`。后续预计只涉及：顶部 Snapshot/AgentItem 的事实类型、SessionPane 的状态徽标与最后事实/原因/恢复入口、renderAgents 的原因说明。具体动作随上述裁定确定；必须等执行主控回复，避开 T-159 的写入。

若裁定需要新增 Electron IPC、preload 或公开命令，当前任务卡未授权这些文件；届时先报最小扩边，不从 renderer 绕过门禁。

## 下一步与责任

执行主控已运行 RUN-OUTSIDE-01，主控 #58 回传 summary、截图及 fixture 路径，worker 已复制核对并保留证据。该消息同时确认已转构思主控（needs-decision `20261024T025739Z`，执行主控推荐选项 2），但尚未给出裁定或 renderer 写入窗口。等待交付顺序、恢复动作的决定及写入窗口；当前不实施任何一个方案。
