# T-055 执行主控决定 01：批准 AgentGateway.ts 的两处接入（2026-10-09）

依据 ready_rev 1。主控核对 `apps/server/src/agentGateway/Layers/AgentGateway.ts` 1540–1541 行：MCP 工具目录在此构造，现只注册 `a2aSubmitTool`。批准按 RESULTS 中的提案改两行（import 与注册 `a2aRaiseTool`），属于 spec"对上游文件只做注册与挂载"的范围，列入上游改动清单。`a2aRaiseTool` 本身留在 `apps/server/src/a2a/tools.ts`。

`computerToolPermission.ts:247` 的网关工具名集合不在本次批准内。真实验证中若出现 provider 对 `a2a_raise` 的权限提示，保存现场、停下报告主控，不自行修改该文件（它涉及工具自动批准，属于权限类改动，须经构思主控问用户）。
