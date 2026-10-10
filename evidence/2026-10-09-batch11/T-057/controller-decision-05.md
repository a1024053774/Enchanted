# T-057 执行主控决定 05：用户专属动作的 MCP 证据组合（2026-10-09）

依据 ready_rev 3；回应 worker 上报 `20261010T034945Z-worker:s11-t057-issue-001`。

同意 worker 建议的证据组合，算满足任务书第 3 项与 ticket"七个处置动作逐个经 MCP 入口验证"：

1. 七个动作全部经真实 MCP（`a2a_disposition`，活跃主控凭据）各调用一次。
2. 主控可用的 close、needs-user、forward、delivered：核对成功追加一条处置记录与派生状态；blocking 被 close 时核对拒绝。
3. 用户专属的 reopen、snooze、dismiss：经 MCP 核对被拒绝、零追加、状态不变；再经 HTTP 用户入口各调用一次，核对追加记录与派生状态。HTTP 与 MCP 走同一核心，在 RESULTS 写明调用链。
4. 不新增用户 MCP 身份、不改权限范围（权限归 T-058 预设与 T-064 设置页）。

理由：spec 第 4 节规定这三个动作只归用户；MCP 入口只开给会话角色。要求它们经 MCP 成功，等于给会话开用户权限，与"dismiss 只归用户"的底线冲突。
