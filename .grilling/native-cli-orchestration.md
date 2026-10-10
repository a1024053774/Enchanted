---
session_id: grilling-native-cli-orchestration-20261010
status: awaiting-user
topic: 改方向：不用 Synara 统一层，原生 CLI 交互终端 + a2a 编排 + 借用 Synara 前端的轻量应用
destination_artifact: intent.md 第三阶段修订 + .project-map/specs/ 下一份新 spec + 旧 Synara 票（T-055～T-068 中未完成者）的处置清单 + 就绪 build ticket；同步 AGENTS.md、CONTEXT.md、MAP.md
created_at: 2026-10-10
updated_at: 2026-10-10
last_round: 4
---

> 指针状态：`.grilling/ACTIVE.md` 于 2026-10-10 经用户同意（R1 Q5“都采纳”）改指向本账本；上一个会话 `controller-split-user-input` 已 confirmed，原样保留。

## Destination

定下新方向并写成文档：工作台不再基于 Synara 的统一层，改为各家原生 CLI 以交互终端运行、a2a 只做编排，前端是借用 Synara 组件与样式的新轻量应用；把已定的三项功能（用户输入记录、两层主控、问题上报）搬到新载体；吸收文章《将军赶路不追小兔》里的好思路，包括权限管理。确认后交接：新 spec、就绪 ticket、旧票标 superseded。不实现。

> "我觉得不用 Synara的统一网关，只用 synara 这种前端样式框架就行，里面具体的 cli 还是看每家自己的能力，我们只做编排，像 herdr 这样。"（2026-10-10）
>
> "5.文章里好的思路我们借鉴，我没细看，但里面也有权限管理这些吧，和我们现在做的结合一下。"（2026-10-10，R0 回答）
>
> 切换条件仍沿用用户 2026-10-09 原话："肯定要把我提的功能至少都做的能用了，我才能到 Synara 里用啊"

R4 起（新会话"新思路构思"）借鉴范围补充为：任务卡与提交追溯、质量保障与写审分开、并行 worktree、构思主控的提问进面板、复盘与指标，见 C1–C10。

## Confirmed constraints

用户在 R4 输入中直接定下（2026-10-10，新会话"新思路构思"；引号内为用户原话）：

- C1 | confirmed | source: R4 输入 | 任务卡与追溯，"提示词 + 脚本"混合。用户以"关于这两点："引出文章原文："第三，我需要完整的任务追踪和复盘能力。每个任务有标准化的任务卡模板（目标、修改边界、验收条件），每次代码提交都能追溯到是哪个执行器、什么模型干的。""能用脚本保证的事情，就不要只靠提示词。" | 落地见 Q14、Q15、Q19
- C2 | confirmed | source: R4 输入 | "然后额度水位监控这个先不做。" | 留在 fog
- C3 | confirmed | source: R4 输入 | "然后还有并行 worktree：统一的命名规范、完成后自动清理、冲突自动处理。" | 落地见 Q18；与冻结契约、intent 的冲突见 R1、R2
- C4 | confirmed | source: R4 输入 | "然后就是文章中质量保证那一节。" | 落地见 Q16
- C5 | confirmed | source: R4 输入 | "然后其实写代码和审查者也要是两个 agent，比如两个干净上下文的 codex 对话。""门禁不能省、写和审必须分开" | 落地见 Q16、Q17
- C6 | confirmed | source: R4 输入 | "还有我之前说的单独面板这个能做吗？比如构思主控需要一些我回复的问题的时候，可以把这些问题放到面板上来？我回复完再传回去，这个方式我之前应该说过，批量和逐个这些。" | 复用 controller-split 的 C6、D3、D24；落地见 Q20
- C7 | confirmed | source: R4 输入 | "我可以设置一个周期或者手动启动最近工作记录的复盘，也就是文章中的周期性复盘这一章，然后可以选择用哪个cli，哪个模型，哪个思考强度来执行。" | 落地见 Q22
- C8 | confirmed | source: R4 输入 | "检测指标可以为以后的 enchanted 做一些地基，还有复盘的轨迹数据，但是 token 监控我觉得没必要做了，重复造轮子，可以想一些其他为我的系统自进化埋一些检测指标。比如按项目看，该项目下每个任务用了哪些模型，做一个分类。"（用户已用 TokenTracker 看 token 用量） | 落地见 Q23
- C9 | confirmed | source: R4 输入 | "每一次代码提交都应该能追溯到：见文章的7." | D20 由此改为用户确认；机制见 Q19
- C10 | confirmed | source: R4 输入 | "主脑给执行层打分 这个也可以。" | 从 fog 移出；落地见 Q21

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
- D17（recommended，R3 Q11）：用户输入、问题上报、收件箱、门禁都放常驻后台的同一个 SQLite 库，只追加；`scripts/inbox` 改为后台的命令行客户端；`.project-map/inbox/` 文件在切换当天退役，不双写；切换前 Herdr 期照旧用文件。
- D18（recommended，R3 Q12）：数据模型从一开始按“项目 → 任务 → 会话”支持多项目；第一个切片只跑 a2a。
- D19（recommended，R3 Q13）：第一版只支持 Claude Code（主控）与 Codex（worker）；其他家以后按需加，每家补启动参数与状态信号。
- D20（user，R4 输入 C9 确认；原为 recommended，R0 Q5 采纳时附带）：提交可追溯到工具、模型、配置、会话（git hook + agent 自己的 hook，只经会话启动参数传入）。机制见 Q19。

