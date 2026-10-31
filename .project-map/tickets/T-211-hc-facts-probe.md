---
id: T-211
title: hc 事实探针：后续建造票依赖的行为逐条实测
type: research
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## Question

[T-209](T-209-hc-as-runtime.md) 的分层建立在以下 hc 行为上，逐条在隔离 `HC_SESSION` 里实测，记下观察到的事实（不是文档说法）；与假设不符的，在开建造票前报给用户：

1. **固定版本与来源**：当前最新的 hc 发布版本号、macOS arm64 构件的下载地址、发布签名或校验的核对方法（按 hc 的 security 文档），许可证与需要随包附带的声明。
2. **环境不外漏**：编排后台以带有 `CLAUDE_*`、`A2A_*` 等变量的环境启动私有 core 时，core 里新终端拿到的环境是什么；`terminal.run` 的 `env` 能否把终端环境完全定下来。
3. **存活**：编排后台（core 的客户端）退出、core 进程被杀、`hc server restart` 之后，终端里的程序是否仍在运行，屏幕与历史能否重新 attach 取回。
4. **输入原样**：经 attach 通道写入的字节（bracketed paste、回车、Esc、中文、控制键）是否原样到达程序；多个 viewer 同时连着时，`observe` viewer 能否完全不影响尺寸与输入。
5. **状态**：Codex（用户设定的模型）在 hc 里实跑一回合，看是否经 OSC 7501 报 working、done、blocked；受管 Claude 去掉 `CLAUDE_CODE_DISABLE_TERMINAL_TITLE` 后，在 `--permission-mode dontAsk` 与主控用的模式下各报什么；agy、opencode 是否照旧上报。
6. **父子与通知**：`terminal.run` 指定 `parent` 时，子终端 blocked、error、退出各给父终端写什么文字、何时写、父终端自身 blocked 时怎么处理；能否关掉某个子终端的通知（`notify`）。
7. **私有 session 的边界**：socket 与状态目录的位置和权限；用户自己的 Herdr app 能否看到或连上私有 session 的终端。
8. **清理**：`kill` 一个终端后，其中 CLI 起的工具 shell、子进程是否全部结束（`HC_SCOPE`）。

## Resolution

（未开始）
