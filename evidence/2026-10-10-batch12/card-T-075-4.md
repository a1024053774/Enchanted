# 任务卡 T-075-4

你是 a2a 的 worker（Codex），由执行主控（Claude Code）派发，只做这张卡。T-075 的前三张卡已经完成：门禁迁移、三项契约与任务卡、编排后台加 Codex 窗格加真实交付（`93a7072`、`7c4bf88`）。本卡是最后一张。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-075-4 |
| 来源 | ticket T-075，以当前的 `ready_rev` 为准 |
| 目标 | 做一个最小的 Electron 窗口，经编排后台的本地入口连接，显示一个项目、一个任务、一个窗格（用 xterm.js 显示真实 PTY 输出）和门禁状态。关掉窗口后，worker 窗格照常运行；重新打开窗口能接上同一个窗格。后台重启后，进行中的 attempt 按恢复语义处理。外置盘未挂载时构建报错，不回退到内置盘。做完后，T-075 的验收项可以逐条核对。 |
| 非目标 | 不做面板、通知、设置页（S5）；不做主控窗格、收件箱入库、唤醒（S4）；不做独立审查会话、打回回写、打分（S2）；不做 worktree 清理（S3）；不做 Claude；不搬 Synara 的 provider 或 MCP 网关；不在 Electron 进程里加载 node-pty。 |
| 修改边界 | 允许：`workbench/` 下新增界面目录（建议 `workbench/app/`，包括 Electron 主进程、preload、渲染层和构建配置），以及界面需要的后台查询和订阅接口（`workbench/src/` 中与此直接相关的部分）、测试、README；本卡证据目录 `evidence/2026-10-10-batch12/T-075/card-4/`；ticket T-075 的 Resolution。禁止：`acceptance/` 已有断言、`scripts/`、`.project-map/specs/`、Synara fork（只读，可以读取它的组件和样式）、全局配置、`~/.codex`、`~/.claude`、`~/Library/Application Support/a2a-workbench`。 |
| 完成条件 | 见下方“完成条件”。 |
| 红态命令 | 在起点提交上运行界面端到端命令，必须因为界面或接口不存在而失败。 |
| 任务类型 | 前端界面 |
| 修复对象 | — |
| 复杂度 | L |
| 执行器 | Codex CLI，`gpt-6-astra`，xhigh，Fast 请求。选用理由：本卡跨 Electron、渲染层、后台订阅接口和后台重启恢复语义，按用户的规定，复杂任务改用 astra。 |
| 起点 | a2a `main` 当前 HEAD（开工时写进 RESULTS） |
| 唯一写入者 | 本 worker 会话（Herdr agent `s12-t075-4`） |

## 执行主控已定的事项
- **依赖**：执行主控已在 `workbench/` 装好以下包（`614471b`）：`electron@43.4.1`（二进制已下载，缓存在 `/Volumes/WD-Elements/a2a-electron-cache`）、`@xterm/xterm@6.0.0`、`@xterm/addon-fit@0.11.0`、`react@19.2.4`、`react-dom@19.2.4`、`vite@8.1.5`、`@vitejs/plugin-react@6.0.1`、`tailwindcss@4.3.3`、`@tailwindcss/vite@4.3.3`。版本与 fork 一致；唯一例外是 `@tailwindcss/vite`，fork 用的 4.2.1 不兼容 Vite 8，所以改用 4.3.3。还需要别的包时，停下问我，不要申请提权去联网。
- **组件来源**：从 fork（GitHub `a1024053774/synara`，本地 `../synara`，只读）搬运组件和样式，保留 MIT 声明。搬多少由你定，以“最小、看起来属于同一视觉家族”为准，可参考 `same-visual-family` 和 `frontend-less-ai-tone` 两个技能。
- **进程边界**：Electron 主进程通过后台的 Unix socket 连接后台，不直接打开库，也不持有 PTY。窗格输出改为由后台推送或分段读取（你在 PLAN 里定）。重开窗口时，必须能从后台补回此前的输出，再接上实时输出。
- **界面输入**：用户在窗口里对窗格的输入，也要经过后台写入，并按 spec 第 6 节记录：受管 worker 窗格记为人工介入，主控派发的文字不算用户输入。如果你判断本卡只做只读显示更合适，在 PLAN 里说明理由，由我来定。
- **数据目录**：产品默认目录是 `~/Library/Application Support/a2a-orchestrator`，本卡所有验证都使用 `/tmp` 下的隔离目录。
- **构建缓存**：Vite 的缓存和构建中间产物放外置盘。构建脚本要先检查外置盘确实已挂载，没挂载就报错，不回退到内置盘。验收时用一个指向“未挂载路径”的配置来证明会报错，不要真的卸载用户的磁盘。构建输出目录里不能放指向源码或依赖的链接（AGENTS.md 有一次事故记录）。
- **截图**：用 Electron 的 `webContents.capturePage` 保存 PNG，不用 Computer Use。
- **真实 Codex**：最好用一个脚本化的 zsh 窗格来证明界面行为，例如持续输出的命令。如果确实需要真实 Codex worker，被测会话用 `gpt-6.1-sol` xhigh Fast，**本卡最多 4 个主 turn**，隔离 CODEX_HOME 的规则同前几张卡。
- **后台重启**：node-pty 的子进程会跟着后台一起退出。所以这里的“恢复”是指：后台重启后，进行中的 attempt 和窗格按 spec 和恢复语义标为中断或未知，门禁意图按 recovery 契约恢复；不自动续跑，不伪造“已完成”。

