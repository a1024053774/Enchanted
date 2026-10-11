# Project map

## Destination

第三阶段（2026-10-10 修订）：各家原生 CLI 以交互终端运行，a2a 只做编排、门禁与记录；工作台是本仓库里的轻量 Electron 应用，借用 Synara 的组件与样式。目标与切换条件见 [intent.md](../intent.md)，决定见 T-069～T-072，执行规格见 [native-cli-orchestration](specs/native-cli-orchestration-2026-10-10.md)；首批切片已切为 T-073（S0 Herdr 期三样）、T-074（S1 第 0 步：R6、R7 事实核实）、T-075（S1 tracer bullet，依赖 T-074）。用户认为新工作台可用之前，日常派发仍经 Herdr。

第二阶段（2026-10-07～10-09）基于 Synara fork：原生门禁、第一次经门禁的真实派发（T-046）与三项功能的部分实现，见 [synara-m1](specs/synara-m1-2026-10-07.md)；这些是日期记录，证据只对各自的代码版本成立。[workbench-m1](specs/workbench-m1-2026-10-06.md) 是更早被取代的 GPUI/Muster 方案。

2026-10-09：主控拆为构思主控与执行主控，并定下用户输入记录与问题上报。设计见 [spec](specs/controller-split-user-input-2026-10-09.md)（决定 T-049～T-052；用户确认与委托决定见 [基线确认记录](specs/controller-split-user-input-baseline-2026-10-09.md)）；第三阶段换载体重做（T-069、T-071）。

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
- `.project-map/inbox/` 是构思主控与执行主控之间的追加式收件箱（Herdr 期），`.project-map/roles/` 是各角色的角色卡；它们不是 ticket，格式见 [spec](specs/controller-split-user-input-2026-10-09.md) 第 5 节。
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
- [T-032 修订后的 M1 与层级要求](tickets/T-032-m1-revised.md): 项目 → 任务 → agent 会话（沿用）；M1 六项由 T-069 的切换条件取代（取代 T-016）
- [T-030 工作台改为基于 Synara 的 fork](tickets/T-030-synara-fork-base.md): superseded by [T-069](tickets/T-069-third-stage-direction.md)（2026-10-10）
- [T-031 a2a 门禁在 Synara 中原生实现](tickets/T-031-native-gates.md): superseded by [T-070](tickets/T-070-gates-task-cards-quality.md)（2026-10-10）
- [T-033 第二阶段术语修订](tickets/T-033-terms-revised.md): 门禁入口、Agent 会话、冻结的 Muster 引擎（取代 T-019）
- [T-034 Synara fork 能构建运行](tickets/T-034-synara-fork-builds.md): 入口 `a2a/scripts/bun`，缺盘即退出 2；Node 24.13.1 与缓存在外置盘；checkout 约 3.4 GiB、首次安装约 41 分钟；上游合并演练无冲突
- [T-020 构建缓存、开源许可与代码复用](tickets/T-020-build-cache-license-reuse.md): 缓存放外置盘且缺盘即报错；开源，允许 GPL，并入后整体 GPL-3.0
- [T-021 Enchanted 的搁置与并入](tickets/T-021-enchanted-freeze.md): 快照 `3e2ad91` 后冻结，功能在 M1 之后并入工作台
- [T-023 主控放在项目级还是任务级](tickets/T-023-controller-placement.md): 主控是角色不分层级，经控制接口同时操作项目级与任务级，做法沿用 Herdr
- [T-026 把构建缓存与工具链放到外置盘](tickets/T-026-external-build-cache.md): `scripts/build` 缺盘拒绝，Cargo/Zig/tmp 在外置盘；同 target 构建串行等待，按 worktree 分槽
- [T-041 provider 登录条款与 magpie 调研](tickets/T-041-provider-auth-policy.md): 不采用 magpie 的 Claude 订阅网关；保留 Synara 经 Agent SDK 启动本机官方 CLI（用户确认采用，读凭据判断登录与限额可接受），Claude 优先 API key；Codex 本地/开源用 app-server 有官方许可
- [T-024 一个引擎能否让多个窗口各看不同项目](tickets/T-024-per-window-project-focus.md): 可以，各连接焦点、尺寸与输入独立；窗口导航须走各自连接，同一任务共享 PTY 尺寸
- [T-049 构思主控与执行主控的分工、层级与权限](tickets/T-049-controller-roles-and-permissions.md): 用户 ⇄ 构思主控 → 执行主控 → worker；提示词为主，不做策略引擎；执行主控在 T-004 边界内可自建缺陷级 ticket；第三阶段权限改为四层（T-071）
- [T-050 用户输入记录：类型、存放、与人工介入的关系、过渡期](tickets/T-050-user-input-records.md): 形态与含义两层，含义判断不用正则；服务端追加式表，人工介入改为派生事件，仅受管 attempt fail-closed；Herdr 期靠派发包装、日志与会话副本
- [T-051 问题上报与面板：语义、处置、发送](tickets/T-051-issue-reports-and-panel.md): 默认不阻塞；每会话一个面板，逐个或打包发送；主控可判断并关闭但不删除，拿不准留给用户
- [T-052 主控交接协议：就绪、收件箱、唤醒、完成报告、紧急停止](tickets/T-052-controller-handoff-protocol.md): `ready` 字段加追加式收件箱，跨会话消息唤醒；完成报告逐字报状态；紧急停止分层，限时 break-glass
- [T-069 第三阶段方向：原生 CLI 编排与 a2a 自己的工作台](tickets/T-069-third-stage-direction.md): 原生 CLI 交互终端、a2a 只做编排；本仓库 Electron 工作台借用 Synara 组件；编排后台常驻；先支持 Claude Code 与 Codex；切换条件含第三阶段全部新功能与用户试用
- [T-070 门禁、任务卡与质量保障](tickets/T-070-gates-task-cards-quality.md): 提示词管判断、脚本管事实；门禁抽进编排后台；任务卡；统一检查串与独立审查；worktree 命名、清理与冲突；集成落到项目工作分支
- [T-071 权限、状态信号、派发唤醒、数据与主控提问](tickets/T-071-permissions-signals-dispatch-data.md): 权限四层；只认结构化状态信号；派发与唤醒写进窗格；唯一 SQLite 库；面板收主控提问
- [T-072 提交追溯、验收打分、复盘与指标](tickets/T-072-traceability-scoring-retrospective-metrics.md): `A2A-*` 尾注；每个 attempt 结束随验收命令打分；手动或定期复盘；原始事件全记、四个指标视图；Herdr 期先用三样

