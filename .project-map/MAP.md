# Project map

## Destination

首轮已排定范围完成：[T-006](tickets/T-006-managed-delivery.md) 受管交付、
[T-007](tickets/T-007-recovery.md) 中断恢复、[T-008](tickets/T-008-supervised-run.md) 自动运行均通过。
方向由 [intent.md](../intent.md) 固定，
执行契约见 [managed-delivery](specs/managed-delivery-2026-10-06.md)。
恢复契约见 [recovery](specs/recovery-2026-10-06.md)，当前契约见 [supervised-run](specs/supervised-run-2026-10-06.md)。
原研究稿与 [初始设计](specs/herdr-a2a.md) 是保留的日期记录。

## Notes

- [开发发现目录](../findings/README.md)：集中相关报告，分别记录 GPT 模型行为、分工协调、工程与证据处理。
- [2026-10-06 框架、实现与操作报告](../findings/herdr-a2a-2026-10-06.zh-CN.md)：日期记录，含 STE 简明英文对照、命令步骤及已验证边界。
- [2026-10-06 session 复盘](../findings/a2a-session-retrospective-2026-10-06.zh-CN.md)：协调与工程发现；F01 模型提前结束回合已另列，不计入协调问题。
- Core goal: collaboration must not depend on the model continuously remembering the operating manual.
- First experiment: Codex workers in the current Herdr workflow; multi-CLI support is a later capability-contract validation, not the first success claim.
- Control rule: the Astra Max controller may dispatch and reclaim workers through Herdr within approved scope; it must pause for major decisions or direction changes and never bypass claim, submit, acceptance, or integration gates.
- Required skills by stage: `project-map` (map/status), `reality-first-engineering` (before architecture or broad implementation), `evidence-first-testing` (behavior changes and failure evidence), `design-integrity-review` (structural-risk completion), `behavioral-acceptance-review` (acceptance/eval surfaces), and `document-writing` (project documents). Use `grilling` for decision sessions.

## Decisions so far

- [T-001 Goal and destination](tickets/T-001-goal-and-destination.md): accepted `intent.md`; the research draft remains initial input; reducing reliance on remembered collaboration procedure is the core goal
- [T-002 First experiment contract](tickets/T-002-first-experiment-contract.md): Codex/Herdr experiment targets stale or unverified result acceptance and must reject invalid state with evidence
- [T-003 Roles and evidence](tickets/T-003-roles-and-evidence.md): Astra Max controller, 6.1 xhigh Fast workers, high-reasoning read-only monitor, append-only run evidence, and exploratory claims only
- [T-004 Major-decision stop boundary](tickets/T-004-major-decision-stop-boundary.md): explicit escalation triggers; routine dispatch, status checking, policy-bounded retry, and reclaim remain autonomous
- [T-005 First seam and baseline](tickets/T-005-first-seam-and-baseline.md): 固定本地源码、真实 Herdr 入口及已有红/绿证据的分页 oracle
- [T-009 Audit recorded a2a work sessions](tickets/T-009-session-retrospective.md): 20 份 session 已扫描；F01 按用户更正另列为模型行为，T-012 仅保留研究交付范围

## Not yet specified

- When and how a second CLI validates the capability contract
- Numeric budget and risk thresholds
- 持久邮箱、hook 与心跳的后续范围，根据首个闭环观察细化

## Out of scope

- 生产发布、对外 push 和重启用户 Herdr server；本轮只做本地实现与隔离验收
- 将 F01 主控 GPT 提前结束回合归为分工协调缺陷并据此改造协调层；用户已明确将其归为模型行为，记录保留在 findings。
- Rewriting the dated research draft | reason: it is the project's initial research record.

## Living docs

| Doc | Covers | Verified |
| --- | --- | --- |
| [CONTEXT.md](../CONTEXT.md) | `intent.md`, `coop.py` | |
| [AGENTS.md](../AGENTS.md) | `.project-map/MAP.md`, `CONTEXT.md` | |
| [README.md](../README.md) | `coop.py`, `acceptance/live_herdr.py` | |
| [findings/README.md](../findings/README.md) | `findings/*.md` | |
