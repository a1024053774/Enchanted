# 09B A-11 协议预算与启动顺序

本包把 A-10 的 1 root/1 Messages 管道回合留作独立证据，不计入 09B 协议预算。A-11 按冻结 `09b-materials-01/protocol.json` 使用 ideation 4 roots/6 Messages、executor 6 roots/11 Messages；供应商模型回合为 0。

| 阶段 | 角色 | roots | Messages | 预期 PermissionRequest/一次性 Yes | 作用与停止条件 |
| --- | --- | ---: | ---: | ---: | --- |
| I1 | ideation | 1 | 2 | 1 | `I_SEND_STOP` tool_use；读屏核对完整 Bash 命令后按一次 Yes；tool_result 结算，实际 Stop/relay 唤醒 executor |
| I2 | ideation | 1 | 1 | 0 | 实际 send 执行反馈，只确认，不再发工具 |
| I3 | ideation | 1 | 2 | 1 | `I_FOREIGN_ACK`；实际 recipient_required 拒绝，无新 ack/wake |
| I4 | ideation | 1 | 1 | 0 | 确认拒绝并 idle |
| E1 | executor | 1 | 2 | 1 | `E_WRONG_TARGET`；读屏核对错误 target 命令后一次 Yes，真实 worker_target_required 拒绝 |
| E2 | executor | 1 | 2 | 1 | `E_STOP`；一次受管目标 Esc |
| E3 | executor | 1 | 2 | 1 | `E_ACK`；实际 ack 并唤醒 ideation |
| E4 | executor | 1 | 2 | 1 | `E_DUP_ACK`；同一 ack 幂等，不二次唤醒 |
| E5 | executor | 1 | 2 | 1 | `E_STOP_ACKED`；已 ack stop 拒绝，不再 Esc |
| E6 | executor | 1 | 1 | 0 | 最终确认并 idle |

角色启动严格串行：先启动 ideation B1，逐屏完成主题、安全说明、信任和 readiness 后才执行 I1/I2；I1 的真实 Stop/relay wake 已读回后，才启动 executor B1。executor B1 的每个启动步骤与 ideation 的每个后续阶段都单独批准，同一时刻只启动一个角色的一个步骤；ideation 会话保持存活但不与 executor 并发启动。I3/I4 在 E3/E4 的实际 ack/wake 读回后执行，E5/E6 在 E4 幂等结果读回后执行。

本表是静态计划，A-11 尚未启动、未发送、未产生真实阶段结果；每个阶段必须以实际 dispatch/request/inbox/relay ID 和目标 `received.bin` 独立读回判定。
