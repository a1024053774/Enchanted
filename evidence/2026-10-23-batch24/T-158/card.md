# 任务卡 T-158-1（修订任务卡后重试被旧 attempt 路径占用挡住）

先读 `evidence/2026-10-23-batch24/COMMON-FIX.md`、`.project-map/tickets/T-158-revise-then-retry-path-release.md`、`findings/2026-10-23-real-user-dogfood.md` 中对应条目。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-158-1 |
| 来源 | T-158 ready_rev 1（ready_by ideation；用户原话见 ticket） |
| 目标 | 打回→保存 v2→revise→正常 dispatch 一次成功（无需交叠参数）；旧 attempt 仍活跃时路径检查照样拒绝；角色说明与 `a2a help` 写明步骤。 |
| 修改边界 | 允许：`workbench/src/gates/**`、`workbench/src/terminalCli.ts`、应用内执行主控与 worker 的角色说明文件（先列出）；新增或修改只属于本票的测试 `workbench/tests/test_t158_*.py`（或 .mjs/.ts）；`evidence/2026-10-23-batch24/T-158/**`；必要的 `workbench/README.md` 行。其他产品文件需要改时先上报说明理由。禁止：`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、他人票的测试。 |
| 任务类型 | 缺陷修复 |
| 复杂度 | M |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 本卡提交所在的 main |
| 唯一写入者 | Herdr agent `b24-t158`，worktree `/Users/luckye/Documents/Code/a2a-wt-t158`，分支 `exec/t158` |

“保留证据”与“占用路径”的区分须来自现行规格；若规格没有定义 revoked attempt 何时释放路径，上报 NEEDS-DECISION。可以不用真实模型（受控 CLI 驱动门禁即可）。