## Facts

- F1（observed）：Synara 统一层的接入成本——T-055、T-058、T-061、T-064、T-066、T-068 均需改上游（provider 适配器、网关、投影）。
- F2（observed）：`packages/a2a-gates` 依赖 `@synara/contracts`、`@synara/shared/processRuntime`、`effect`、`node:sqlite`；可抽出但需替换两处 Synara 包。
- F3（observed）：Synara web 栈 React 19、Vite、Tailwind 4、TanStack Router、`@xterm/xterm`；server 有终端（node-pty）实现；desktop 为 Electron 43。
- F4（observed）：Herdr 0.9.3 有 socket API（`herdr api`）、`--session <name>` 多会话、`worktree`、`integration`、`notification` 子命令。用户正在用的 Herdr server 不得修改。
- F5（observed，文章附录）：文章的权限全靠提示词（主脑不写代码、执行者只改允许范围、审查者只读），由门禁兜底（改了禁止路径的提交被打回）；任务卡有"允许/禁止"修改边界与"唯一写入者"；门禁按风险分 personal/internal/saas 三档；AI 审查分 primary/advisor/shadow 三种角色。没有沙箱配置、审批人名单或越权上报流程。
- F6（unknown）：Herdr API 能否把 pane 输出流式给外部 GUI 渲染；Herdr 许可证。
- F7（unknown）：Codex CLI 有无"运行中/等确认/结束"的结构化信号（Claude Code 有 hooks；用户转述其 2.1.295 支持 OSC 7501，未核实）。
- F8（observed，fork `packages/a2a-gates/src/core.ts:1999-2027`、`2155-2199`；managed-delivery、supervised-run 规格）：门禁把 worktree 建在 `state/worktrees/<随机 attempt_id>`，detached，没有分支名，代码里没有删除 worktree 的路径；冻结契约要求回收时"保留 worktree/候选/证据"（supervised-run 第 4 步写作"保留所有 worktree、候选和历史"）。verify 把候选合进集成头，文本冲突返回 `merge_conflict`，任务停在 submitted，没有后续自动流程；验收后集成头变化返回 `integration_conflict`。
- F9（observed，fork `git log --since=2026-10-06 --author=LuckyE`）：52 个 a2a 提交作者都是 LuckyE；7 个带 Co-Authored-By（Claude 或 Codex），没有一个带任务、attempt、会话、模型或思考强度。
- F10（measured，同上加 `--numstat`，不计 lock、snap 文件）：单个提交的增删行数之和 p50=105、p75=394、p90=720、最大 1,748。
- F11（measured，scratchpad 探针，git 2.52.0，2026-10-10）：用环境变量 `GIT_CONFIG_COUNT`、`GIT_CONFIG_KEY_0`、`GIT_CONFIG_VALUE_0` 为一个进程设置 `core.hooksPath`，不写任何配置文件；`prepare-commit-msg` 追加了尾注，加 `--no-verify` 时同样追加；不带这组环境变量的提交没有尾注。
- F12（observed，`claude --help` 2.1.296、`codex --help` 0.162.1）：Claude 有 `--session-id <uuid>`、`--model`、`--effort <level>`、`--settings`；Codex 有 `-m`、`-c key=value`、`-p` profile、沙箱与审批参数。
- F13（measured/observed，2026-10-10）：`~/.codex/sessions` 7.1G、1,175 个 rollout，覆盖 2026 年 1 至 10 月，未见自动清理；`~/.claude/projects` 563M，本项目目录下 4 个会话记录，最早一个最后活动于 10-08；`~/.claude/settings.json` 没设 `cleanupPeriodDays`。Claude Code 文档（code.claude.com/docs/en/data-usage）："store session transcripts locally in plaintext under `~/.claude/projects/` for 30 days by default"，在 Claude Desktop 或 Cowork 里开始或最近续过的会话默认不受此限。Herdr 期 `scripts/session-copy` 的副本只含 2 个会话（执行主控 Claude 会话 `9a64ed90` 与一个 Codex 会话），已被 Git 忽略。一个 1.8M 的 rollout gzip 后 0.7M。
- F14（observed，文章附录 05、06，2026-10-10 下载到 scratchpad）：05 仓库级 AGENTS.md 是索引而非手册，200 行以内，只写稳定约定，命令须从配置核实。06 验收记分卡：时间、任务、执行器、模型、任务类型、复杂度、轮数、耗时、结果（accepted/escalated/abandoned）、边界纪律 0–3、工程品味 0–3、备注；每次都记，打分带理由，词表定了不轻改，按"执行器 × 任务类型"每月交叉分析。
- F15（observed，文章第三至五章与附录 07）：质量保障三条硬规矩（先写测试、小步提交、门禁持续找问题）；写审分开；AI 审查加规则式审查（OCR）；单个 PR 3,500 行硬上限；前端录屏；门禁全绿才合并，自己派的活也不放水；审查角色主审/顾问/影子；风险三档 personal/internal/saas；周期性复盘以本地轨迹为据；指标 1–8（token、一次到位率、最长执行时间、保留轨迹、每百万 token 成本、缓存命中率、提交追溯、主脑打分）。

