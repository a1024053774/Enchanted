---
id: T-120
title: 不改全局配置、不写用户项目，怎样让 Enchanted 终端里启动的 Claude Code 与 Codex 读到 a2a 的使用说明
type: research
status: closed
blocked_by: []
claimed_by:
supersedes:
---

## Question

T-119 定下“终端自带 a2a 命令，并自动挂上 skill”。用户在 Enchanted 的普通终端里用自己的命令启动 CLI，没有 a2a 传入的启动参数。约束：不写 `~/.claude`、`~/.codex`，不往用户项目仓库写文件。

要实测回答：

1. Claude Code：终端环境（环境变量、PATH）能否让它加载一个由 Enchanted 提供的插件或 skill 目录？用哪个变量，哪个版本起支持，加载后模型能否看到并按它行事？
2. Codex：同样的问题。有没有不覆盖用户 `CODEX_HOME` 的挂法？
3. 挂不上的 CLI，退路是什么（例如 `a2a` 命令本身打印用法，用户第一次说“你去做主控”时附一句“用 a2a”）。

## Resolution

2026-10-21 实测（Claude Code 2.1.306、codex-cli 0.163.0，真实登录）。重跑：`evidence/2026-10-21-batch19/T-120/probe.sh`，输出见同目录 `probe-output.txt`。Claude 用用户自己的设置（只读）和 `--no-session-persistence`；Codex 用只含 auth.json 的隔离 `CODEX_HOME`，用完删除。

| 探针 | 结果 |
| --- | --- |
| Claude，终端环境变量 `CLAUDE_CODE_PLUGIN_DIRS` | 读不到。用户 `~/.claude/settings.json` 的 `env` 块设了同名变量，会盖掉终端传入的值 |
| Claude，同上但跳过用户设置 | 读到，说明变量本身有效，只是被用户设置盖掉 |
| Claude，启动参数 `--plugin-dir` | 读到，并且与用户设置里的插件目录合并，不替换 |
| Codex，`-c skills.config` 指路径 | 读不到：这一项只能启用或停用已有的 skill。Codex 只从 `CODEX_HOME`、`~/.agents`、项目 `.agents`、`/etc/codex` 读 skill，没有按会话指定目录的方式 |
| Codex，`-c developer_instructions` | 读到。用户 `~/.codex/config.toml` 没有设这一项，不会被覆盖 |
| 只把包装目录放在 PATH 前面 | 不行：用户 `.zshrc` 会把 `~/.local/bin` 重新排到前面 |
| `ZDOTDIR` 引导（VS Code 终端集成的做法） | 包装目录排在最前；先加载用户的 `.zshenv`、`.zprofile`、`.zshrc`、`.zlogin`，239 个 alias 都在；不改用户文件 |

结论：两家 CLI 都只能靠启动参数挂说明，所以挂法定为“终端里的同名包装命令”：

1. Enchanted 普通终端以 `ZDOTDIR` 引导启动 zsh：先依次加载用户自己的启动文件，再把 Enchanted 的命令目录放到 PATH 最前面。目录里有 `a2a`，以及 `claude`、`codex` 两个包装命令。
2. 包装命令在 PATH 里跳过自己，找到用户真正的 CLI，原样转发用户的参数，只多加一个按会话生效的参数：Claude 加 `--plugin-dir <Enchanted 插件>`（含 a2a skill），Codex 加 `-c developer_instructions=…`（说明怎么用 `a2a`）。用户自己在命令行传了 `developer_instructions` 时不加，避免覆盖。
3. 退路：其他 CLI，或用户绕开包装直接调用真实路径时，`a2a` 仍在 PATH 里，`a2a help` 打印用法，用户可以对 agent 说“用 a2a”。
