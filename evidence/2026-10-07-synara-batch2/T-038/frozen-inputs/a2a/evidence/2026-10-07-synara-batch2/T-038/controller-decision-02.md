# T-038 主控决定 02：Synara 原生 ProjectTask 与 a2a 任务的关系（2026-10-07，Claude Code）

发现 Synara 已有 ProjectTask / ProjectTaskAttempt / HubWorkItem。为避免出现两个都叫"任务"的概念（统一术语要求）：

1. 实现前先在证据中写一页对照：Synara 的 ProjectTask、ProjectTaskAttempt、HubWorkItem、Todo chatThreadId、split views 各自表示什么、能否表示"同一任务下多个带角色的 thread"，以及它们和门禁 task/attempt 的对应关系。
2. 优先方案：任务窗口以 Synara 原生 ProjectTask 为"任务"，a2a 的 membership 只是一张以 ProjectTask id（及门禁 task id）为键的附加表，记录多个 thread 及角色；不改上游表结构。
3. 若原生 ProjectTask 不能作为任务窗口的载体（例如生命周期或语义与门禁 task 冲突），再用独立 membership，并在对照页写明原因。
4. 两种方案的选择与理由写进对照页后，先告诉主控再实现。术语表由主控更新，你不改 CONTEXT.md。
