---
id: T-160
title: M03：reviewer 把审查 JSON 包进代码块，门禁协议错误暂停
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

报告 M03/T-101、T-102：reviewer（haiku）三次输出 ```json 围栏，门禁按 review_json 协议错误暂停；其中一次实质判“可合并”仍无法使用。
目标：（1）提示词层：reviewer 启动指令与角色卡写清最终输出格式、不带围栏，并在输出前自检；（2）产品层：协议错误时保留原文并拒绝，不剥围栏追认通过；界面写明原因，并给出明确的恢复路径（例如为同一次交付新开审查）。是否新增自动重试不做，需要时经 needs-decision。

通用要求：先在真实 Electron（隔离实例）复现并留红态证据，再修最小根因层；不加自动重试掩盖未知；使用 `CONTEXT.md` 术语；修改界面文案前读 `frontend-less-ai-tone`。

## Acceptance

- [x] 真实 haiku reviewer 跑 3 次，输出均符合协议（或被拒后界面给出恢复入口）。
- [x] 反例：带围栏输出仍被拒绝，原文保留。
- [x] 不剥围栏、不自然语言替代门禁结果。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-24 关闭，PASS。修前红态（RUN-OUTSIDE-01，3aea74368）：带围栏输出暂停后界面只有原始 JSON、无恢复入口（recovery_guidance_visible 失败）；Codex reviewer 协议失败后无法回收。修复：reviewer 启动指令与 `workbench/roles/reviewer.md` 要求输出裸 JSON 并自检；门禁仍拒绝围栏输出、保留原文、不剥围栏；`gates/core.ts` 新增为同一次交付（同 task/attempt/候选）新开审查的恢复，不复用旧结论、不自动重试；问题页写明原因与下一步；经执行主控批准扩展 `panes.ts`（+8/-1）：仅“审查提交协议解析失败且该提交的 Stop 已匹配完成”时记 idle 可回收。RUN-OUTSIDE-02：idle 红/绿、两个状态变异、真实 Electron 绿态、三个门禁变异、问题页与审查集成回归均 PASS。RUN-OUTSIDE-03 真实 haiku reviewer 3 次（9/9 回合）：2 次裸 JSON 被接受，1 次仍带围栏被拒并经恢复入口处理——验收第 1 条经“被拒后界面给出恢复入口”一支成立，提示词对策 2/3 生效，残余记为 M03 模型行为。独立审查 agy PASS（两条 P3 观察）。合并 06ed64b4e。证据 `evidence/2026-10-23-batch24/T-160/RESULTS.md`。
