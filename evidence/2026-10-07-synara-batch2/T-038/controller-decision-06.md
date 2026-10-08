# T-038 主控决定 06：Electron 任务窗口的有限复验（2026-10-08，Claude Code）

INCOMPLETE 交付、独立审查 INCOMPLETE 与 post-review-electron 现场原样保留。暂不关闭 ticket。第 1 项（桌面版截图）是 M1 切换条件之一，且 `_nonReactive`（preloadRoute）可能来自本 ticket 新增的路由，需先排除。授权一轮有限复验：

1. 路由错误归因：在 dev Chrome 中分别打开基线 worktree 与候选，以相同步骤到达根页面和（候选的）任务窗口入口，记录控制台是否出现 `_nonReactive`、404。只在候选出现且与新增路由相关时，按本 ticket 缺陷处理：先保存红态，再修复、重新冻结并补审查。两边都出现则记为上游。
2. 导入弹窗：只经 UI 操作关闭（例如 Escape、弹窗内其他关闭控件），或在 Electron 窗口中直接导航到任务窗口的路由地址；不注入业务状态、不改上游代码、不写用户 profile。仍无法关闭就记录现场。
3. 若到达任务窗口，按 ticket 第 1 项截图（一个项目下至少两个任务，其中一个含 worker 与 reviewer，显示门禁状态）。到不了就保持 INCOMPLETE，写明原因，主控据此决定。
4. 时间有限：这一轮结束即交接，不再扩大排查；结果追加到 RESULTS，旧结论不覆盖，完成后照常给 DONE 行。
