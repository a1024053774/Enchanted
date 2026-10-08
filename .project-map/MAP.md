# Project map

## Destination

第二阶段（2026-10-07 修订）：基于 Synara fork（`a1024053774/synara`）的 a2a 多 Agent 工作台，目标与 M1 见 [intent.md](../intent.md)，决策见 T-030～T-033。
门禁在 Synara 服务端原生实现（T-031）；`coop.py` 与 Muster 引擎冻结为参考实现。执行规格见 [synara-m1](specs/synara-m1-2026-10-07.md)；第一批：T-034、T-035、T-036 已关闭；第二批：T-037、T-038、T-039 已关闭；T-041、T-042、T-043 已关闭 → T-040（切换）。
[workbench-m1](specs/workbench-m1-2026-10-06.md) 是被取代的 GPUI/Muster 方案的日期记录；其中 T-024、T-026、T-027、T-029 已完成并保留为证据。

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
- [T-032 修订后的 M1 与层级要求](tickets/T-032-m1-revised.md): 项目 → 任务 → agent 会话；M1 六项含原生门禁、真实闭环与切换（取代 T-016）
- [T-030 工作台改为基于 Synara 的 fork](tickets/T-030-synara-fork-base.md): fork Synara v1.0.1-beta.2，原生协议会话，持续跟进上游，独立 clone（取代 T-017、T-022）
- [T-031 a2a 门禁在 Synara 中原生实现](tickets/T-031-native-gates.md): TypeScript 独立 package、唯一门禁入口、契约不变、移植场景重新证明（取代 T-018）
- [T-033 第二阶段术语修订](tickets/T-033-terms-revised.md): 门禁入口、Agent 会话、冻结的 Muster 引擎（取代 T-019）
- [T-034 Synara fork 能构建运行](tickets/T-034-synara-fork-builds.md): 入口 `a2a/scripts/bun`，缺盘即退出 2；Node 24.13.1 与缓存在外置盘；checkout 约 3.4 GiB、首次安装约 41 分钟；上游合并演练无冲突
- [T-020 构建缓存、开源许可与代码复用](tickets/T-020-build-cache-license-reuse.md): 缓存放外置盘且缺盘即报错；开源，允许 GPL，并入后整体 GPL-3.0
- [T-021 Enchanted 的搁置与并入](tickets/T-021-enchanted-freeze.md): 快照 `3e2ad91` 后冻结，功能在 M1 之后并入工作台
- [T-023 主控放在项目级还是任务级](tickets/T-023-controller-placement.md): 主控是角色不分层级，经控制接口同时操作项目级与任务级，做法沿用 Herdr
- [T-026 把构建缓存与工具链放到外置盘](tickets/T-026-external-build-cache.md): `scripts/build` 缺盘拒绝，Cargo/Zig/tmp 在外置盘；同 target 构建串行等待，按 worktree 分槽
- [T-041 provider 登录条款与 magpie 调研](tickets/T-041-provider-auth-policy.md): 不采用 magpie 的 Claude 订阅网关；保留 Synara 经 Agent SDK 启动本机官方 CLI（用户确认采用，读凭据判断登录与限额可接受），Claude 优先 API key；Codex 本地/开源用 app-server 有官方许可
- [T-024 一个引擎能否让多个窗口各看不同项目](tickets/T-024-per-window-project-focus.md): 可以，各连接焦点、尺寸与输入独立；窗口导航须走各自连接，同一任务共享 PTY 尺寸

## Not yet specified

- When and how a second CLI validates the capability contract
- Numeric budget and risk thresholds
- 持久邮箱、hook 与心跳的后续范围，根据首个闭环观察细化
- 上游测试 `ProviderCommandReactor.test.ts:7200` 在全仓运行时失败、单例通过（无 a2a 改动）；T-037 全仓顺序运行另有服务端 4 项失败（GitCore、CheckpointReactor 单例复跑通过；`CodexTextGeneration` 两项假 CLI 场景单例仍失败，文件与基线无差异，未在基线上复跑），desktop `cuaDriverHost` 用例经 T-038 基线/候选交替各 3 次，两边首轮超时、后两轮通过，判为上游不稳定用例；`workspaceUpload` 候选单跑通过；T-039 全仓运行 desktop 另 3 项失败（长 tmp 路径 EINVAL、目录清理、5 秒超时），外置盘短路径下单跑 67/67 通过，尚未定性；fork 中未跟踪的 `.grok/` 来源不明——待核实归属
- synara-m1 中尚未切片的部分：完整编排场景移植、界面上的任务窗口与人工介入记录、切换与删除 Muster/`coop.py` 运行路径

## Out of scope

- 生产发布、对外 push 和重启用户 Herdr server；本轮只做本地实现与隔离验收
- 将 F01 主控 GPT 提前结束回合归为分工协调缺陷并据此改造协调层；用户已明确将其归为模型行为，记录保留在 findings。
- Rewriting the dated research draft | reason: it is the project's initial research record.
- 基于 Zed 二次开发、从零自建 GPUI 界面 | reason: 见 T-030；T-025、T-028 以 out-of-scope 关闭。
- M1 之外的工作：对话视图、Enchanted 其他功能、远程机器、插件、Windows/Linux、元素级背景模糊、上游同步 | reason: 见 intent.md 的范围。

## Living docs

| Doc | Covers | Verified |
| --- | --- | --- |
| [CONTEXT.md](../CONTEXT.md) | `intent.md`, `coop.py` | 6656545 |
| [AGENTS.md](../AGENTS.md) | `CONTEXT.md`, `intent.md` | |
| [README.md](../README.md) | `coop.py`, `acceptance/live_muster.py`, `intent.md`, `muster/**`, `scripts/build` | |
| [findings/README.md](../findings/README.md) | `findings/*.md` | |
