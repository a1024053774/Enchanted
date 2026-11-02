# 任务书：调查 T-238（2026-11-02）

用户原话：“第三个要让 codex 去调查清楚”。你只调查、不修：查清项目终端里的 Codex、agy 为什么收到第一句话后一直不执行，写成报告。不改 a2a 仓库的源码、ticket 或地图。

## 先读

- `.project-map/tickets/T-238-codex-agy-first-prompt-never-runs.md`
- `evidence/2026-11-02-batch30/cu-bugsweep/BUGS-r2.md`、截图 `shots/r2-codex-queue.png`
- `workbench/README.md` 里项目终端、包装脚本（`workbench/terminal/bin/codex`、`agy`）、`a2a session-context`、`a2a mcp`、钩子的部分

## 环境

- 程序：`/private/tmp/a2a-build-cu-test-20261102/Enchanted.app`（HEAD `2b3b12dac`）。**只准**用这条命令启动，启动后用 `ps` 核对后台的 state 路径是 `/private/tmp/a2a-t238/state`，不是就立刻退出并写进报告：

  ```bash
  open -n /private/tmp/a2a-build-cu-test-20261102/Enchanted.app --args --state /private/tmp/a2a-t238/state --user-data /private/tmp/a2a-t238/ui
  ```

- 测试项目：自己在 `/private/tmp/a2a-t238/` 下 `git init` 一个小仓库。上一轮的现场 `/private/tmp/a2a-cu/` 只读参考（它的 `state.sqlite3` 有上一轮的事件），不要再用它启动。
- 主控（Claude Code）此时正在修 T-236、T-237，会另打包到别的目录；你只用上面这份包，不碰 `workbench/` 的文件。
- 可以用 Computer Use 操作你启动的 Enchanted 窗口；也可以不经界面复现，例如照包装脚本的环境变量自己起 CLI、跑 `a2a session-context`、`a2a mcp codex`、`a2a hook`，看它们是否阻塞。能不经界面复现的优先。

## 授权

用户原话：“他要是让授权,你帮我点同意就行”。CLI 对 `/private/tmp/a2a-t238/` 下目录的信任框、Codex 的钩子信任框、Enchanted 界面里的角色申请批准，都直接同意并记下时间和是哪个框。系统设置、macOS 隐私授权、登录密码不碰，遇到就停。不用临时 `CODEX_HOME`（产品里的 Codex 本来就用用户的 `~/.codex`）。不碰用户自己的 Herdr、hc（非本次启动的 hc 进程）和 `/Applications/Enchanted.app`。

## 要回答的问题

1. Codex 第一句话排队时，它在等什么：enchanted MCP 服务器启动（`a2a mcp codex`）、SessionStart 钩子（`a2a session-context`）、UserPromptSubmit 钩子（`a2a hook`）、模型请求，还是别的？给出直接证据（进程树与各进程状态、`lsof`、Codex 自己的日志 `~/.codex/log/`、会话 jsonl、后台事件），不要只凭推断。
2. agy 一直“运行中”不回复，是不是同一个原因。
3. 在普通终端（不经 Enchanted）起同样版本的 Codex、agy 是否正常，作对照。
4. 结论：是不是 Enchanted 的缺陷；是的话根因在哪个文件、哪段逻辑，最小修法是什么（只写建议，不改代码）；不是的话写明依据。

## 交付

中文报告写到 `evidence/2026-11-02-batch30/T-238/REPORT.md`：结论（PASS / INCOMPLETE / BLOCKED / NO_GO 之一，表示调查是否查清）、复现步骤、证据（命令与输出摘录）、根因、修法建议、没查清的部分。截图放同目录 `shots/`，截图里不要有账号邮箱。测完退出你启动的 Enchanted 和它的后台、core、CLI 进程，`ps` 核对。现场 `/private/tmp/a2a-t238/` 保留。
