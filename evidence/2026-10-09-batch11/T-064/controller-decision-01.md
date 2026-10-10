# T-064 执行主控决定 01：上游接入与免确认口径（2026-10-10）

依据 ready_rev 1；回应 `T-064/needs-decision-01.md`。

## 批准的上游接入（只做挂载、传递身份与调用 a2a 模块的判断，逻辑放 a2a 模块）
1. `apps/web/src/settingsNavigation.ts`：加"角色权限"导航项。
2. `apps/web/src/routes/_chat.settings.tsx`：import 并挂载 `apps/web/src/a2a/RolePermissionsSettingsPanel.tsx`。
3. `apps/server/src/agentGateway/Services|Layers/AgentGatewaySessionRegistry.ts`：签发时读取用户自定义（无自定义取现有预设）并冻结进凭据；已签发 token 不重写。
4. `apps/server/src/agentGateway/Services|Layers/AgentGatewayCredentials.ts`：connection 增加窄的 a2a 权限查询，经已有 `registry.verify` 核对原 token。
5. `apps/server/src/codexAppServerManager.ts`（约 4493–4501）：在已有 lease/退休/stopping/活跃 turn 检查都通过后，按冻结的 a2a 免确认集合决定；未勾选留在原提示路径。
6. `apps/server/src/provider/Layers/ClaudeAdapter.ts`（约 5940、6125）：同样口径。先做无模型协议探针确认 SDK 的 `setMcpPermissionModeOverride` 在已安装 CLI 上真实可用；探针失败就停下报告，不加 fallback。

## 不批准
- OpenCode、ACP（`AcpAdapterSupport.ts`）、Devin、Cursor、Grok、Droid 适配器：本票不改。a2a 的受管会话目前是 Codex worker 和 Claude 主控；这些 provider 保持现有行为（不新增免确认）。设置页对免确认写明"目前对 Codex、Claude 会话生效"，RESULTS 列为局限。
- 不改 `computerToolPermission.ts` 共享匹配函数的签名；需要的判断放在 a2a 模块，由第 5、6 项的调用点调用。若你认为必须改该文件，先停下说明为什么调用点方案不行。

## 免确认口径（采纳你的建议）
- 某角色**没有自定义**：完全沿用既有语义（含 T-055 的 a2a_raise/a2a_submit 前提与反例），界面标"沿用默认"。反例对照 T-058/T-055。
- 用户**显式设置**某角色的免确认集合后：勾选项在有效受管身份 + 活跃 turn 下免确认；未勾选项照常提示；非受管会话、非活跃 turn 仍提示。
- 恢复默认 = 回到"没有自定义"。
- 免确认选择与能力一样在**签发时冻结**；界面提示"新会话（重新签发凭据）后生效"。

## 其他
五种失败方式按你的计划处理（CAS、同一事务、拒绝未知能力名并保留原值、允许显式空集合、旧凭据不变）。完成后冻结、审查一次（约定不变）。这项范围取舍会在完成报告里告诉构思主控，用户可修订。
