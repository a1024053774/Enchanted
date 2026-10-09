# T-058 执行主控决定 01（2026-10-09，依据 ready_rev 1）

批准 needs-decision-01 的两处上游接入，范围限：

1. `apps/server/src/agentGateway/Services/AgentGatewaySessionRegistry.ts`：扩展能力类型加入 a2a 能力；增加按 thread 绑定角色预设的窄接口。
2. `apps/server/src/agentGateway/Layers/AgentGatewaySessionRegistry.ts`：签发时读取已绑定预设并冻结能力集合；没有 a2a 预设的原生会话保持现有六种通用能力不变。

理由：ticket 与 spec 第 1 节要求每个预设的 `tools/list` 精确等于预期集合、主控不需要通用 `thread:write`（结构底线“不暴露的工具就是没权限”）；不在签发处接入无法实现。这是落实已定设计的接入，不是新增业务权限。

条件：
- 无 a2a 预设的会话行为不变，需要一条反例证明（普通 Synara 会话签发的能力集合与父修订一致）。
- 预设变更不修改已签发凭据，须重新签发（ticket 反例项）。
- 不改 provider adapter、`sessionLease.ts`、`AgentGatewayCredentials.ts`、`computerToolPermission.ts`；两处接入列入上游清单。
