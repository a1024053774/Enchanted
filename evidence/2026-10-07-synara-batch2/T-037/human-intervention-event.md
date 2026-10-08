# 人工介入事件（T-037，2026-10-07）

公共 `events` 入口返回的事件类型为 `human_intervention`。沿用既有顶层 `seq`、`time`、`task`、`attempt`、`type`、`details`；不删除或改名 T-036 的字段。

`details` 字段：`task_id`、`attempt_id`、`session_id`、`fence`、`spec_rev`、`thread_id`、`turn_id`（可为 null）、`message_id`、`event_id`（Synara 原始事件 ID）、`source_sequence`（Synara 原始序号）、`created_at`、`dispatch_origin: "user"`、`text`。

只有服务端 `thread.message-sent` 中 `role === "user"` 且可信 `dispatchOrigin === "user"` 的消息进入记录。agent、automation、assistant 消息与非受管 thread 不产生事件。记录绑定该 thread 所属的原 attempt（包括历史 attempt），不借 current_attempt 重新归属。相同 event_id 回放不重复写入，原始门禁事件前缀保留；人工输入本身不提交候选或改变验收状态。

接入订阅和回放放在新增的 `apps/server/src/a2a/orchestration.ts`，事件写入由核心完成。这里只确定接口形状；行为通过记录另见最终 RESULTS.md。
