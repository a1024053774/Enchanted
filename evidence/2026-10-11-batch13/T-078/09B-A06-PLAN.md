# A-06 完整协议材料计划

A-06 重新创建 root、daemon、target claim 和最终 protocol fake API，再重跑 B1 reuse/label/逐键路径。A-05 五进程、清理归档和 B1 历史原样保留，不迁移 attempt/session/fence/PID。

最终 fake API 在阶段 A 就登记并实现 I1～I4/E1～E6 的 `/v1/messages` SSE 应答：每条请求核对实际 registered dispatch.text、全局 dispatch.seq、request/stop ID、role、attempt/session/fence；响应为 message_start、content delta、message_stop。I 预算 4 roots/6 Messages，E 预算 6 roots/11 Messages；离线完整 protocol green 与 seq/text/identity/role 反例已通过，real launch NO_GO。

A-06 approval 只允许逐屏启动到第一屏，再按已验证 key helper 单键批准；I1～I4/E1～E6 每阶段另签，任何额外 API 请求、409、身份漂移或预算超限停并保留现场。