## Frontier

R4 已问（2026-10-10）：

- Q14 | decide | 原则写进 intent：提示词管判断，脚本管事实；脚本只做能判定对错的检查，不做策略引擎 | recommended: 采纳 | basis: C1、T-049、D9
- Q15 | decide | 任务卡：名称（统一"验收合同"与 brief）、字段、任务类型词表、脚本生成与校验、存后台库、与 ticket 的关系 | recommended: 采纳 | basis: C1、D8、F14
- Q16 | decide | 统一门禁的九项检查、先机械后审查、打回自动回写、连续 3 次打回交执行主控；风险分档、OCR、安全扫描先不做 | recommended: 采纳 | basis: C4、C5、D8、F10
- Q17 | decide | 审查独立性：后台新开只读审查会话，门禁核对非写入会话、新开、绑定提交号；默认同为 Codex，v1 一个主审 | recommended: 采纳 | basis: C5、D9、F15
- Q18 | decide | worktree 命名、清理规则（改冻结契约一句）、冲突的预防与自动流程（不做内容取舍） | recommended: 采纳 | basis: C3、F8、R1、R2
- Q19 | decide | 提交追溯：会话环境变量注入 git 钩子目录追加 `A2A-*` 尾注；Claude 用 `--session-id`；门禁核对尾注，无尾注当用户本人提交记为人工介入，带别的任务尾注的打回；配置即启动记录 | recommended: 采纳 | basis: C9、D9、D14、F9、F11、F12

排队到 R5（本轮只问前五六个最能解锁的）：

