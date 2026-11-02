---
id: T-238
title: 项目终端里的 Codex、agy 收到第一句话后一直不执行（疑问，待查）
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---
## What to build

2026-11-02 Computer Use 实测（`evidence/2026-11-02-batch30/cu-bugsweep/BUGS-r2.md`，截图 `shots/r2-codex-queue.png`）：隔离 Enchanted 的项目终端里启动 `codex`，信任目录和钩子后，发出“申请执行主控角色”的话，Codex 显示 `Queued follow-up inputs`，几分钟都不执行，再发一次变成两条排队。agy（Gemini 3.8 Flash）收到同样的话后，好几分钟一直显示运行中，没有回复。

同期后台库里，这些终端没有发来任何钩子或角色申请请求（只有一条普通终端的 `inbox_ready`）。所以还不确定卡在哪：Codex 的 enchanted MCP 服务器启动、SessionStart 钩子，还是模型服务本身。先在项目终端复现，看 CLI 在等什么，再定是不是 Enchanted 的缺陷。如果不是，写明依据后关闭。

这一条挡住了用户最在意的闭环：没有主控，就没法测任务卡从派发到集成、问题面板、人工介入记录。

## Acceptance

- [ ] 复现，并记下 CLI 当时在等什么（MCP 启动、钩子、网络）。
- [ ] 是 Enchanted 的问题就修在根因处，修后项目终端里的 Codex 能接着执行第一句话，并能走完 `a2a request`；不是就附依据关闭。
- [ ] 独立审查（GPT 只读，新开干净会话）无未处理的阻塞意见。

## Resolution

（未开始）
