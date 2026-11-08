# T-255 现场记录（2026-11-08）

命令：`a2a call '{"command":"run","task":"a2a+T-249-1","runtimeMode":"workspace-write","wait_seconds":28800,"model":"gpt-6-astra","effort":"xhigh"}'`

回执摘要：`ok: False`，`error: operation_busy`，run `0a9e5100-ca49-4446-ab5f-a26b5bef3d61`，attempt `6bab2eb9-0d63-4bb1-b325-f70fa6df2d2b`，`phase: verifying`，`outcome: paused`，开始 2026-11-08T08:50:02.288Z，结束 2026-11-08T09:06:41.377Z。

事件顺序（`orchestration_events`，同一 launch `f36d7d22-41a2-4819-ba48-36ebda96a99a`）：

- 09:06:40.885Z `relay_received`、09:06:41.230Z `relay_processed`：请求 `91e8efd2-…`（submit）
- 09:06:41.230Z `relay_received`、09:06:41.672Z `relay_processed`：请求 `e8151221-…`（issue #3）
- 09:06:41.377Z：run 以 `operation_busy` 结束

之后主控手动 `verify`：`ok: true`，09:07:37Z 机械验收通过，任务进入 `reviewing`。这只说明门禁本身没坏，缺陷还在。