- Q20 | decide | 面板收构思主控的提问：每题带选项与推荐，逐个或打包传回构思主控窗格，记为 `answer` 输入；执行主控的 needs-decision 经构思主控转面板 | basis: C6
- Q21 | decide | 验收打分：验收时必填，脚本自动填客观字段，执行主控填边界纪律与工程品味各 0–3 并写理由；词表固定 | basis: C10、F14
- Q22 | decide | 复盘与轨迹：手动加周期，选 CLI、模型、思考强度；脚本准备复盘包；报告与改进建议的去处，建议经面板由用户批；后台归档它启动的所有会话 | basis: C7、C8、F13
- Q23 | decide | 指标：原始事件从第一天全记，指标是能重算的视图；v1 先做哪些视图 | basis: C8
- Q24 | decide | Herdr 期先用哪些（任务卡模板、提交尾注） | basis: C1、C9

## Blocked

- Q25 | decide | 切换条件（D10）要不要加入 C1–C10 的部分功能 | blocked by: Q14–Q24

## Fog

- 额度感知调度与额度水位监控（C2：先不做）、无头模式（D4 之后按需）。
- 多机/远程（文章的 herdr + mosh）。
- 风险分档（personal/internal/saas）：第二个风险不同的项目接入时再定。
- 多审查者交叉、顾问与影子审查；规则式审查工具（文章的 OCR）；定期架构扫描与安全扫描。
- 集成之后怎么进入项目的工作分支：冻结契约不更新用户工作分支，现在由执行主控手工合并。

## Risks and conflicts

- R1 | open | owner: user（Q18） | affects: D8、C3 | 冻结契约要求回收时保留所有 worktree（F8），与 C3"完成后自动清理"不能同时成立。
- R2 | open | owner: user（Q18） | affects: intent.md 范围外条款、C3 | intent 把"自动解决复杂语义冲突"列在范围外；C3"冲突自动处理"需定义为流程自动，不由程序取舍改动内容。
- R3 | open | owner: user（Q25） | affects: D10 | 新功能是否进入切换条件。
- R4 | open | owner: user | affects: C7、C8 | 终端版 Claude Code 默认只留 30 天会话记录（F13）；新应用只能归档它自己启动的会话，此前的记录要长期留，需用户自己调 `cleanupPeriodDays`，我们不改全局配置。

## Out of scope

- 实现与派发 | reason: 决策会话。
- 修改用户的 Herdr server、`~/.claude`、`~/.codex` 全局配置 | reason: AGENTS.md 与用户 2026-10-09 纠正（"不是让你在Claude code和codex里改权限"）。

## Changelog

- R0（2026-10-10）：读文章与附录 01–04、07；核实 F1–F5；用户回答 Q1–Q6（D1–D6）；写 cancel 条目；建本账本。
- R1 答复（2026-10-10）：“Q1:b, 然后用 zsh 不行吗？哪个终端方案好？ / Q2:抽出来用，契约不变，加路径检查 / 3. 采纳这四层 / 4.采纳 / 5. 都采纳”。D7–D11；ACTIVE 改指向本账本。小事：用户说“1.推送 2.删掉”——已 HTTPS 推送 a2a main 到 097268b（fork 不推）；已删 /tmp 下本项目 45 个 a2a-* 夹具目录。
- R2 答复（2026-10-10）：“Q6:采纳 / Q7:a / Q8: 采纳 / Q9: 采纳 / Q10:a + Electron / 然后要删的东西删一下，左边已经回复了”。D12–D16。删除：fork 的四个旧 worktree（synara-t038、t040bc、t040bp、t045）已 `git worktree remove --force`，分支保留；内置盘可用 19G→27G。
- R3 答复（2026-10-10）：“Q11:采纳 / Q12: 采纳 / Q13: 采纳”。D17–D19；补记 D20。frontier 清空，给出漂移检查。
- R4（2026-10-10，新会话"新思路构思"）：上一会话"a2a-构思主控"停在 R3 后的漂移检查，用户没有回"确认"，而是另开会话补充借鉴范围（C1–C10），R3 后的基线因此仍未确认。读文章正文与附录 01–07（05、06 为首次读）；核实 F8–F15（含 git 尾注注入探针）；D20 改为用户确认；执行器打分移出 fog；记 R1–R4；提出 Q14–Q19，Q20–Q24 排队到 R5，Q25 待前面定完。
