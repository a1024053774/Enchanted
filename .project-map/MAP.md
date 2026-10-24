# Project map

## Destination

第三阶段（2026-10-10 修订）：各家原生 CLI 以交互终端运行，a2a 只做编排、门禁与记录；工作台是本仓库里的轻量 Electron 应用，借用 Synara 的组件与样式。目标与切换条件见 [intent.md](../intent.md)，决定见 T-069～T-072，执行规格见 [native-cli-orchestration](specs/native-cli-orchestration-2026-10-10.md)；首批切片 T-073～T-075（S0、S1）已关闭；第二批为 T-076（S2 质量串与打分）、T-077（S3 worktree 与冲突）、T-078（S4 两个主控进工作台）。2026-10-14 插入门禁加固三张：T-080（验收文件受保护）、T-081（坏 worker 测试集）、T-082（reviewer 审查完成条件并做变异检查），决定见 [gate-hardening](proposals/gate-hardening-2026-10-14.md)。用户认为新工作台可用之前，日常派发仍经 Herdr。

第二阶段（2026-10-07～10-09）基于 Synara fork：原生门禁、第一次经门禁的真实派发（T-046）与三项功能的部分实现，见 [synara-m1](specs/synara-m1-2026-10-07.md)；这些是日期记录，证据只对各自的代码版本成立。[workbench-m1](specs/workbench-m1-2026-10-06.md) 是更早被取代的 GPUI/Muster 方案。

2026-10-09：主控拆为构思主控与执行主控，并定下用户输入记录与问题上报。设计见 [spec](specs/controller-split-user-input-2026-10-09.md)（决定 T-049～T-052；用户确认与委托决定见 [基线确认记录](specs/controller-split-user-input-baseline-2026-10-09.md)）；第三阶段换载体重做（T-069、T-071）。

首轮已完成：[T-006](tickets/T-006-managed-delivery.md) 受管交付、
[T-007](tickets/T-007-recovery.md) 中断恢复、[T-008](tickets/T-008-supervised-run.md) 自动运行均在 Herdr 上通过；
契约见 [managed-delivery](specs/managed-delivery-2026-10-06.md)、[recovery](specs/recovery-2026-10-06.md)、[supervised-run](specs/supervised-run-2026-10-06.md)。
这些证据只对 Herdr 运行时成立，切换后需重跑。原研究稿与 [初始设计](specs/herdr-a2a.md) 是保留的日期记录。

2026-10-21：主控与 worker 的建立方式改为 Herdr 式，见 [T-119](tickets/T-119-herdr-style-terminals-claimed-roles.md) 与 [spec](specs/herdr-style-claimed-roles-2026-10-21.md)。

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
- [T-010](tickets/T-010-descendant-session-accounting.md)、[T-011](tickets/T-011-monitor-closure.md)、[T-012](tickets/T-012-research-handoff.md)、[T-013](tickets/T-013-fixture-governance-scope.md)、[T-014](tickets/T-014-evidence-preflight.md) 早期调研票：2026-10-22 用户定关闭不做（“早期的调研票关掉”）
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
- [T-088 证据体量：大块归档到外置盘](tickets/T-088-evidence-archive-policy.md): 2026-10-16 起新批次只留文本摘要与 `*.archive.json` 清单，run/fixtures 目录、gz、sqlite、监视器日志归档到 `/Volumes/WD-Elements/a2a-evidence/`；不带校验值；缺盘报错；已提交历史不改写；落地见 T-089
- [T-097 发布前瘦身 Git 历史](tickets/T-097-slim-git-history-before-release.md): 2026-10-19 用户定"先瘦身再发布，发布后才使用"；范围 T-088 类别加 evidence/ 下大于 5 MiB 的文件，外置盘备份与归档，哈希映射表入仓库；push origin main 一次已授权；执行见 T-101
- [T-092 正常登录启动方式](tickets/T-092-normal-login-profile.md): 2026-10-17 决定：隔离 HOME 加只复制登录凭据、本地转发层逐条计数、脚本只核对事实放行由用户定、现有登录总上限 3 回合先做小复核；落地见 T-093（未就绪）
- [T-119 像 Herdr 一样的终端，认领身份加权限](tickets/T-119-herdr-style-terminals-claimed-roles.md): 用户自己在项目终端启动任意 CLI；agent 经 `a2a` 命令与自动挂上的 skill 申请角色，界面批准后生效并绑定项目；worker 由后台按主控选的 CLI 带权限参数启动（取代 D19 的 worker 只用 Codex）；规格见 [spec](specs/herdr-style-claimed-roles-2026-10-21.md)
- [T-120 不改全局配置挂上 a2a 使用说明](tickets/T-120-mount-a2a-skill-without-global-config.md): 环境变量会被用户设置盖掉；改为在终端里用 ZDOTDIR 引导，放同名的 `claude`、`codex` 包装命令，分别加 `--plugin-dir` 和 `-c developer_instructions`；`a2a help` 作为退路
- [T-125 操作员凭据的持久化位置](tickets/T-125-operator-credential-storage.md): 用户选 A——凭据放 `~/Library/Application Support/Enchanted/` 的 0600 文件，终端改用专用 socket、环境里不出现后台数据目录；接受“挡不住有意搜索磁盘的 agent”；落地见 T-126
- 输入法验证：2026-10-17 用户决定本轮不做，日后使用中发现问题再修（逐字："输入法先不做，我到时候使用的时候若发现了再修"）；T-078 的 Resolution 已记为未验证
- T-098 pane 启动延时：2026-10-18 关闭未实现——用户把 `~/.zshrc` 的 oh-my-zsh 更新模式改为 reminder 消除已知提问源，不再加延时设置；一般缺陷（前台只剩 shell≠等命令）仍在，靠启动后核对回显

