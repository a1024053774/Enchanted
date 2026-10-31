---
id: T-211
title: hc 事实探针：后续建造票依赖的行为逐条实测
type: research
status: closed
blocked_by: []
claimed_by: claude-code-2026-10-31
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

2026-10-31，Claude Code 主控在隔离会话里实测 hc 0.1.15。用户自己 Herdr 的 core 没有碰。完整结果、复现命令与原始输出见 [evidence/2026-10-31-batch29/T-211/RESULTS.md](../../evidence/2026-10-31-batch29/T-211/RESULTS.md)。**总状态 INCOMPLETE**：只有第 5 项的 Codex 部分为 BLOCKED（Codex 登录已过期，需要用户重新登录），挪到后续受管窗格切片开票前补测；其余各项都取得了事实。

1. **PASS**：固定 0.1.15。macOS arm64 构件的 SHA-256 与 manifest 一致，发布没有独立签名密钥。许可证为 Apache-2.0，随包附带 `LICENSE` 与 `THIRD-PARTY-NOTICES`。
2. **PASS，与假设部分不符**：
   - core 的环境原样进入终端，`env` 只能覆盖、不能删除，所以终端环境只能靠 core 的启动环境控制。
   - 给 core 设的 XDG 变量也会进终端。实测可行的组合是：socket 用 `HC_SOCKET`；私有状态与配置目录经 XDG 变量交给 core；终端 argv 前加 `env -u XDG_STATE_HOME -u XDG_CONFIG_HOME`。这样终端里的 `hc` 仍能连回私有 core。
   - socket 路径上限为 103 字节。
3. **PASS**：
   - 客户端退出、`server restart`、kill -9 core 之后，程序都还活着。
   - 正常重启时屏幕与历史完整。core 崩溃后屏幕标为 inexact，历史丢失，hc 会让全屏程序重画。
   - 后台重启不动 core，因此不受影响。
4. **PASS**：
   - attach 写入的字节（bracketed paste、中文、CR、Esc、Ctrl-C、Ctrl-D）原样到达程序。
   - observe viewer 改不了尺寸，也敲不进字。
5. **INCOMPLETE**：
   - Claude 在不设或设空 `CLAUDE_CODE_DISABLE_TERMINAL_TITLE` 时正常上报：dontAsk 与默认 auto 模式下为 idle/working/done，default 模式下为 blocked(permission)。设为 `1` 时完全不报，T-209 子决定 3 成立。
   - agy 启动时先报约 7 秒的 blocked(auth)。opencode 回合结束报 idle，不报 done。
   - Codex 停在登录页，不报任何状态，正常回合未测。
6. **PASS**：
   - 子终端 blocked、error、退出时，hc 各往父终端粘贴一行 `<hc>…</hc>`。
   - 父终端 blocked 时通知扣住，回到 idle 后送达。
   - `no_notify` 能关掉单个子终端的通知，配置项 `notes = false` 全局关闭。
7. **PASS**：
   - 私有 core 的目录权限为 0700。
   - 用户的 Herdr app 经 `herdr-core connect` 只连 `default` 会话，看不到私有 core。
   - 会话不是安全边界。
8. **PASS，与假设部分不符**：
   - `hc kill` 能清掉脱离 session 的 node、python 子进程。
   - 在 macOS 上，被 launchd 收养的系统二进制（`/bin/sleep`）会逃过清理，上游认为可以接受。

另：`terminal.send` 的条件参数名是 `if`；评估报告里写的 `only_if` 不对。
