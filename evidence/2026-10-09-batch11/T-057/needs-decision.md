# T-057：四处上游接入需主控决定

状态：**BLOCKED**。worker `s11-t057`，T-057 `ready_rev: 2`；fork 基线 `2330534b2cf906b9d8f0a0b643adb370683d7fe0`。尚未修改产品代码，也未启动应用或调用真实模型。

任务书要求“系统通知、项目侧栏徽标等若需要改这些目录外的上游文件，先停下说明位置与最小接入”。T-057 验收要求项目侧栏徽标、后台系统通知、MCP 处置与 CLI/HTTP 共用核心。现有接入点都在指定四个目录之外，需要批准以下最小接入后才能继续：

| 文件（相对 Synara fork） | 当前位置 | 最小接入 |
| --- | --- | --- |
| `apps/web/src/components/Sidebar.tsx` | 5721、5790 行，现有项目名称行 | 从 a2a 模块挂载“等你决定”计数徽标，不复制项目行逻辑 |
| `apps/web/src/routes/__root.tsx` | 109、359 行，全局通知运行组件 | 导入并挂载 a2a 提醒组件，离开任务窗口也继续观察；逻辑留在 `apps/web/src/a2a` |
| `apps/server/src/agentGateway/Layers/AgentGateway.ts` | 1541、1609 行，a2a 工具注册与导入 | 注册新的问题处置 MCP 工具，处理、身份校验与状态派生留在 a2a 核心/服务 |
| `apps/server/src/agentGateway/computerToolPermission.ts` | 246～248 行，网关工具目录 | 将新工具名加入既有目录，保持真实注册与目录一致，沿用已有 grant/lease/turn 保护 |

建议允许这四处接入。提醒复用已有 `window.desktopBridge.notifications.show`，设置复用 `enableSystemTaskCompletionNotifications`，不新增通知基础设施或设置字段；发送参数明确 `silent: true`、`suppressWhenForeground: true`。尚未判断 macOS 通知权限是否可用；若真实验证遇到系统授权，按任务书再次停下，不自行授予。

`scope-probe.json` 保存完整源码版本、位置与实际命令输出；重放命令：`python3 evidence/2026-10-09-batch11/T-057/scope-probe.py`。这只是只读范围证据，不是红态验收。

开工前已对照 T-055 `RESULTS-03.md` 和 `acceptance-review-final.md`。前者保留当时最终审查未完成的 INCOMPLETE，后者对最终候选明确给出 PASS；不改写历史结论。T-055 单条路径继续使用。已发现核心 `forward` 永久显示“已转交”，而 `scripts/inbox:267` 在转交满 15 分钟后派生“等你决定”；这属于 T-057 指定的状态完整化范围，后续按 spec 第 4 节与 inbox 的超时语义修正，不能以旧实现为准。

请求主控明确是否允许这四处上游接入。若不允许，完整验收无法成立，请主控调整范围或安排接入归属；worker 不自行缩减验收。
