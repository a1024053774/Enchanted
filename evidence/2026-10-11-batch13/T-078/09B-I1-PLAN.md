# 09B I1 离线协议与下一步材料

I1 只验证 ideation 的第一条 `/v1/messages` 协议：请求正文绑定本次登记的 dispatch.text、dispatch.seq、dispatch/request/stop ID 与 attempt/session/fence；假 API 返回固定 SSE `message_start → content_block_delta(I1_ACK) → message_delta → message_stop`。离线驱动不启动 socket、API、CLI、daemon、target 或模型。

预算按已批准 I 角色上限 4 roots / 6 Messages：本 I1 根使用 1、Messages 使用 1，剩余预算留给 I2～I4。反例逐项拒绝：正文改写、global dispatch.seq 重置、request_id 改写、role 越权、超过 Messages 上限；每个变异保留独立结果。executor 角色不在本轮启动。

待批材料绑定真实 B1 ideation session/launch 与 A-05 target attempt；真实 I1 执行前需主控逐项批准 action、Messages 数、stop/request ID 登记和 fake API 应答，再另取真实请求原件。当前 launch `NO_GO`。
