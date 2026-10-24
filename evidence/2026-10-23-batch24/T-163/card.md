# 任务卡 T-163-1（派发漏要求、验收脚本只做字串、无新事实长轮询的提示词对策）

先读 `evidence/2026-10-23-batch24/COMMON-FIX.md`、`.project-map/tickets/T-163-model-behavior-countermeasures.md`、`findings/2026-10-23-real-user-dogfood.md` 中对应条目。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-163-1 |
| 来源 | T-163 ready_rev 1（ready_by ideation；用户原话见 ticket） |
| 目标 | 执行主控（应用内）角色说明与派发说明补三条判断要求；脚本只做机械可核的部分。 |
| 修改边界 | 允许：应用内执行主控角色说明所在文件（先 `git grep` 找出并列出，如 `workbench/src/terminalCli.ts` 的说明文本）；新增或修改只属于本票的测试 `workbench/tests/test_t163_*.py`（或 .mjs/.ts）；`evidence/2026-10-23-batch24/T-163/**`；必要的 `workbench/README.md` 行。其他产品文件需要改时先上报说明理由。禁止：`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、他人票的测试。 |
| 任务类型 | 缺陷修复 |
| 复杂度 | M |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 本卡提交所在的 main |
| 唯一写入者 | Herdr agent `b24-t163`，worktree `/Users/luckye/Documents/Code/a2a-wt-t163`，分支 `exec/t163` |

验收要求真实 haiku 主控复跑 C5 与验收脚本两个场景，修前同场景复现为红态：写成 RUN-OUTSIDE 交我跑，真实模型回合上限 16。不做策略引擎。