## Not yet specified

- When and how a second CLI validates the capability contract
- Numeric budget and risk thresholds
- 持久邮箱、hook 与心跳的后续范围，根据首个闭环观察细化（主控之间的收件箱已由 T-052 定义，worker 侧邮箱与心跳仍待细化）
- 用户输入的抽取、含义标注与 Enchanted 消费：以后再说（用户 2026-10-09）；两个主控进入工作台后，Herdr 期做法（收件箱文件、`scripts/inbox`、`scripts/dispatch`、`scripts/session-copy`）的停用与删除，在切换 ticket 里切片
- 第三阶段 S0～S7 尚未切票：切片建议见 [spec 第 12 节](specs/native-cli-orchestration-2026-10-10.md#12-切片建议)，构思主控先切 S0、S1

## Out of scope

- 生产发布、对外 push 和重启用户 Herdr server；本轮只做本地实现与隔离验收
- 将 F01 主控 GPT 提前结束回合归为分工协调缺陷并据此改造协调层；用户已明确将其归为模型行为，记录保留在 findings。
- Rewriting the dated research draft | reason: it is the project's initial research record.
- 基于 Zed 二次开发、从零自建 GPUI 界面 | reason: 见 intent.md 的范围（最初由 T-030 记录）；T-025、T-028 以 out-of-scope 关闭。
- 第三阶段之外：额度感知调度与水位监控、token/成本/缓存监控、无头模式、改动量上限、前端录屏、风险分档、多审查与影子审查、OCR、定期安全扫描、Claude Code 与 Codex 以外的 CLI、Windows/Linux、多机与远程、Enchanted 功能、跟进 Synara 上游 | reason: 见 intent.md 的范围与 T-069～T-072。

## Living docs

| Doc | Covers | Verified |
| --- | --- | --- |
| [CONTEXT.md](../CONTEXT.md) | `intent.md`, `acceptance/entry/a2a_gates.py` | 5fb7009 |
| [AGENTS.md](../AGENTS.md) | `CONTEXT.md`, `intent.md` | c94d388 |
| [README.md](../README.md) | `coop.py`, `acceptance/live_muster.py`, `intent.md`, `muster/**`, `scripts/build` | |
| [findings/README.md](../findings/README.md) | `findings/*.md` | |
| [workbench/README.md](../workbench/README.md) | `workbench/src/**`, `workbench/hooks/**` | 7c4bf88 |
