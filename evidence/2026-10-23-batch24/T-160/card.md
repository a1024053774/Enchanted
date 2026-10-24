# 任务卡 T-160-1（reviewer 输出带围栏 JSON 被门禁暂停）

先读 `evidence/2026-10-23-batch24/COMMON-FIX.md`、`.project-map/tickets/T-160-review-json-fenced-recovery.md`、`findings/2026-10-23-real-user-dogfood.md` 中对应条目。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-160-1 |
| 来源 | T-160 ready_rev 1（ready_by ideation；用户原话见 ticket） |
| 目标 | 提示词层：reviewer 启动指令与 `workbench/roles/reviewer.md` 写清输出格式（无围栏）并自检；产品层：协议错误保留原文并拒绝，界面写明原因并给出“为同一次交付新开审查”这类明确恢复路径。 |
| 修改边界 | 允许：`workbench/roles/reviewer.md`、`workbench/src/gates/qualityProtocol.ts`、`workbench/src/gates/core.ts`（仅协议错误后的恢复）、`workbench/app/` 问题页相关文件；新增或修改只属于本票的测试 `workbench/tests/test_t160_*.py`（或 .mjs/.ts）；`evidence/2026-10-23-batch24/T-160/**`；必要的 `workbench/README.md` 行。其他产品文件需要改时先上报说明理由。禁止：`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、他人票的测试。 |
| 任务类型 | 缺陷修复 |
| 复杂度 | M |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 本卡提交所在的 main |
| 唯一写入者 | Herdr agent `b24-t160`，worktree `/Users/luckye/Documents/Code/a2a-wt-t160`，分支 `exec/t160` |

不剥围栏、不用自然语言替代门禁结果。验收要求真实 haiku reviewer 跑 3 次：写成 RUN-OUTSIDE 交我跑，真实模型回合上限 9。是否加自动重试不做。
