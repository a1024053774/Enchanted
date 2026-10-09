# T-057 执行主控决定 01：上游接入范围（2026-10-09）

依据 ready_rev 2。

批准（只做挂载与注册，逻辑留在 a2a 模块，列入上游清单）：
1. `apps/web/src/components/Sidebar.tsx`：在项目名称行挂载 a2a 的"等你决定"计数徽标。
2. `apps/web/src/routes/__root.tsx`：导入并挂载 a2a 提醒组件；复用 `window.desktopBridge.notifications.show` 与 `enableSystemTaskCompletionNotifications`，`silent: true`、`suppressWhenForeground: true`，不新增通知基础设施或设置字段。
3. `apps/server/src/agentGateway/Layers/AgentGateway.ts`：注册问题处置 MCP 工具（import 与列表注册），身份校验与状态派生留在 a2a 核心/服务。

不批准：
4. `apps/server/src/agentGateway/computerToolPermission.ts` 加入新工具名。把工具加入免确认目录属于权限变更，用户只授权了 `a2a_raise`（"A，然后你开"）。T-057 验收要求处置"经 MCP 走同一核心"，不要求该工具免确认；注册后按 Synara 普通权限路径弹确认即可。验收中若确有无人值守调用该工具的需要，停下报告，执行主控再经构思主控问用户。

另：核心 `forward` 永久显示"已转交"与 `scripts/inbox` 的 15 分钟后派生"等你决定"不一致——按 spec 第 4 节修正核心，与 inbox 对齐，红绿记入 RESULTS。
