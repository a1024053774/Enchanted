# Project map

## Destination

第二阶段：a2a 多 Agent 工作台，目标与 M1 见 [intent.md](../intent.md)（2026-10-06 accepted，决策见 T-016～T-021）。
工作台以 Herdr 0.9.3 引擎的硬分叉加 GPUI 界面取代 Herdr CLI；`coop.py` 的门禁保留，改接工作台的控制接口。
工作台名为 Muster（T-022）；执行规格与初步任务书见 [workbench-m1](specs/workbench-m1-2026-10-06.md)。
执行顺序：T-026，与之并行 T-024 → T-025、T-027 → T-029、T-028。

首轮已完成：[T-006](tickets/T-006-managed-delivery.md) 受管交付、
[T-007](tickets/T-007-recovery.md) 中断恢复、[T-008](tickets/T-008-supervised-run.md) 自动运行均在 Herdr 上通过；
契约见 [managed-delivery](specs/managed-delivery-2026-10-06.md)、[recovery](specs/recovery-2026-10-06.md)、[supervised-run](specs/supervised-run-2026-10-06.md)。
这些证据只对 Herdr 运行时成立，切换后需重跑。原研究稿与 [初始设计](specs/herdr-a2a.md) 是保留的日期记录。

## Notes

- [开发发现目录](../findings/README.md)：集中相关报告，分别记录 GPT 模型行为、分工协调、工程与证据处理。
- [2026-10-06 框架、实现与操作报告](../findings/herdr-a2a-2026-10-06.zh-CN.md)：中文日期报告，含命令步骤及已验证边界。
- [2026-10-06 session 复盘](../findings/a2a-session-retrospective-2026-10-06.zh-CN.md)：协调与工程发现；F01 模型提前结束回合已另列，不计入协调问题。
- [Claude / SiteCraft 实际经验](../findings/claude-sitecraft-experience-2026-10-06.zh-CN.md)：用户指定对话的日期记录，保留外部项目与 a2a 的证据边界。
- [图形客户端方向评估](../findings/gui-client-assessment-2026-10-06.zh-CN.md)：2026-10-06 日期记录；其推荐的"Herdr 客户端"路线未被采用，最终方向见 intent.md 与 [grilling ledger](../.grilling/a2a-gui-client.md)。
- Core goal: collaboration must not depend on the model continuously remembering the operating manual.
- First experiment: Codex workers in the current Herdr workflow; multi-CLI support is a later capability-contract validation, not the first success claim.
- Control rule: the Astra Max controller may dispatch and reclaim workers through Herdr (the workbench control interface after the switch) within approved scope; it must pause for major decisions or direction changes and never bypass claim, submit, acceptance, or integration gates.
- Required skills by stage: `project-map` (map/status), `reality-first-engineering` (before architecture or broad implementation), `evidence-first-testing` (behavior changes and failure evidence), `design-integrity-review` (structural-risk completion), `behavioral-acceptance-review` (acceptance/eval surfaces), and `document-writing` (project documents). Use `grilling` for decision sessions.

## Decisions so far

- [T-001 Goal and destination](tickets/T-001-goal-and-destination.md): accepted `intent.md`; the research draft remains initial input; reducing reliance on remembered collaboration procedure is the core goal
- [T-002 First experiment contract](tickets/T-002-first-experiment-contract.md): Codex/Herdr experiment targets stale or unverified result acceptance and must reject invalid state with evidence
- [T-003 Roles and evidence](tickets/T-003-roles-and-evidence.md): Astra Max controller, 6.1 xhigh Fast workers, high-reasoning read-only monitor, append-only run evidence, and exploratory claims only
- [T-004 Major-decision stop boundary](tickets/T-004-major-decision-stop-boundary.md): explicit escalation triggers; routine dispatch, status checking, policy-bounded retry, and reclaim remain autonomous
- [T-005 First seam and baseline](tickets/T-005-first-seam-and-baseline.md): 固定本地源码、真实 Herdr 入口及已有红/绿证据的分页 oracle
- [T-009 Audit recorded a2a work sessions](tickets/T-009-session-retrospective.md): 20 份 session 已扫描；F01 按用户更正另列为模型行为，T-012 仅保留研究交付范围
- [T-015 Review the specified Claude Code collaboration session](tickets/T-015-claude-session-experience.md): 指定对话已回读并整理中文经验，报告只保留中文版本
- [T-016 第二阶段目的地与 M1](tickets/T-016-phase2-destination.md): 自建类 Herdr 的 GPUI 工作台，项目窗口、任务页、pane 分工；M1 为接替 Herdr 承担 a2a 日常工作
- [T-017 工作台的技术底座](tickets/T-017-workbench-base.md): Herdr 0.9.3 引擎硬分叉加 GPUI；否决 Zed 二开、muxel fork、从头重写和跟随上游 rebase
- [T-018 运行时切换与门禁优先](tickets/T-018-runtime-switch-and-gates.md): 工作台取代 Herdr；三套验收与一次真实 run 通过后切换；界面操作受管任务只走 `coop.py`
- [T-019 第二阶段术语](tickets/T-019-phase2-terms.md): 工作台、引擎、项目、Task、Pane、原生会话写入 CONTEXT.md
- [T-020 构建缓存、开源许可与代码复用](tickets/T-020-build-cache-license-reuse.md): 缓存放外置盘且缺盘即报错；开源，允许 GPL，并入后整体 GPL-3.0
- [T-021 Enchanted 的搁置与并入](tickets/T-021-enchanted-freeze.md): 快照 `3e2ad91` 后冻结，功能在 M1 之后并入工作台
- [T-022 工作台的代码位置与正式名称](tickets/T-022-workbench-location-and-name.md): 名为 Muster，代码放在本仓库 `muster/`，命名空间前缀 `muster`/`MUSTER_`
- [T-023 主控放在项目级还是任务级](tickets/T-023-controller-placement.md): 主控是角色不分层级，经控制接口同时操作项目级与任务级，做法沿用 Herdr

## Not yet specified

- When and how a second CLI validates the capability contract
- Numeric budget and risk thresholds
- 持久邮箱、hook 与心跳的后续范围，根据首个闭环观察细化
- M1 后续切片（第一批 ticket 关闭后再切）：多项目多窗口、侧栏与状态汇总、玻璃质感与强调色、Claude Code 端到端与已装 CLI 冒烟、界面上的受管任务操作与人工介入记录、引擎名词由 workspace/tab 改为 project/task、面向 agent 的 Muster 控制指南、切换后删除 Herdr 路径

## Out of scope

- 生产发布、对外 push 和重启用户 Herdr server；本轮只做本地实现与隔离验收
- 将 F01 主控 GPT 提前结束回合归为分工协调缺陷并据此改造协调层；用户已明确将其归为模型行为，记录保留在 findings。
- Rewriting the dated research draft | reason: it is the project's initial research record.
- 基于 Zed 二次开发 | reason: NO_GO，见 T-017。
- M1 之外的工作：对话视图、Enchanted 其他功能、远程机器、插件、Windows/Linux、元素级背景模糊、上游同步 | reason: 见 intent.md 的范围。

## Living docs

| Doc | Covers | Verified |
| --- | --- | --- |
| [CONTEXT.md](../CONTEXT.md) | `intent.md`, `coop.py` | |
| [AGENTS.md](../AGENTS.md) | `.project-map/MAP.md`, `CONTEXT.md`, `intent.md` | |
| [README.md](../README.md) | `coop.py`, `acceptance/live_herdr.py`, `intent.md`, `muster/**` | |
| [findings/README.md](../findings/README.md) | `findings/*.md` | |
