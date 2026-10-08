# T-037 主控审阅记录 01：异常边界抽查（2026-10-08，Claude Code）

对冻结候选 a493421 的异常处理做了只读抽查。

确认合理：`core.ts:530` 回收失败记入 run.cleanup_failure 且不改变原错误码；`cli.ts:111`、`core.ts:1031` 为 CLI/核心的统一出口；`httpRoute.ts:58`、`tools.ts:45` 只把请求解码失败映射为 400/`invalid_submit`（核心的 Promise 拒绝在 Effect.promise 中是 defect，不被 Effect.catch 吞掉）；`AgentGateway.ts` 为上游代码，本候选未改；`pagination_oracle.py` 为冻结 oracle 原文。

需要回答：`apps/server/src/a2a/orchestration.ts:75` 之后的常驻订阅。某条消息记录失败时，Stream 失败，`tapError` 只写日志，forkScoped 的观察 fiber 随之结束；此后受管 thread 中的人工输入不再被记录，而门禁与界面没有任何可见信号。请在交接说明中回答：
1. 这条失败路径能否由真实输入触达（例如 state 文件不可写、核心拒绝）；
2. 若能，记录停止后谁会知道；是否应当让失败进入门禁可见状态（例如服务启动失败或可查询的 observer 状态），而不是只写日志。
若判定为缺陷，按先红后绿处理并重新冻结；若判定不在本 ticket 范围，写明理由与影响，主控决定是否另开 ticket。
