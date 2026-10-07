---
session_id: grilling-synara-fork-20261007
status: confirmed
topic: synara-fork
destination_artifact: intent.md
created_at: 2026-10-07T10:30:35-04:00
updated_at: 2026-10-07T10:30:35-04:00
last_round: 5
---

## Destination

修订 `intent.md` 的第二阶段：放弃从零自建 GPUI 界面，改为 fork Synara，在其上继续做 a2a 与 Enchanted；同步项目地图，标明被取代的决定与 ticket。

> "我说白了，codex做的UI屎的不行，我真受不了。我现在想到，咱们从0做UI还是不现实，简直灾难。所以咱们复用https://github.com/Emanuele-web04/synara的仓库吧，在他的仓库上fork然后继续做我们想要的a2a以及enchanted。刚好他今天发布了Synara v1.0.1-beta.2版本。"

## Out of scope

- 实现、fork 操作、构建与发布 | reason: grilling 只做决定并交接。

## Confirmed constraints

- C1 | state: confirmed | source: 本轮用户原话 | 不再从零自建界面；基于 Synara 的 fork 继续 a2a 与 Enchanted。

## Decisions so far

- D1 | confirmed | compare | origin: recommended | round 1 Q1 | agent 以 Synara 的原生协议会话为主（Codex app-server、Claude Agent SDK、ACP、OpenCode SDK），终端 pane 为辅。 | assumes: 项目→任务→多 agent 分工可映射到 Synara 的项目、thread、split views | rejected: (b) Synara 界面+Muster 引擎（接两套运行模型，改动最深）；(c) 只用 Synara 终端（放弃其核心价值） | 取代 a2a-gui-client 的 C1、D1。
- D2 | confirmed | decide | origin: recommended | round 1 Q2 | 持续跟进上游：我们的功能做成独立模块、少量核心补丁、定期合并上游，通用修复回馈作者。 | rejected: 硬分叉。
- D3 | confirmed | decide | origin: recommended | round 1 Q3 | 代码放在独立 GitHub fork（a1024053774/synara），单独 clone；a2a 仓库保留规范、coop.py、门禁与证据。 | 取代 T-022 的"代码在 a2a 文件夹下"。
- D4 | confirmed | decide | origin: recommended | round 1 Q4 | 从 v1.0.1-beta.2 fork。
- D5 | confirmed | decide | origin: user | round 2 Q5 | 门禁原生化：在 Synara 服务端用 TypeScript 重写 a2a 门禁；coop.py 与 Muster 冻结为参考实现。用户原话："我建议选B，你觉得呢？这是为长远考虑，最好原生。" | rejected: agent 推荐的 (a)（保留 coop.py 为唯一门禁实现）。附加条件见 Q9。
- D6 | confirmed | decide | origin: recommended | round 2 Q6 | Enchanted 在 a2a 门禁接入 Synara 之后再并入；并入方式待重叠调研。
- D7 | confirmed | decide | origin: recommended | round 2 Q7（"先按此来"） | 被取代：T-017、T-022；T-016、T-019 中的 GPUI/Muster.app 部分；T-025、T-028 以 out-of-scope 关闭（保留录屏与探针证据）；intent 与 spec 中的 gpui-kit、窗口级玻璃移除，视觉目标改为 Synara 自身的界面。
- D9 | confirmed | decide | origin: recommended | round 3 Q9（"可以"） | D5 附加条件：契约不变；重新证明（外部门禁入口 + 移植 8/9/18 场景、红绿与反例）；门禁为独立 package；coop.py 与 Muster 冻结，新门禁通过同样验收后删除 Muster；AGENTS 改为"唯一门禁入口、同样锁语义"。
- D10 | confirmed | decide | origin: user（修改推荐） | round 3 Q10 | M1 六项：fork 能跑起来（含缓存测量与上游合并演练）；项目→任务→agent 层级（一个项目多个任务、一个任务多个 agent，缺则在 fork 中补模块，"任务窗口"指应用内区域）；原生门禁与移植场景；真实闭环；界面显示门禁状态；切换后删除 Muster/coop.py 运行路径。用户原话："反正就是要项目 任务 agent 这样的层级展开，一个项目里可以有多个任务窗口，一个任务窗口里可以有多个agent" | rejected: 推荐中"先用 Synara 现有布局、以后再评估"的假设。
- D8 | confirmed | decide | origin: recommended | round 2 Q8 | fork 的 checkout 放内置盘；Bun 全局缓存与 Electron 下载放外置盘；首个任务实测内置盘占用与安装、dev server 启动耗时。

