# herdr-core 能否做 Enchanted 的终端内核（2026-10-31 调研）

范围：读 herdr.dev 的 App、Core、Mods 页面；读 `herdrdev/herdr-core`（1d09234）与 `herdrdev/herdr-app`（9af0ecc）源码；在隔离 core（`HC_SESSION=a2a-probe`，用后已停止并删除状态目录）里用 Claude Code 2.1.312 + Haiku 实测状态上报。未改动用户正在使用的 Herdr 与其 core。

## 事实

- **herdr-core（`hc`）是什么**：Rust 写的终端运行时，自己不画界面。程序跑在 holder 进程里，core 重启、更新、界面关掉都不影响；`--keep` 的终端丢了程序会起新 shell，不重跑原命令。对外是一套 JSON-RPC API（Unix socket；`hc connect` 走 stdin/stdout，所以 `ssh box hc connect` 就是远端 core），OpenRPC 描述，状态为 preview 0.x，只增不删。Apache-2.0。
- **API 面**：`terminal.run`（argv、cwd、env、labels、parent）、`list/get/read/send/keys/interrupt/wait/kill`、`terminal.attach`（分帧流，带信用流控、首帧补画、多 viewer）、`events.subscribe`（created/status/turn/finished… 带 seq，落后给快照）、`doc.get/set`（带版本号 CAS 的不透明 JSON）、`machine.*`（SSH 多机）、`file.*`。
- **父子 agent**：在 hc 终端里起的 agent 成为子终端；子终端阻塞、出错、退出时 core 往父终端里打一条 `<hc from=...>` 通知；`hc wait --children`。
- **状态只看 OSC 7501**：不刮屏、不认品牌。`blocked` 带 `kind`（permission / question / auth）和 `msg`；`blocked` 时 `send` 默认拒绝，防止把文字当作对弹框的回答。
- **实测**：Claude Code 2.1.312 原生上报。干净环境下 `idle → working（msg 是当前动作）→ done`，`turn` 每轮 +1；用 AskUserQuestion 时报 `{"state":"blocked","kind":"question","msg":"answer: 红色还是蓝色？ (红色 · 蓝色)"}`，此时 `hc send` 返回 `kind: blocked`。前提是终端回应 `OSC 7501 ; ?` 探测，且环境里没有 `CLAUDE_CODE_DISABLE_TERMINAL_TITLE`（有它就完全不报——本会话环境带着它，第一次实测因此全是 null）。
- Codex 0.164.0 二进制里有 `]7501;state=` 输出，未实跑验证。
- **herdr-app**：原生 GPUI（Rust）客户端，mods 是跑在内置 QuickJS 里的 JS，配 GPUI 组件库；布局、按键、mods 都是 `~/.config/herdr-app` 下的纯文件，由用户的 agent 改。mods 依赖它的 `.d.ts` API 和 GPUI 渲染，不能直接搬进 Electron。
- 后台 Computer Use 能点到窗口，但 GPUI 窗口在后台不重绘、键入延迟上屏，全屏控制未获批，界面只看了设置页；界面行为以官网与 README 为准。

## 我们的工作台对应部分

- `workbench/src/panes.ts`（2,251 行）自己用 node-pty 托管终端，`paneRecovery.ts` 做恢复；agy、opencode 已读 OSC 7501（`terminalClis.ts`）。
- 受管 Claude 以 `CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1` 启动（`claudeLaunch.ts:78`），所以在工作台里不报 7501；Claude、Codex 的回合、提问、权限都走钩子，并按 session、prompt_id、submission 做绑定（`questions.ts`）。
- 问题面板已有：T-055、T-057 做了上报、回复、逐个/打包发送；T-124 让终端主控能回答 worker 的提问。

## 判断

可以用，但它只能替换“终端托管”这一层，替换不了门禁、钩子绑定与用户输入记录。

能省的：pty 托管与跨重启存活、xterm 流与流控、多 viewer、多机 SSH、父子 agent 通知、Claude/Codex 的统一状态（不用再为每家 CLI 写一套回合判断）。

