# Protocol I1 待批材料

I1 输入是已批准的 test-simulated-user 窗口 stop 请求：自动化经产品窗口入口记录 action，明确标注为执行主控批准的模拟用户动作，不冒称真人。假 API 按登记的真实 dispatch/request/stop/inbox ID 下发一次 Anthropic `tool_use`，命令来自冻结 `protocol.commands.I_SEND_STOP`；实际 ID 在门禁/收件箱登记后填入，不写死序号。共享 `t078_09b_protocol_core.py` 严格核对工具历史、工具 ID、完整 argv 和实际 `tool_result`；tool_result 作为第二条 Messages 结算，真实 Stop 转交后唤醒 executor。

离线 shared-core 证据在 `api-green.json`：I1 首条 SSE 是 6 个 Anthropic tool-use 事件，第二条 SSE 是 6 个结算事件；I2 是一条 confirm-only Messages。E1 由真实 wrong-target 工具命令产生门禁 `worker_target_required`（409），随后 API 只接受该登记的中性拒绝结果作为第二条结算，不编造业务错误。`api-red-*.json` 覆盖工具 ID、工具结果 entry、target、seq、role 和正文变异，均拒绝；未启动 socket/API/CLI/daemon/target/model。

本次预算：ideation 已用 A-10 管道回合 1 root/1 Messages；计入 4 roots/6 Messages。Protocol I1 另用 1 root/2 Messages，累计 2 roots/3 Messages，仍在上限内，不需要 A-11 重建。预期 PermissionRequest 1 次，一次性 Yes；读屏确认 command 原文后按 Enter。

停止条件：一条 test-simulated-user stop action、一次 `I_SEND_STOP` tool_use、一次 tool_result、两条 Messages、一个真实 Stop/relay 唤醒 executor；不执行 I2/E 阶段，不重试，不由 operator 代发 send/stop/ack。
