# T-066 执行主控决定 01：批准两处上游接入（2026-10-10）

回应 `upstream-scope-request.md` 与收件箱 `20261010T150042Z-worker:t066-issue-001`。

1. 批准 `upstream-proposed.patch` 的两处改动：`apps/server/src/agentGateway/toolRuntime.ts` 加可选只读 `callerA2ARole`；`apps/server/src/agentGateway/mcpTransport.ts` 从 `callerSession.a2aPermissions?.role` 赋值。只加这一个字段，不做别的。理由：角色已在签发时冻结在凭据里；靠能力反推角色不可靠，因为用户可以改能力。
2. 批准核心 stop 的检查从“caller.address 必须是 ideation”改为“调用者有 a2a:stop 能力”，地址写凭据里冻结的角色。只改 a2a_stop，不改其他命令的地址投影。没有冻结角色的凭据（非受管会话）照旧拒绝，不猜角色。
3. 红态接受 red02（其中“原生事件 oracle 过严”这一项按 reassessment 处理，原始结果保留）。red01 是夹具准备失败，不计入红态。
4. 其余照任务书，独立审查一次。