省不掉、且要新做的：

1. **用户输入记录**：任何能连上那个 core 的 viewer（包括 Herdr app、`hc attach`）都能直接打字，core 不记谁打的。要保证“受管 worker 里的直接输入记为人工介入”，必须用独立 `HC_SESSION`，不让用户的 Herdr app 连到受管终端。
2. **提问的结构化选项与答复绑定**：7501 的 `msg` 只是摘要，答复要落到哪个 tool_use、哪个 prompt，仍要靠钩子。
3. **打包**：hc 是外部二进制，要随 Electron 一起分发并固定版本；API 仍是 preview。
4. **约束冲突**：AGENTS.md 要求“不得修改或重启用户正在使用的 Herdr server”、“工作台出缺陷不回退 Herdr”。用独立 session 的 hc 不碰用户的 core，但这是改变终端层归属的设计取舍，要用户拍板后开决定票。

建议的最小探针（未做）：在隔离 `HC_SESSION` 下，让编排后台用 `terminal.run` + `terminal.attach` 起一个受管 Claude worker，xterm.js 接 attach 流，钩子照旧，看门禁的红态、绿态和反例能否原样通过。通过了再决定是否替换 node-pty。

## 第二轮：Herdr app 实操（同日，全屏控制获批后）

在用户正在使用的 Herdr app 里（默认 core），用 Claude Code + Haiku 在 a2a 目录跑了三步，结束后杀掉 helper、父会话 `/exit` 回到 zsh。

1. **等你**：让 Claude 用 AskUserQuestion 提问。core 记 `blocked / question / "answer: red or blue? (Red · Blue)"`。界面五处同时提示：侧栏 Agents 顶部出现“Needs you 1”分组，标签页红点，窗格标题“Needs you”徽标，底栏“1 needs you”，右下角提示“Claude Code needs you · a2a / 1”。
2. **agent 起 agent**：让父 Claude 运行 `hc run --bg --name helper claude … '问 tea or coffee'` 再 `hc wait helper`。helper 自动成为 t1 的子终端（`parent: t1`），侧栏把 helper 缩进挂在父 agent 下，红标在 helper 上；`hc wait` 在 helper 进入 blocked 时立即返回 `status: blocked`，父 agent 不用轮询就知道子 agent 卡住。点 helper 打开 peek 浮层，标题“helper · needs you · from t1”，可直接作答，也可 keep 成标签页。
3. **主控替子 agent 答**：让父 Claude `hc read helper` 看屏，`hc keys helper enter` 选 Tea，再 `hc wait helper`，helper 走到 `done`。**helper 自己的记录写的是“User answered Claude's questions: Tea or coffee? → Tea”**：Herdr 不区分“父 agent 答的”和“用户答的”。

界面细节：工作区按第一个终端的目录自动命名（`~` → `a2a`）；右侧常驻 Changes 面板，直接显示仓库 diff 并可提交。GPUI 窗口被全屏透明窗口（用户的 Vorssaint）遮住时停止重绘，隐藏再显示可恢复。

## 它的 core 比我们好在哪里

