---
session_id: grilling-native-cli-orchestration-20261010
status: awaiting-user
topic: 改方向：不用 Synara 统一层，原生 CLI 交互终端 + a2a 编排 + 借用 Synara 前端的轻量应用
destination_artifact: intent.md 第三阶段修订 + .project-map/specs/ 下一份新 spec + 旧 Synara 票（T-055～T-068 中未完成者）的处置清单 + 就绪 build ticket；同步 AGENTS.md、CONTEXT.md、MAP.md
created_at: 2026-10-10
last_round: 0
---

> 指针状态：`.grilling/ACTIVE.md` 仍指向已 confirmed 的 `controller-split-user-input.md`；改指向本账本需用户同意（R1 Q5）。

## Destination

定下新方向并写成文档：工作台不再基于 Synara 的统一层，改为各家原生 CLI 以交互终端运行、a2a 只做编排，前端是借用 Synara 组件与样式的新轻量应用；把已定的三项功能（用户输入记录、两层主控、问题上报）搬到新载体；吸收文章《将军赶路不追小兔》里的好思路，包括权限管理。确认后交接：新 spec、就绪 ticket、旧票标 superseded。不实现。

> "我觉得不用 Synara的统一网关，只用 synara 这种前端样式框架就行，里面具体的 cli 还是看每家自己的能力，我们只做编排，像 herdr 这样。"（2026-10-10）
>
> "5.文章里好的思路我们借鉴，我没细看，但里面也有权限管理这些吧，和我们现在做的结合一下。"（2026-10-10，R0 回答）
>
> 切换条件仍沿用用户 2026-10-09 原话："肯定要把我提的功能至少都做的能用了，我才能到 Synara 里用啊"

## Decisions so far

- D1（user，R0 Q1=A）：不用 Synara 包装各家 CLI 的 provider 层，也不用它给 agent 的 MCP 网关；agent 以各家原生 CLI 的终端界面运行。
- D2（user，R0 Q2=B）：前端新建轻量应用，借用 Synara 的前端组件与样式（MIT），不继续删改 fork。
- D3（user，R0 Q3=停止）：T-059、T-066、T-068 停止；已写 `20261010T153340Z-ideation-cancel-001`。T-067 一并不动，去留由本会话定。
- D4（user，R0 Q4）：执行层用交互终端，不用无头模式。
- D5（user，R0 Q5）：借鉴文章的好思路，含权限管理，与现有设计结合。
- D6（user，R0 Q6=等）：T-068 等方向定；按 D1 预计作废。

## Facts

- F1（observed）：Synara 统一层的接入成本——T-055、T-058、T-061、T-064、T-066、T-068 均需改上游（provider 适配器、网关、投影）。
- F2（observed）：`packages/a2a-gates` 依赖 `@synara/contracts`、`@synara/shared/processRuntime`、`effect`、`node:sqlite`；可抽出但需替换两处 Synara 包。
- F3（observed）：Synara web 栈 React 19、Vite、Tailwind 4、TanStack Router、`@xterm/xterm`；server 有终端（node-pty）实现；desktop 为 Electron 43。
- F4（observed）：Herdr 0.9.3 有 socket API（`herdr api`）、`--session <name>` 多会话、`worktree`、`integration`、`notification` 子命令。用户正在用的 Herdr server 不得修改。
- F5（observed，文章附录）：文章的权限全靠提示词（主脑不写代码、执行者只改允许范围、审查者只读），由门禁兜底（改了禁止路径的提交被打回）；任务卡有"允许/禁止"修改边界与"唯一写入者"；门禁按风险分 personal/internal/saas 三档；AI 审查分 primary/advisor/shadow 三种角色。没有沙箱配置、审批人名单或越权上报流程。
- F6（unknown）：Herdr API 能否把 pane 输出流式给外部 GUI 渲染；Herdr 许可证。
- F7（unknown）：Codex CLI 有无"运行中/等确认/结束"的结构化信号（Claude Code 有 hooks；用户转述其 2.1.295 支持 OSC 7501，未核实）。

## Frontier

R1 Q1–Q5 见对话（终端宿主、门禁去留、权限结合、切换条件与旧功能搬迁、旧票与 fork 处置及 ACTIVE 指针）。

## Fog

- 额度感知调度、执行器打分、无头模式（D4 之后按需）。
- 多机/远程（文章的 herdr + mosh）。

## Out of scope

- 实现与派发 | reason: 决策会话。
- 修改用户的 Herdr server、`~/.claude`、`~/.codex` 全局配置 | reason: AGENTS.md 与用户 2026-10-09 纠正（"不是让你在Claude code和codex里改权限"）。

## Changelog

- R0（2026-10-10）：读文章与附录 01–04、07；核实 F1–F5；用户回答 Q1–Q6（D1–D6）；写 cancel 条目；建本账本。
