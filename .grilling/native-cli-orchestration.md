---
session_id: grilling-native-cli-orchestration-20261010
status: awaiting-user
topic: 改方向：不用 Synara 统一层，原生 CLI 交互终端 + a2a 编排 + 借用 Synara 前端的轻量应用
destination_artifact: intent.md 第三阶段修订 + .project-map/specs/ 下一份新 spec + 旧 Synara 票（T-055～T-068 中未完成者）的处置清单 + 就绪 build ticket；同步 AGENTS.md、CONTEXT.md、MAP.md
created_at: 2026-10-10
last_round: 2
---

> 指针状态：`.grilling/ACTIVE.md` 于 2026-10-10 经用户同意（R1 Q5“都采纳”）改指向本账本；上一个会话 `controller-split-user-input` 已 confirmed，原样保留。

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
- D7（recommended，R1 Q1=b）：我们自己托管终端，复用 Synara 的终端实现（node-pty + xterm）。用户追问“用 zsh 不行吗？哪个终端方案好？”——zsh 是窗格里跑的 shell，不是终端宿主，见 R2 回答；终端方案待 R2 Q6 确认。
- D8（user，R1 Q2）：门禁抽出来用，契约不变，加路径检查（任务卡“允许/禁止”路径，越界打回）。
- D9（recommended，R1 Q3）：权限四层，都在应用内：角色卡；任务卡路径 + 门禁检查；每会话的 CLI 启动参数（只作用于该会话，不碰 ~/.claude、~/.codex）；收件箱命令行限定谁写哪种条目。设置页“角色权限”编辑启动参数与路径规则，默认按此。
- D10（recommended，R1 Q4）：切换条件改为：三项功能在新应用里能用 + 用户试用说“可用”；面板界面、打包格式、处置规则、提醒两路、T-057 软件内通知（并入 T-067）、T-064 设置页都换载体重做，不推翻。
- D11（recommended，R1 Q5）：T-059、T-064 后端、T-066、T-067、T-068 标 superseded；已关闭的 T-055～T-065 保留为历史；fork 只作组件来源，不再跟上游，不删；`ddb765956` 保留不推送；ACTIVE 改指向本账本（已改）。
- D12（recommended，R2 Q6）：终端组成：xterm.js 渲染、node-pty 托管、窗格里用用户的 zsh（登录 shell），在 zsh 里启动各家 CLI。D7 的待确认项由此关闭。
- D13（user，R2 Q7=a）：编排后台单独常驻（像 Herdr server），界面只是连上去看；关掉或重开界面，agent 照常跑。
- D14（recommended，R2 Q8）：状态只认各家结构化信号（Claude Code hooks、OSC 7501；Codex `notify`），拿不到的显示“未知”，不用正则匹配屏幕或标题；钩子只经本会话启动参数传入（Claude `--settings`，Codex `-c`），不改全局配置。
- D15（recommended，R2 Q9）：派发文本写入 worker 窗格并带 `⟦主控 #序号⟧` 标记、记派发日志、不算用户输入；两个主控也作为窗格跑在应用里，互相唤醒改为往对方窗格写带标记的提示；收件箱条目仍是事实来源。
- D16（user，R2 Q10=a + Electron）：新应用放在本仓库的新目录；外壳用 Electron。

## Facts

- F1（observed）：Synara 统一层的接入成本——T-055、T-058、T-061、T-064、T-066、T-068 均需改上游（provider 适配器、网关、投影）。
- F2（observed）：`packages/a2a-gates` 依赖 `@synara/contracts`、`@synara/shared/processRuntime`、`effect`、`node:sqlite`；可抽出但需替换两处 Synara 包。
- F3（observed）：Synara web 栈 React 19、Vite、Tailwind 4、TanStack Router、`@xterm/xterm`；server 有终端（node-pty）实现；desktop 为 Electron 43。
- F4（observed）：Herdr 0.9.3 有 socket API（`herdr api`）、`--session <name>` 多会话、`worktree`、`integration`、`notification` 子命令。用户正在用的 Herdr server 不得修改。
- F5（observed，文章附录）：文章的权限全靠提示词（主脑不写代码、执行者只改允许范围、审查者只读），由门禁兜底（改了禁止路径的提交被打回）；任务卡有"允许/禁止"修改边界与"唯一写入者"；门禁按风险分 personal/internal/saas 三档；AI 审查分 primary/advisor/shadow 三种角色。没有沙箱配置、审批人名单或越权上报流程。
- F6（unknown）：Herdr API 能否把 pane 输出流式给外部 GUI 渲染；Herdr 许可证。
- F7（unknown）：Codex CLI 有无"运行中/等确认/结束"的结构化信号（Claude Code 有 hooks；用户转述其 2.1.295 支持 OSC 7501，未核实）。

## Frontier

R3：Q11 数据放哪（单一 SQLite，收件箱文件退役）；Q12 一开始就支持多项目的数据模型；Q13 第一版支持哪些 CLI。

## Fog

- 额度感知调度、执行器打分、无头模式（D4 之后按需）。
- 多机/远程（文章的 herdr + mosh）。

## Out of scope

- 实现与派发 | reason: 决策会话。
- 修改用户的 Herdr server、`~/.claude`、`~/.codex` 全局配置 | reason: AGENTS.md 与用户 2026-10-09 纠正（"不是让你在Claude code和codex里改权限"）。

## Changelog

- R0（2026-10-10）：读文章与附录 01–04、07；核实 F1–F5；用户回答 Q1–Q6（D1–D6）；写 cancel 条目；建本账本。
- R1 答复（2026-10-10）：“Q1:b, 然后用 zsh 不行吗？哪个终端方案好？ / Q2:抽出来用，契约不变，加路径检查 / 3. 采纳这四层 / 4.采纳 / 5. 都采纳”。D7–D11；ACTIVE 改指向本账本。小事：用户说“1.推送 2.删掉”——已 HTTPS 推送 a2a main 到 097268b（fork 不推）；已删 /tmp 下本项目 45 个 a2a-* 夹具目录。
- R2 答复（2026-10-10）：“Q6:采纳 / Q7:a / Q8: 采纳 / Q9: 采纳 / Q10:a + Electron / 然后要删的东西删一下，左边已经回复了”。D12–D16。删除：fork 的四个旧 worktree（synara-t038、t040bc、t040bp、t045）已 `git worktree remove --force`，分支保留；内置盘可用 19G→27G。
