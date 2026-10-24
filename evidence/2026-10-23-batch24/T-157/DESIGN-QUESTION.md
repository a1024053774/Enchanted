# T-157-1 / a1：Stop 批次与人工介入的交付语义

语义已裁定（主控 #61，2026-10-24）；实现与完整验收 INCOMPLETE。红态复现 PASS，证据见 RED-01.json 及截图。下面保留当时问题与未采纳选项。

## 裁定

主控 #61 转述构思主控 answer `20261024T030734Z-001`，用户逐字：“我在 agent 工作过程中输入内容这个他自己 cli 会处理的吧,他会在此次工具执行完成后加入这句话再做思考,这个不用我们处理吧”。用户未选下面的 1 或 2。

执行约束：输入原样直达 CLI，不拦、不延后、不改写时机或语义，只记人工介入。Enter 不得清空或替换仍有效的 turn 身份；正在进行的 Stop 批次按原 turn 核对同 attempt 的 submit，门禁的 turn/attempt/版本检查不放松。只有真实原生新 turn 已开始、旧 turn 不再当前时才明确拒绝，界面显示最后事实与原因并给最小恢复入口；不做常规的“暂停后点重新交付”，不自动重试。

实现边界：先改 panes.ts/gates；renderer.tsx 等 T-159 合并后由执行主控通知 rebase 到合并后的 main，再开始写入。沙箱外运行交 RUN-OUTSIDE-02。

此前按任务卡要求先写问题并停止；候选选项没有当作已授权验收条件。上述用户原则取代两项候选，下面的基线调查与问题为日期记录。

## 已知事实与推断

- observed：T-155 在产品 `f3412fb4ae5cfa3c4983440eb26ea8c5b34b0697` 观察到输入后的“未知/忙”和无恢复入口；停止后的摘要记录同一 attempt 的 submit 被 `worker_not_active` 拒绝。来源：`findings/2026-10-23-real-user-dogfood.md` F01；`evidence/2026-10-23-batch24/T-155/stopped-readback.json` orchestration event 860、gate event 299。
- observed（源码，调查基线 `ef99842b35e17c4cd69e1e58d5afca0689bf88b1`）：`workbench/src/panes.ts:1168` 的人工 Enter 清空 `claudePromptId` 并替换 `active`。`panes.ts:1520` 的 Stop 转交包含 await；`panes.ts:1690` 的 worker `assertActive` 在异步进程核对后要求 prompt_id 仍相同。
- inferred：人工 Enter 落在旧 Stop 的异步核对之间时，旧请求可能得到 `worker_not_active`。拒绝可能发生在 `daemon.ts:801` 的转交前检查，也可能发生在 `gates/core.ts:3997` 或 `4055` 的 submit 核对；不能仅凭旧摘要确定是哪一次。
- observed（源码）：`workbench/src/relay.ts` 把请求和明确结果追加持久化；相同 request_id 只读回原结果，结果缺失才是 `relay_outcome_unknown`。因此不能把明确拒绝与结果未知混称，也不能用同 request_id 重放来恢复。
- observed（源码）：`sidebar.ts` 派生 agent 状态，renderer 的窗格头直接显示 `pane.state`；窗格没有展示交付拒绝的结构化字段或交付恢复动作。
- measured：执行主控按 `RUN-OUTSIDE-01.sh` 在基线 `ef99842b35e17c4cd69e1e58d5afca0689bf88b1` 运行真实 Electron 探针。RED-01.json 记录 Stop seq 93、submit relay_received seq 95、人工提交 seq 99、worker_not_active seq 104、after_transfer 的 stop_not_matched seq 106。人工介入绑定原 attempt，任务仍无候选，侧栏 unknown / 窗格头“忙”；两个界面期望断言失败，red_reproduced=true，errors=[]。测试退出 1，证明修前缺陷，未证明修复。
- unknown：拒绝调用栈未采集，尚不确定是哪一次身份核对；新证据不替代下面的语义裁定。真实供应商模型回合为 0，使用本地脚本化 Messages 接口；无真实模型理解或可靠性结论。

## 当时提出的最小选项（均未采纳）

1. **Stop 批次先处理完**：已经匹配的 Stop 批次继续按原 turn/attempt 做首次门禁处理；新输入先记为人工介入，实际提交顺序排在该批次之后。所有原有门禁检查保留；这不是失败请求自动重试。需要确认是否允许用户输入的提交等待旧批次处理。
2. **交付暂停后重新确认**：新输入的提交使未完成的旧交付暂停；保留旧请求、提交号、明确拒绝/未知结果和原 attempt 绑定。恢复入口让原 worker 在原 attempt 下核对当前合同、代码版本及人工介入后，发出新的显式 submit；不替 worker 直接提交，不复用旧 request_id。

两种方案都不能把明确拒绝的旧请求改写成成功；处理历史拒绝是否统一采用选项 2 的显式确认，也需要裁定。恢复时原 attempt 已失效、合同版本变化、结果未知等情况仍须拒绝或交给现有中断恢复流程，不能接管 current_attempt。

## renderer 协调

尚未修改 `workbench/app/renderer.tsx`。后续预计只涉及：顶部 Snapshot/AgentItem 的事实类型、SessionPane 的状态徽标与最后事实/原因/恢复入口、renderAgents 的原因说明。具体动作随上述裁定确定；必须等执行主控回复，避开 T-159 的写入。

若裁定需要新增 Electron IPC、preload 或公开命令，当前任务卡未授权这些文件；届时先报最小扩边，不从 renderer 绕过门禁。

## 下一步与责任

执行主控已运行 RUN-OUTSIDE-01，主控 #58 回传红态；主控 #61 已转述用户新原则。worker 依此修根因，RUN-OUTSIDE-02 用同一竞态验证原 submit 通过、原样输入、人工介入与原 attempt 绑定；隔离身份测试覆盖原生新 turn 拒绝旧 caller。真实 Electron 的新 turn 反例与界面验证还未完成，等待 renderer 写入窗口后接续。
