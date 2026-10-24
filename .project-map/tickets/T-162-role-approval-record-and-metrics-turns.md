---
id: T-162
title: F04+F06：角色批准不进用户输入记录；指标把未知主控回合显示为 0
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：用户 2026-10-23 逐字：“全部 7 条 + 3 条模型行为对策”（选项：切全部修复票）；报告 findings/2026-10-23-real-user-dogfood.md，执行主控 needs-decision 20261023T222913Z。

报告 F04：角色批准/拒绝只在角色事件里，不在“用户输入记录”。F06：指标主控回合恒为 0，实际 37 个根回合（managed 23、主控 13、Reflect 1），看板 22 且漏计一次人工输入。
目标：批准/拒绝进统一输入记录并关联角色申请事件（此为用户输入，术语见 CONTEXT.md）；指标区分已核对的零与未知/未覆盖，并说明口径，提供逐会话计数来源。不把看板数报成全局总回合。

通用要求：先在真实 Electron（隔离实例）复现并留红态证据，再修最小根因层；不加自动重试掩盖未知；使用 `CONTEXT.md` 术语；修改界面文案前读 `frontend-less-ai-tone`。

## Acceptance

- [x] 真实实例：批准后记录页出现该条并关联角色事件。
- [x] 指标：主控回合与原生日志核对一致，或明确显示“未覆盖/未知”。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-24 关闭，PASS。修前红态（RUN-OUTSIDE-01，c01742804）：角色决定不进用户输入、项目终端主控回合显示 0。修复：`roleRequests.ts` 决定与用户输入同一事务写入并关联角色事件（自动竞争拒绝不计用户输入，重复决定被拒，存储故障整体回滚）；`metrics.ts`/`MetricsPage.tsx` 区分未覆盖、已记录 0 与已记录 N，并可展开逐会话来源；`RecordsPage.tsx`、README 同步。RUN-OUTSIDE-02（候选 b27e9e4d0）14/14：真实 Electron 绿态、7 个已知坏实现均被拒、T-121/T-133/T-134/T-107 回归通过；两个真实原生主控日志核对（构思 4、执行 1 根回合）显示为未覆盖，修前版本对同一日志误报 0。独立审查 agy PASS。合并 3feb9e5ae。证据 `evidence/2026-10-23-batch24/T-162/RESULTS.md`。范围外：README 记录页旧“Codex 主控暂不记”与 T-133 一节矛盾，已转构思主控（20261024T022208Z）。