## Facts

- F1 | observed | gh api，2026-10-07 | Synara：MIT；2,056 star、317 fork；当天仍有推送；v1.0.1-beta.2（预发布，2026-10-07 01:28 UTC）、v1.0.1-beta.1、v1.0.0（正式，2026-10-05）。
- F2 | observed | apps/{desktop,marketing,server,web}、packages/{contracts,shared}；Bun + Turbo 单仓。
- F3 | observed | server 依赖 `@anthropic-ai/claude-agent-sdk`、`@agentclientprotocol/sdk`、`@opencode-ai/sdk`、`node-pty`、`@xterm/headless`，并有 codexAppServerManager：agent 主要经各家原生协议（Codex app-server、Claude Agent SDK、ACP、OpenCode SDK）驱动，另有 node-pty 终端。
- F4 | observed | web：React 19、TanStack Router/Query/Virtual、Base UI、xterm 6（WebGL）、Lexical、react-markdown。
- F5 | observed | 用户录屏（2026-10-07 10:24，抽帧）：T-025 探针中拼音、emoji、粘贴可用；玻璃质感几乎不可见，界面朴素；用户判定不可接受。
- F7 | observed | Synara 文档 organize.mdx、thread-goals.mdx、automations.mdx、workspace-editor.mdx | 已有：split views（可跨项目并排）、任务的 Local/Worktree checkout、agent 间消息、thread goals（持久目标、可自动续跑）、Automations、Studio、Profile/用量统计。
- F8 | inferred | apps/server/src/agentGateway（bearerToken、approvalGate、automationTools、completionDelivery 等） | 存在供 agent/外部调用的网关；是否足够让 coop.py 创建任务、投递 prompt、读取状态，unknown，需核实。
- F6 | observed | 已完成：T-027 Muster 引擎（Herdr 硬分叉）、T-029 coop.py 改接 Muster；进行中：T-025（GPUI 探针）；未开始：T-028（GPUI Muster.app）。

## Frontier

- （无）

## Blocked

- （无）

## Not yet specified

- 无（Enchanted 重叠调研属于 M1 之后，已列入 intent 的事实表与范围）。


## Risks and conflicts

- R1 | resolved（D1） | 冲突：Synara 以原生协议驱动 agent（F3），与旧 ledger 已确认的"agent 仍以各自 CLI 运行在终端 pane 中，不改用 provider 原生协议驱动"（a2a-gui-client C1、D1）冲突 → Q1
- R2 | resolved（D7、T-030～T-033） | 冲突：fork Synara（Electron/React）取代 GPUI 与"Herdr 引擎 + GPUI"（T-017、D8）；评估中的路线 D 当时被否决 → 本轮 C1 已表明用户改变方向，待 Q1～Q5 落定后标记 superseded
- R3 | accepted（D2，持续跟进上游） | Synara 迭代极快（F1），fork 的同步成本 → Q2

## Handoff

已确认（用户："确认，按草案落地，然后 fork 并推送"）。canonical artifact 为根目录 [`intent.md`](../intent.md)（2026-10-07 accepted）；草案已并入并删除。CONTEXT、AGENTS、README、项目地图已更新；决策 ticket T-030～T-033 关闭并取代 T-016～T-019、T-022；T-025、T-028 以 out-of-scope 关闭。下一步：在 project-map 中写基于 Synara 的 M1 spec（fork 与同步流程、构建缓存、层级模型、门禁 package 的边界与入口、移植场景），再切 tracer-bullet build ticket。本 ledger 不记录实现进度。

## Changelog

- Round 1: 用户要求 fork Synara；核实 F1～F6；提出 Q1～Q4。
- Round 2: 用户全部采纳推荐（D1～D4）；核实 F7～F8；提出 Q5～Q8。
- Round 3: Q5 用户改选 B（D5，原生门禁）；Q6～Q8 采纳推荐（D6～D8）；提出 Q9（D5 附加条件）。
- Round 4: Q9 接受（D9）；Q10 用户补充层级要求（D10）。frontier 清空；起草 intent 草案，做漂移检查。
- Round 5: 用户确认漂移检查与草案；落地并交接。
