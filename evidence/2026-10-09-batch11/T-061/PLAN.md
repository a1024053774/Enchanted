# T-061 执行与证据计划

目标：让 Codex 原生 MCP 提示中的数字工具名在缺少 `_meta.tool_name` 时可被解析；免确认仍由既有目录、运行身份、活跃 turn 和授权条件共同决定。

不做：改工具名目录、权限策略、工作台运行数据、其他 ticket、真实模型调用或外部发布。

验收：复用 T-055 的 13 项探针，先取得 `a2a_raise` / `a2a_submit` 缺字段的红态，再运行同一信号取得绿态；逐条覆盖非受管、非活跃、失效身份、未授权与目录外数字名字；所有其他目录工具逐项对照；相关套件及 fmt/typecheck/lint 通过；固定候选只做一次 fresh-context 只读审查。

失败方式（测试前列明）：数字名字不能解析；授权不足仍被批准；lease 缺失或撤销仍被批准；空闲/缺失/过期 turn 或错误 thread 仍被批准；错误 server/approval kind 仍被批准；停止中/Plan 模式仍被批准；目录外名字、近似工具名或非完整原生提示被批准；显式工具名被提示文本覆盖；自动批准写入持久授权；目录内其他工具发生行为变化。

起点：fork `2330534b2cf906b9d8f0a0b643adb370683d7fe0`，worktree `/Users/luckye/Documents/Code/synara-t045`，分支 `a2a-t061`。切换前工作树干净。ticket ready_rev 1，worker `s11-t061`，派发序号 2，Herdr pane `wF:p1K`。本次不是工作台受管模型 run；brief 未提供门禁 task/attempt/session/fence，需要主控明确 Herdr 期的显式 submit 收据方式。

Ubiquitous language：沿用 CONTEXT.md 的工具名目录、原生会话、受管 attempt 与 Submit 术语。Deep modules：保留现有 manager 决策入口，不新增解析包装层。本票单层解析修复，无需增加跨层 Tracer bullet。
