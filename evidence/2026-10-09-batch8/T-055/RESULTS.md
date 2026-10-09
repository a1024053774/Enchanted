# T-055：问题上报最薄一刀

状态：**BLOCKED**。需要执行主控批准一个范围外的上游接入文件；尚未开始实现，ticket 保持 open，待主控决定与关闭。

依据：任务书 `brief-T-055.md`、T-055 `ready_rev: 1`、`controller-split-user-input-2026-10-09.md` 第 2～4 节。Synara fork 基线为 `6efac8432d7ae37e74b76e42d4e9fd3004d9a0e2`，分支 `a2a`。本次按用户原话“读并执行 /Users/luckye/Documents/Code/a2a/evidence/2026-10-09-batch8/brief-T-055.md”执行任务书；未把旧 ticket 或队友消息作为新增授权。

## 需要主控决定

任务书限定写入 `packages/a2a-gates`、`packages/contracts`、`apps/server/src/a2a`、`apps/web/src/a2a`，并明确要求“其他上游文件先停下问主控”。

实际 MCP 工具目录由范围外的 `apps/server/src/agentGateway/Layers/AgentGateway.ts` 构造。第 1540～1541 行只注册 `a2aSubmitTool(a2aGates)`；第 1588～1591 行将该目录传给 `makeAgentGatewayMcpTransport`；第 1609 行导入现有 submit 工具。只在允许目录里增加 `a2aRaiseTool` 无法让正式入口的 `tools/list` 出现它。

最小选项：批准上述文件的两处接入，后续实现保持在原四个目录内。

```diff
-    ...(a2aGates ? [a2aSubmitTool(a2aGates)] : []),
+    ...(a2aGates ? [a2aSubmitTool(a2aGates), a2aRaiseTool(a2aGates)] : []),
-import { a2aSubmitTool } from "../../a2a/tools";
+import { a2aRaiseTool, a2aSubmitTool } from "../../a2a/tools";
```

这只是接入提案，未应用。`a2aRaiseTool` 本身将放在允许目录 `apps/server/src/a2a/tools.ts`，按规格使用凭据身份与活跃 turn 校验。

另有一个待验证点：`apps/server/src/agentGateway/computerToolPermission.ts:247` 的网关工具名集合目前只有 `a2a_submit`，未列出 `a2a_raise`；这影响 provider 自动批准识别，不是工具注册入口。本次不申请扩大该文件的修改权限，也不绕过其普通权限路径；如后续真实验证证明必须改动，将另向主控报告。

## 已执行与未执行

- 启动时 `project_map.py status --root .`：exit 0，Problems 0、Stale living docs 0。
- 已读取项目 AGENTS.md、地图、术语、intent、ticket、规格相关章节，以及 fork AGENTS.md、CLAUDE.md、WORKBENCH.md；已定位门禁核心、消息记录器、HTTP 路由、工具定义、任务窗口和工具注册的直接调用方。
- 原始定位命令及输出保存在 [scope-check.txt](scope-check.txt)。这属于静态定位证据，不冒称真实 `tools/list` 红态。
- 未改 fork 源码，未启动服务或 provider，未执行红绿验收、截图、真实 Codex、既有套件、typecheck、lint 或完成检查点的独立审查。全部 Acceptance 仍未勾选。
- 未操作正式工作台数据、共享 dist、用户 Herdr 或用户配置；未 push。fork 原有未跟踪 `.grok/` 保留。a2a 其他 worker/主控的文件保留，本次只提交本目录与 T-055 Resolution。

批准后从父修订真实入口的红态开始，按同一验收脚本完成 Tracer bullet，再运行既有相关检查与一次 fresh-context 只读独立审查。本次未取得任何 PASS 结论。
