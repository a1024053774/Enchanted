# 任务卡 T-159-1（向右分屏换成新普通终端，原 worker 不并排）

先读 `evidence/2026-10-23-batch24/COMMON-FIX.md`、`.project-map/tickets/T-159-split-keeps-original-pane.md`、`findings/2026-10-23-real-user-dogfood.md` 中对应条目。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-159-1 |
| 来源 | T-159 ready_rev 1（ready_by ideation；用户原话见 ticket） |
| 目标 | 任务视图里对 worker 点向右分屏后，原 worker 与新窗格并排，窗格数、类型、目录与菜单一致；与 T-139 视图模型一致。 |
| 修改边界 | 允许：`workbench/app/renderer.tsx`、`workbench/app/*.ts(x)` 中布局/视图相关文件（列出）、`workbench/src/layout*.ts`；新增或修改只属于本票的测试 `workbench/tests/test_t159_*.py`（或 .mjs/.ts）；`evidence/2026-10-23-batch24/T-159/**`；必要的 `workbench/README.md` 行。其他产品文件需要改时先上报说明理由。禁止：`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、他人票的测试。 |
| 任务类型 | 缺陷修复 |
| 复杂度 | M |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 本卡提交所在的 main |
| 唯一写入者 | Herdr agent `b24-t159`，worktree `/Users/luckye/Documents/Code/a2a-wt-t159`，分支 `exec/t159` |

若任务 agent 与普通终端按 T-139 视图模型不能同屏，按 ticket 做“操作前说明”，并在 RESULTS 写明依据。不用真实模型（受控 PTY 即可）。
