---
id: T-064
title: 工作台设置里可以自己调各角色的权限，默认按已定的预设
type: build
status: open
blocked_by: [T-057, T-058]
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

用户 2026-10-09 的要求（逐字）："权限规则放在用户级设置，默认按我说的来，然后设置里也可以自己选"；随后澄清（逐字）："设置里也可以自己选，说的是权限问题"。

[T-058](T-058-server-inbox-capabilities-wake.md) 已经按 [spec](../specs/controller-split-user-input-2026-10-09.md) 第 1 节给各角色（构思主控、执行主控、worker、reviewer、monitor）做了能力预设，签发凭据时冻结。本票在工作台设置里加一页"角色权限"：

- 列出每个角色当前的能力和工具，默认值就是 T-058 的预设，并标明哪些是默认。
- 用户可以给某个角色加上或去掉能力；可以选哪些 a2a 工具免确认（例如处置工具，用户 2026-10-09 说"免确认等 057 之后"，本票就是那个入口）。
- 可以一键恢复默认。

## Acceptance

- [ ] 红态在先：父修订上设置里没有这一页，改不了预设；保存输出与重放命令。
- [ ] 设置页显示五个角色的预设，与 T-058 的预设定义逐项一致（预期从 spec 第 1 节手写，不从实现输出复制）。
- [ ] 改动生效：改了某角色的能力后，新签发的凭据按新集合冻结（T-058 的条件：改预设要重新签发凭据）；已签发的凭据不变。真实 MCP `tools/list` 与调用作证，正例、反例各一。
- [ ] 免确认：用户勾选某个 a2a 工具免确认后，受管会话、有效运行身份、活跃 turn 时不再弹权限提示；未勾选的照常提示；非受管会话、非活跃 turn 仍提示（与 T-055 的 `a2a_raise` 同口径）。
- [ ] 结构底线不被设置页突破：`dismiss` 仍只有用户能做，主控仍不能关闭 blocking 问题；设置页不提供这两项的开关。
- [ ] 每次修改记成一条用户输入（形态 `action`，渠道为设置页），并追加一条可读的变更记录（谁、何时、改了什么、改前改后）；恢复默认也记。
- [ ] 没有自定义时，行为与 T-058 完全一致（反例证明）。
- [ ] 既有套件、typecheck、lint 通过；对上游文件的改动列清单。

## 说明

- 失败方式清单（处理方式写进 RESULTS）：两个窗口同时改同一角色；改到一半应用退出；自定义里出现已不存在的能力名；把某角色的能力全部去掉；正在运行的会话遇到预设变化。
- 与 T-057、T-058 改同一批文件时，同一文件同一时间只能有一个写入者，由执行主控串行安排。
- 这是用户要求的功能，用户试用、说"可用"之前须完成（见 AGENTS.md 切换条件与用户"不要延后"的要求）。
- 范围澄清（用户 2026-10-09，逐字）："我要的是synara软件层面的，不是让你在Claude code和codex里改权限ok？"。本票只改 Synara 工作台自己的设置与凭据签发，不读写 Claude Code、Codex 的权限配置。
- 授权来源：`ready_by: ideation`，`ready_rev: 1`，用户原话见上。范围的具体化（设置页的内容、免确认入口）是构思主控按用户原话做的解释，用户可以修订。

## Resolution

2026-10-10，worker `t064` 依据主控 #22 和 ready_rev 1：**BLOCKED，待主控批准上游接入，保持 open，待主控关闭**。

fork 基线 `7a3a13249e562bf2d7f9ff4cb024f39b13d62434`，尚未修改产品源码或提交 fork。实际设置导航经 Vite resolver 加载，没有“角色权限”，合同探针退出 1，原输出与重放命令已保存。共享权限 matcher 缺少会话/凭据上下文，具体上游接入及免确认默认/生效时点需确认；已上报 `20261010T064912Z-worker:t064-issue-001`。

见 [报告](../../evidence/2026-10-09-batch11/T-064/RESULTS.md) 和 [待批清单](../../evidence/2026-10-09-batch11/T-064/needs-decision-01.md)。完整 MCP、权限正反例、截图、产品检查、独立审查均未运行；本票验收框不勾选，未用旧候选结论替代本票证据。

2026-10-10，主控 #23 批准后继续：fork 实现提交 `0bf4bb2cab2216f567df2d4fb1729bee3cac6fe9`；五角色设置、真实 MCP 能力变化/冻结、Codex/Claude 免确认正反例、原子 action/审计、CAS、空集合、无效配置、真实中断、UI 保存/恢复和既有 35 项端到端通过，typecheck/fmt/lint、服务端相关 365 项、gates 19 项通过。**INCOMPLETE：等待唯一一次独立审查；保持 open，待主控关闭。** 其它 provider 按批准范围未适配免确认，外观待用户判断。新证据与局限见本票 RESULTS；原 BLOCKED 与失败现场保留。

最终交接：**INCOMPLETE，保持 open，待主控关闭**。唯一一次独立审查目标 `0bf4bb2ca` + a2a `10718bd2c77b375c3b5fdde3930ba75109400d7e`，结论 INCOMPLETE：缺实际 Codex/Claude 进程发出并消费权限请求的证据，未把受控 I/O 或 CLI 方法可用性当作完整边界通过。上报 `20261010T073006Z-worker:t064-issue-001`，待主控决定验证入口/预算/认证。

实施者随后保留红态并修复默认 Claude override 误影响 Auto、operate 遮蔽 stop 两项回归；最终 fork `49cae984f22924de006e0f8358cb447eb881aaf6`。实际 MCP 组合红绿、旧 tools 投影反例、final27 全 API、final28 原有 35 场景、369 项相关测试及静态检查通过；UI 源码在 7c04 修正默认说明后经真实 UI 验证，其后只改 stop 投影。未第二次审查、未关闭整票、未用旧审查上调最终候选。完整版本与局限见 RESULTS，原始证据保留。

主控 #24 / 决定 02 补证完成：**PASS（worker 执行结论，限批准范围；保持 open，待主控关闭）**。生产代码仍为已提交的 fork `49cae984f22924de006e0f8358cb447eb881aaf6`。真实 Codex app-server 最终两个 turn（加首次两次，共 4/4；固定 CLI、模型、Fast 请求，启动器核对实际 CODEX_HOME 在 /tmp）和真实 Claude CLI + Synara adapter + 本机假 Messages API，均取得 checked raise 实际成功、unchecked submit 实际待批准请求；同一不读取驱动 verdict 的外部断言分别对好候选退出 0、坏候选退出 1。首次认证来源在 /tmp、实际 native overlay 却在外置盘的缺项已保留、上报、修正夹具后用剩余预算复验。认证副本、来源/native home 与旧 overlay 已删除，服务已停，归档排除秘密。

RESULTS 补入其他角色被授予 stop 后核心按 ideation 地址记录的实际 MCP/核心事件；明确核心 thread 为目标，caller 由凭据绑定、未另存该事件。另上报 native interrupted 与最终 completed 投影分歧，未修范围外编排模块，不宣称整个中断链路通过。唯一独立审查的历史 INCOMPLETE 未改判，遵从决定 02 不开第二次审查，新增证据交执行主控自审。准备失败和原 INCOMPLETE 报告全部保留，Acceptance 勾选与关闭留给主控。
