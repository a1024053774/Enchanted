# 任务卡 T-162-1（角色批准不进输入记录；指标把未知主控回合显示为 0）

先读 `evidence/2026-10-23-batch24/COMMON-FIX.md`、`.project-map/tickets/T-162-role-approval-record-and-metrics-turns.md`、`findings/2026-10-23-real-user-dogfood.md` 中对应条目。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-162-1 |
| 来源 | T-162 ready_rev 1（ready_by ideation；用户原话见 ticket） |
| 目标 | 批准/拒绝进统一用户输入记录并关联角色申请事件；指标区分已核对的零与未知/未覆盖、写明口径、提供逐会话计数来源。 |
| 修改边界 | 允许：`workbench/src/userInputRecords.ts`、`workbench/src/metrics.ts`、`workbench/src/gates/core.ts`（仅角色批准写记录处）、`workbench/app/RecordsPage.tsx`、`workbench/app/MetricsPage.tsx`；新增或修改只属于本票的测试 `workbench/tests/test_t162_*.py`（或 .mjs/.ts）；`evidence/2026-10-23-batch24/T-162/**`；必要的 `workbench/README.md` 行。其他产品文件需要改时先上报说明理由。禁止：`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、他人票的测试。 |
| 任务类型 | 缺陷修复 |
| 复杂度 | M |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 本卡提交所在的 main |
| 唯一写入者 | Herdr agent `b24-t162`，worktree `/Users/luckye/Documents/Code/a2a-wt-t162`，分支 `exec/t162` |

角色批准属于用户输入（CONTEXT.md）。指标口径改动只做显示与来源，不改评分口径；不用真实模型时须用夹具证明“未知”与“0”区分，真实主控回合核对写成 RUN-OUTSIDE，haiku 上限 6。

## 边界修订（执行主控 2026-10-24，回复 worker issue 20261024T003142Z）

卡上写的 `workbench/src/gates/core.ts` 是执行主控定位错误：角色批准在 `workbench/src/daemon.ts` 的 `role_request_decide` 分支与 `workbench/src/roleRequests.ts` 的 `decide`。允许修改这两处，仅用于把操作员亲自做出的批准/拒绝写入统一用户输入记录并关联角色申请事件，保持事件与记录一致；同角色其他申请的自动拒绝、过期不算用户输入。`gates/core.ts` 不再在允许范围内。