## Not yet specified

- When and how a second CLI validates the capability contract
- Numeric budget and risk thresholds
- 持久邮箱、hook 与心跳的后续范围，根据首个闭环观察细化（主控之间的收件箱已由 T-052 定义，worker 侧邮箱与心跳仍待细化）
- 用户输入的抽取、含义标注与 Enchanted 消费：以后再说（用户 2026-10-09）；两个主控进入工作台后，Herdr 期做法（收件箱文件、`scripts/inbox`、`scripts/dispatch`、`scripts/session-copy`）的停用与删除，在切换 ticket 里切片
- 第三阶段 S7（切换）尚未切票：S0～S5 已切并关闭；S6 于 2026-10-22 切为 T-134（指标）、T-135（轨迹归档）、T-136（复盘），面板与记录视图补为 T-132、T-133，多 worker 为 T-131（用户 2026-10-22：“还缺的都做”）；Reflect 页（会话树、打分、复盘入口，定期复盘默认关闭）为 T-137（用户 2026-10-22 决定；当日关闭）

- 2026-10-23 客户端整体评估后的九张票（用户当日逐条裁定）：T-138 输入法错位、T-139 视图模型（项目→任务→agent 分屏）、T-140 项目额外目录（可写）、T-141 放宽受管会话限制（网络、MCP、Codex 跟随用户配置，写入范围为硬边界）、T-142 主控 `terminal_open`、T-143 终端卡顿、T-144 流程页、T-145 记录页鼠标误判、T-146 已结束仍显示运行中；T-141 关闭时须同步 AGENTS.md 的关网络与 Codex untrusted 条目
- 2026-10-23 T-155 真实使用测试后的修复票（用户裁定全部切、修完重跑）：T-157 Stop 期间输入致交付停住（F01）、T-158 修订后路径占用（F05）、T-159 分屏保留原窗格（F03）、T-160 reviewer 围栏 JSON（M03）、T-161 只读横幅与主控角色标识（F02/F07）、T-162 批准入输入记录与指标口径（F04/F06）、T-163 模型行为提示词对策（M01/M02/M04）、T-164 重跑到集成并补 Codex worker
- T-119 之后待切：主控之间、worker 与主控之间经 `a2a` 通信；在界面上编辑每个角色的边界与权限默认值（T-121、T-122 关闭后再切）

## Out of scope

- 生产发布、对外 push 和重启用户 Herdr server；本轮只做本地实现与隔离验收
- 将 F01 主控 GPT 提前结束回合归为分工协调缺陷并据此改造协调层；用户已明确将其归为模型行为，记录保留在 findings。
- Rewriting the dated research draft | reason: it is the project's initial research record.
- 基于 Zed 二次开发、从零自建 GPUI 界面 | reason: 见 intent.md 的范围（最初由 T-030 记录）；T-025、T-028 以 out-of-scope 关闭。
- 第三阶段之外：额度感知调度与水位监控、token/成本/缓存监控、无头模式、改动量上限、前端录屏、风险分档、多审查与影子审查、OCR、定期安全扫描、Claude Code 与 Codex 以外的 CLI（T-119 起按需另开票）、Windows/Linux、多机与远程、Enchanted 功能、跟进 Synara 上游 | reason: 见 intent.md 的范围与 T-069～T-072。

## Living docs

| Doc | Covers | Verified |
| --- | --- | --- |
| [CONTEXT.md](../CONTEXT.md) | `intent.md`, `acceptance/entry/a2a_gates.py` | 2876c9fd |
| [AGENTS.md](../AGENTS.md) | `CONTEXT.md`, `intent.md` | f0188d77 |
| [README.md](../README.md) | `coop.py`, `acceptance/live_muster.py`, `intent.md`, `muster/**`, `scripts/build` | 2876c9fd |
| [findings/README.md](../findings/README.md) | `findings/*.md` | 8933ee0f4 |
| [workbench/README.md](../workbench/README.md) | `workbench/src/**`, `workbench/hooks/**`, `workbench/app/**`, `workbench/package.json` | fddbc50d1 |