| 设计点 | herdr-core | 我们现在 | 影响 |
|---|---|---|---|
| 进程归属 | holder 进程只管 PTY、不解析、不做策略；core 可崩溃、可升级，程序不受影响；holder 保留每个终端约 1 MB 尾部，用来重建屏幕 | node-pty 在编排后台进程里；后台重启后 worker、reviewer 随之消失，登记为 stopped，门禁回收再重派新 attempt（`panes.ts:615-630`，T-096 裁定 B） | 后台一次重启就丢掉进行中的 attempt |
| 状态来源 | 只认程序自报的 OSC 7501，带 turn 计数和“刚卡住”变化 | Claude、Codex 走各自钩子；agy、opencode 走 7501；侧栏有“未知”（U04） | 我们每接一家 CLI 都要写一套回合判断 |
| 卡住时谁知道 | 子 agent blocked、error、退出时，core 往父 agent 里打一条带标记的通知；父 agent 正在 `wait` 这个子 agent 时不打，父 agent 自己 blocked 时先存着 | worker `issue` 只写一条 `to: "triage"` 记录（`gates/core.ts:722-791`），不推送给主控；主控要轮询（证据里有 3 份 `controller-poll.log`）；15 分钟没处理或标 blocking 直接变“等你决定” | 主控不知道有问题要处理，问题直接落到用户头上 |
| 等待 | `wait` 等某个终端、等全部或任一子 agent、等“我这次 send 开启的那一轮”；手册明写不许 sleep 轮询 | 主控靠轮询和收件箱唤醒 | 轮询费额度，也慢 |
| 人和 agent 同时输入 | 每终端一条输入队列；人打字后 3 秒内 agent 不插话；agent 粘贴时人按的键先存着、粘完再放 | `userDraft` 时队列不发，思路相同 | 持平 |
| 清理子进程 | 每个终端的环境带随机令牌 `HC_SCOPE`，按令牌找出全部后代，包括已离开会话的工具 shell | 按进程树快照，遇到过 setuid 进程 EPERM（T-124） | 令牌更简单、更稳 |
| 接口 | 一张方法表生成 CLI、API 与 OpenRPC，三者一致；agent 一条 `hc --skill` 读完手册 | 门禁 CLI、MCP、后台命令几套入口 | 接口面多 |
| 多机 | SSH 加机器，远端终端进同一列表 | 无 | 以后要用 |

我们领先、必须保留的：门禁检查串（认领、交付、审查、验收、集成）、任务卡与路径边界、独立审查、按来源区分用户输入与主控回答（T-124、T-206）。实测 3 说明 Herdr 没有这一层。

## “直接拿它的 core 来改”怎么做

建议先**不改它的 Rust 源码**，把未改动的 `hc` 当运行时，我们的门禁、记录、问题路由留在编排后台（TypeScript），经 JSON-RPC 调它：

- 起 worker：`terminal.run`，argv、env、cwd 照现在记录，labels 带 task、attempt、role；`parent` 设为主控的终端，worker 卡住、退出时主控自动收到通知。
- 显示：xterm.js 接 `terminal.attach`。
- 派发：`terminal.send`（`only_if: idle`），我们在调用前后照旧记 `paste_intent`、`turn_submitted` 等事件。
- 钩子不变，仍负责 Claude、Codex 的会话、prompt 绑定与提问的结构化选项。
- 用独立 `HC_SESSION`，socket 只给我们的后台和 Electron，用户的 Herdr app 连不到受管终端。这样人的按键全部经过我们的 attach 通道，人工介入照样能记，不需要改 core。

只有碰到它做不到、上游也不收的需求时才 fork；目前没找到这样的需求。fork 的代价是自己跟进一个日更的 Rust 项目（hc 0.1.15，当天仍有提交）。herdr-app 是 GPUI，按 AGENTS.md 不基于它做界面；mods 以后要兼容，得在 Electron 里实现它的 mod API。

## 问题面板按 T-124 的差距

用户 2026-10-31 原话：“规则肯定按 t-124 的来啊，有些问题主控能解决就没必要一直等我回复”；“我们当前不是有个问题界面嘛？那个就是我想做的这个功能”。

现状：问题页（`workbench/app/IssuesPage.tsx`）按项目列出上报，已支持答复、关闭、稍后、主控答复记为主控（T-124）。缺的是**主控先处理**这一步：

1. 上报时不通知主控（见上表）。改为上报即推给执行主控（收件箱唤醒，或 hc 的父终端通知）。
2. 标 blocking 的直接算“等你决定”，主控没有机会先答。按用户这次的话，应先给主控；主控答不了或属于 T-051 列的不许主控处置的类别（权限、范围、验收条件、安全、不可逆操作），再标“交给你决定”。这一条改动了 T-051 的规则，需要用户确认边界。
3. “等你决定”只在项目内的问题页显示数字。可学 Herdr：侧栏顶部跨项目的“等你”分组、标签页红点、应用内提示。
