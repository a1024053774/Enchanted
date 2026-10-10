# T-066 最小上游接入请求

BLOCKED：brief 限定生产修改在四个 a2a 目录；在真实 MCP 中，凭据已有冻结的 `a2aPermissions.role`，但没有传到工具上下文。若只看能力推断角色，用户可自定义能力后归属仍会错误；若读取当前 membership，旧凭据的角色就不再是凭据发放时的角色。

证据位置：Synara fork `apps/server/src/agentGateway/Services/AgentGatewaySessionRegistry.ts:25` 保存凭据角色；`apps/server/src/agentGateway/toolRuntime.ts:43` 定义 ToolContext，但只有 callerCapabilities、thread、turn；`apps/server/src/agentGateway/mcpTransport.ts:360` 构造上下文，没有角色字段。

建议批准两处上游最小接入（不改权限、凭据发放或其他工具）：

- `apps/server/src/agentGateway/toolRuntime.ts:55`：新增可选只读 `callerA2ARole`，类型来自 contracts 的 A2ASessionPreset。
- `apps/server/src/agentGateway/mcpTransport.ts:366`：赋值 `callerA2ARole: callerSession.a2aPermissions?.role`。

a2a_stop 独立使用该冻结角色写实际地址，thread/turn 沿用现有凭据上下文。核心只看传入的 stop 能力，不再要求 ideation 地址。其他命令的地址投影不扩大本票范围。

请主控批准上述两文件的接入。批准前不做生产修改；红态复现仍可使用现有真实服务端夹具。
