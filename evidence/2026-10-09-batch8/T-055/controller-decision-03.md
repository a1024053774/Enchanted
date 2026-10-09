# T-055 执行主控决定 03：按 ready_rev 2 在当前候选上补第 9 项（2026-10-09）

构思主控 revise 条目 `20261009T105730Z-ideation-revise-001`：用户选 A，逐字"A，然后你开"；T-055 由 ready_rev 1 改为 2，只增加第 9 项验收。

决定：由当前 worker 在同一候选上补做，不另起；之后的证据与 Resolution 依据 ready_rev 2。

1. 撤销决定 02 中"逐次人工批准"的安排（已做的逐次批准记录保留）。
2. 把 `a2a_raise` 加入 `apps/server/src/agentGateway/computerToolPermission.ts` 的网关工具名目录，与 `a2a_submit` 同口径；只改这一处，列入上游清单。先红后绿；反例逐条：非受管会话、非活跃 turn、身份无效时仍要提示（或按既有口径拒绝）。不改其他工具、会话类型或权限模式（用户授权范围仅限此项）。
3. 真实 Codex 上报（第 8 项）须在无人批准的情况下完成；runtimeMode 用 full-access 或已授权自动批准的配置，并写明依据。
