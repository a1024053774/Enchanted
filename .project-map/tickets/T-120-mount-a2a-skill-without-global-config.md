---
id: T-120
title: 不改全局配置、不写用户项目，怎样让 Enchanted 终端里启动的 Claude Code 与 Codex 读到 a2a 的使用说明
type: research
status: open
blocked_by: []
claimed_by: claude-2026-10-21
supersedes:
---

## Question

T-119 定下“终端自带 a2a 命令，并自动挂上 skill”。用户在 Enchanted 的普通终端里用自己的命令启动 CLI，没有 a2a 传入的启动参数。约束：不写 `~/.claude`、`~/.codex`，不往用户项目仓库写文件。

要实测回答：

1. Claude Code：终端环境（环境变量、PATH）能否让它加载一个由 Enchanted 提供的插件或 skill 目录？用哪个变量，哪个版本起支持，加载后模型能否看到并按它行事？
2. Codex：同样的问题。有没有不覆盖用户 `CODEX_HOME` 的挂法？
3. 挂不上的 CLI，退路是什么（例如 `a2a` 命令本身打印用法，用户第一次说“你去做主控”时附一句“用 a2a”）。
