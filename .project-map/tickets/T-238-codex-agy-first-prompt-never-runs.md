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

2026-11-02 进展（未关闭）。第 1 轮（[REPORT](../../evidence/2026-11-02-batch30/T-238/REPORT.md)）未复现；第 2 轮在新包上复现了 Codex 排队与 agy 一直 working：

- 已查到的（[T-236 结果](../../evidence/2026-11-02-batch30/T-236/RESULTS.md)、[T-238 第 2 轮报告](../../evidence/2026-11-02-batch30/T-238/REPORT-02.md)）：项目终端里的 Claude 停在加载 skill 时打开 `~/Documents/SKILLS/...` 下的文件；Codex、agy 卡住时也各有线程停在 open 类系统调用（路径未取得）。
- 打开 `~/Documents/SKILLS` 下的几个 SKILL.md 会在内核 `open` 里停约 5 秒后以 `Interrupted system call` 失败；同一现象在打包应用的终端、源码后台的终端、Codex 自己的进程里都出现，**不是 Enchanted 独有**；主控工具进程里读同样的文件 0.02 秒内返回。`~/Documents` 下别处的文件（如 `~/Documents/Code/a2a/AGENTS.md`）读得出来。
- 已否定：“新包在等文稿文件夹授权”（从没启动过的新包读 `~/Documents` 0.11 秒返回，`tccd` 无该请求）；已排除：文件被占用、iCloud、Endpoint Security 扩展。`~/Documents/SKILLS` 及部分子目录带 `com.apple.macl`，与此是否有关未查；再往下需要 `sudo fs_usage` 一类的系统工具，主控没有这个权限。
- 目前没有证据表明是 Enchanted 的代码缺陷，也没有可做的代码修复；状态 **INCOMPLETE**，等用户决定是否继续查。
