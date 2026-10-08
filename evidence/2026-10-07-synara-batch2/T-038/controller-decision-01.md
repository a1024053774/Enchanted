# T-038 主控决定 01：共用接入文件归属（2026-10-07，Claude Code）

在 T-037 决定 01（`../T-037/controller-decision-01.md`）之上补充。T-038 在自己的 worktree（分支 `a2a-t038`）中负责：

1. `packages/a2a-gates/package.json`：只新增 membership 子路径导出，不改其他字段。
2. membership 的 schema/types 不放 `packages/contracts/src/a2aGates.ts`（归 T-037）；放 T-038 新建的 `packages/contracts/src/a2aMembership.ts`，在 contracts 的导出入口只加一行导出。该入口文件本轮归 T-038，T-037 不改；T-037 需要时先问主控。
3. `apps/server/src/a2a/httpRoute.ts`：在既有 auth 下挂 membership 路由，只做新增，不改既有 gate 路由与鉴权。本轮归 T-038，T-037 不改。
4. web 路由：优先新建 route 文件挂任务窗口入口；必须改 `apps/web/src/routes/_chat.tsx` 时只加入口，改动最小，并列入上游文件改动清单。
5. 所有改动都是新增式，便于主控合并 `a2a-t038` 回 `a2a`；合并冲突由主控处理，提交前不要 rebase 到 `a2a`。
6. 人工介入事件形状：T-037 尚未定。按 T-037 决定 01 第 3 条，定下后由主控转来；在此之前界面显示为空，不自造字段。

补充（2026-10-08，见 `../T-037/controller-decision-03.md`）：`httpRoute.ts` 按段分写。T-037 改既有门禁 GET 处理的几行；T-038 只新增 membership 路由与 OPTIONS，不改既有门禁 GET/POST 段。