## 先交计划，停下等我
写 `card-4/PLAN.md`，内容包括：
- 界面结构；
- 后台新增的接口；
- 输出补回与订阅；
- 输入记录；
- 重启恢复语义（逐项对照 recovery spec）；
- 构建脚本和外置盘检查；
- 端到端正例与反例清单；
- 截图；
- 真实回合预算；
- 需要在沙箱外运行的项。

写完回复 `T-075 PLAN READY`，然后停下等我。

## 完成条件（我写好的，交付前跑一遍并保存输出）
1. Electron 窗口的截图，能看到项目、任务、窗格（有真实输出）和门禁状态。截图由 `capturePage` 生成，并附上生成它的命令。
2. 关闭窗口后，窗格进程仍在运行，用 ps 读回 pid 确认；窗格输出仍在增长，用后台的 trace 读回确认。重开窗口后，能看到关闭期间的输出，并且继续接收新输出。补回的内容要和 trace 原文逐字比对。
3. 后台重启：停掉后台再启动后，原窗格和 attempt 的状态按 PLAN 中批准的语义显示，用库和 CLI 读回。没有自动续跑，也没有被写成“已完成”。
4. 构建：外置盘已挂载时构建成功；把检查路径指向未挂载的位置时，构建报错，且没有在内置盘上留下缓存。
5. 窗格状态拿不到结构化信号时显示“未知”。至少有一个反例证明界面不读屏。
6. `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .` 输出 0 problems。

## 沙箱外运行、审查与交付
- 沙箱外运行的做法同前几张卡：写 `card-4/outside-sandbox.sh`，回复 `T-075 OUTSIDE-SANDBOX READY` 后停下，由我执行。Electron 的启动和截图都在沙箱外进行。
- 探针或测试本身的错误，可以直接修，但要记录。git 写操作（`git add`、`git commit`）必须各自单独执行，不要串联，也不要加环境变量前缀。
- 交付前做一次 fresh-context 只读独立审查。审查中发现的问题，先拿到红态再修；修复部分的 diff 由我审。
- 交付内容：a2a 提交（带尾注）、`card-4/RESULTS.md`、ticket Resolution（写清 T-075 每一条验收项的证据位置，ticket 保持 open，由我关闭），最后在终端回复一行 `T-075 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。
## 共同规则
- 先读 a2a 的 `AGENTS.md`、`CONTEXT.md`、`intent.md`（第三阶段修订）、你的 ticket（验收以它为准，依据 ticket 当前的 `ready_rev`），以及 `.project-map/specs/native-cli-orchestration-2026-10-10.md` 里 ticket 指向的章节。
- 发现 spec 与实际行为不符：停下说明（由主控写 needs-decision），不绕开。
- 不碰用户的 Herdr server（可以经 `herdr` 命令行建、关自己的 pane），不写 `~/.codex`、`~/.claude`、全局或仓库级 git 配置，不停正式工作台、不读写 `~/Library/Application Support/a2a-workbench`。不 push。只停你启动的进程，只删你创建的文件。不改 Synara fork。
- 真实 Codex 调用：见上文“真实 Codex”。
- 依赖缓存放外置盘 `/Volumes/WD-Elements`，没挂载就报错，不回退到内置盘。
- 先红后绿；预期来自 ticket/spec，不来自实现输出；失败原样保留；不用正则或关键词规则判断内容含义；不加兜底重试。
- 证据放 `evidence/2026-10-10-batch12/T-075/card-4/`，中文 `RESULTS.md`，每项产物附重新生成它的命令；a2a 只提交你的文件与 ticket Resolution（保持 open，写"待主控关闭"）。完成前运行 `python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .`。
- 最后在终端回复一行：`T-0xx DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。需要决定的事停下说明，完成前不要结束回合。
- 发给你的文本经 `scripts/dispatch` 投递，带 ⟦主控 #序号⟧ 标记；没有这个标记的输入来自用户本人。
- 范围外的问题用 `scripts/inbox send --kind issue` 上报，不要自行忽略。
