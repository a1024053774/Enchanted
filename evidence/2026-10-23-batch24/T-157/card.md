# 任务卡 T-157-1（Stop hook 期间用户输入后交付停住）

先读 `evidence/2026-10-23-batch24/COMMON-FIX.md`、`.project-map/tickets/T-157-stop-hook-user-input-submit.md`、`findings/2026-10-23-real-user-dogfood.md` 中对应条目。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-157-1 |
| 来源 | T-157 ready_rev 1（ready_by ideation；用户原话见 ticket） |
| 目标 | 按 ticket：先查清 Stop 批次与用户输入相交时 submit 被 worker_not_active 拒绝的根因；界面显示最后确定事实、拒绝原因与绑定原 attempt 的恢复入口；不自动重试。 |
| 修改边界 | 允许：`workbench/src/panes.ts`、`workbench/src/gates/**`、`workbench/app/renderer.tsx`、`workbench/src/sidebar.ts`；新增或修改只属于本票的测试 `workbench/tests/test_t157_*.py`（或 .mjs/.ts）；`evidence/2026-10-23-batch24/T-157/**`；必要的 `workbench/README.md` 行。其他产品文件需要改时先上报说明理由。禁止：`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、他人票的测试。 |
| 任务类型 | 缺陷修复 |
| 复杂度 | L |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 本卡提交所在的 main |
| 唯一写入者 | Herdr agent `b24-t157`，worktree `/Users/luckye/Documents/Code/a2a-wt-t157`，分支 `exec/t157` |

交付语义（人工介入后交付是否仍有效、恢复入口做什么）若需选择，先写 `DESIGN-QUESTION.md` 列证据与最小选项，停下说 NEEDS-DECISION，不自己定。真实模型回合上限 12（haiku）。
