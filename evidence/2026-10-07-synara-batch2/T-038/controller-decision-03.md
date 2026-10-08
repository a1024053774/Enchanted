# T-038 主控决定 03：任务载体选择（2026-10-07，Claude Code）

批准独立 membership。主控抽查了对照页的两条关键依据：`ProjectAgentService.ts:1361` coordinator 仅限 Hub；`groupsBetaGate.ts` 在 Stable 下拒绝 createTask 等 API。均属实。

1. 任务窗口的"任务"= a2a 任务；受管任务以门禁 task id 为身份。membership 保存项目、显示标题、thread 与角色；业务状态只读门禁核心。未挂合同的任务只有归属与标题，没有第二套状态。
2. 不读写、不同步 Synara 原生 ProjectTask/ProjectTaskAttempt/HubWorkItem 的状态；本轮不做 Hub 场景。
3. 术语已由主控更新到 CONTEXT.md 的 Task 条目：原生对象提及时用原名，不称为任务或 attempt。
4. 按对照页的下一步实施：先经隔离服务器 HTTP 入口取得归属请求的红态，再做 storage → 鉴权 HTTP → web 的 tracer bullet。
