# 任务卡 T-161-1（只读查看报输入错误；窗格头不显示主控角色）

先读 `evidence/2026-10-23-batch24/COMMON-FIX.md`、`.project-map/tickets/T-161-readonly-view-and-role-label.md`、`findings/2026-10-23-real-user-dogfood.md` 中对应条目。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-161-1 |
| 来源 | T-161 ready_rev 1（ready_by ideation；用户原话见 ticket） |
| 目标 | 只读窗格（审查员、历史 worker）不申请可写输入焦点，真正输入失败仍提示；批准后的主控窗格头显示载体与角色，收起侧栏仍可辨认。 |
| 修改边界 | 允许：`workbench/app/main.ts`、`workbench/app/preload.ts`、`workbench/app/renderer.tsx`；新增或修改只属于本票的测试 `workbench/tests/test_t161_*.py`（或 .mjs/.ts）；`evidence/2026-10-23-batch24/T-161/**`；必要的 `workbench/README.md` 行。其他产品文件需要改时先上报说明理由。禁止：`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、他人票的测试。 |
| 任务类型 | 缺陷修复 |
| 复杂度 | S |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 本卡提交所在的 main |
| 唯一写入者 | Herdr agent `b24-t161`，worktree `/Users/luckye/Documents/Code/a2a-wt-t161`，分支 `exec/t161` |

不用真实模型。
