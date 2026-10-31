---
id: T-209
title: 用 Herdr 的 hc 当 Enchanted 的终端运行时
type: decide
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by:
ready_rev:
---

## Question

Herdr 于 2026-10 发布了 herdr-core（命令名 `hc`）：只托管终端、不画界面的运行时，程序跑在单独的 holder 进程里，core 重启、升级都不影响；状态只认程序自报的 OSC 7501；子 agent 卡住时会主动通知父 agent。我们自己的终端层（编排后台里的 node-pty）只有用户一个人维护。要不要改用 hc？如果改，怎么分层，哪些旧决定随之改变？

调研与实测见 [findings/2026-10-31-herdr-core-evaluation.md](../../findings/2026-10-31-herdr-core-evaluation.md)。

## Resolution

2026-10-31 用户决定改用 hc。原话：

- “或者我们直接把他们的 Core 拿过来，然后在把我们需要的功能在上面改呢”
- “是在我们的 Enchanted 上做，就用他们 herdr 的 hc 当底层运行时吧，我们自己开发的这套底层只有我自己一个人维护，我也维护不过来，最好的方案就是用别人现成的，我们在此基础上再改，你可以逐步推进任务了。先列好要做什么，要开的票有哪些，给我看了之后再开始执行。”
- 对四个子决定与执行方式：“1.用固定打包版本  2.用建议的  3.用建议的  4.用建议的  建造票不走 Enchanted 了，就用当前 cluade code 就行，你在侧边栏终端开 codex，antigravity 就行。”

分层：

- **hc 管**：起进程、保活、清理子进程（`HC_SCOPE`）、输出流与流控、回应终端查询、状态（OSC 7501 事件）、父子终端与通知。
- **编排后台管**（TypeScript，不变）：门禁检查串、任务卡、审查、钩子（会话与 prompt 绑定、提问的结构化选项）、用户输入与派发记录、问题路由、指标与复盘。
- **输入仍经我们**：界面里的按键和派发文字都经编排后台写进 hc 的 attach 通道，所以用户输入记录和人工介入判定照旧。
- **hc 不改源码**；只有碰到它做不到、上游也不收的需求时才 fork，届时另开决定票。

子决定（用户逐条选“用建议的”）：

1. **来源**：随应用打包固定版本的 hc，不用用户电脑上已装的 hc。编排后台用独立的 `HC_SESSION` 启动私有 core，不连、不改、不重启用户自己 Herdr 的 core。
2. **后台重启后**：程序仍在运行，编排后台接回原 attempt 继续，不再“先回收，再开新 attempt”。这取代 [T-096](T-096-restore-panes-and-sessions-after-restart.md) 的裁定 B。只有程序真的没了（例如电脑重启、holder 丢失）才走原生会话续接。恢复场景须重新证明。
3. **受管 Claude 上报状态**：去掉 `CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1`（T-078-2 为假 API 探针加的），Claude 在 hc 里经 OSC 7501 报 working、blocked（question、permission）、done。代价是 Claude 每轮多一次生成标题的请求。
4. **“阻塞”问题的边界**：见 [T-210](T-210-issues-controller-first.md)。

随之改变的旧决定：

- [T-069](T-069-third-stage-direction.md) 中“终端由编排后台托管（node-pty）”一项改为由 hc 托管；其余方向不变。
- T-096 裁定 B 由上面第 2 条取代。
- 门禁换了运行时，按 AGENTS.md“重新证明”：交付、恢复、编排场景须在 hc 上重新取得红态、绿态与反例。

执行方式（本批例外）：本批建造票不经 Enchanted 门禁派发。由当前 Claude Code 会话做主控，在侧边栏终端开 Codex（gpt-6.1-sol high）写代码、开 agy 做只读审查；主控按每张票的验收条目亲自核对并提交，不 push。写审分开、红态在先、证据入库的要求不变。

规格见 [hc-runtime-2026-10-31](../specs/hc-runtime-2026-10-31.md)。
