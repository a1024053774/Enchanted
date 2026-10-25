---
id: T-184
title: 查明 lcu 实测中主控终端钩子与 a2a 插件都没生效的原因
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

用户 2026-10-25 逐字：“1. 查明一下 3.装上钩子  5.发新 release,产品页也更新  新票:增加 antigravity,opencode 的支持吧,按理说应该不限 cli 的,但应该还要实测一下,”

对应 T-176 遗留与 T-181 观察（findings/2026-10-25-lcu-real-use.md）：真实 0.1.3、用户真实 Claude 下，主控终端一条钩子事件都没送到后台，技能里也没有 a2a；隔离复现时插件都能加载。待验证假设（不限于）：那一轮应用是从 Herdr 用 open 启动、继承了 HERDR_*/CLAUDECODE 等环境；用户 zsh 启动脚本让 claude 解析到包装脚本以外（PATH 顺序、hash、别名或函数）；插件目录在替换应用期间失效；Claude 2.1.310 对 --plugin-dir 的行为。用 `type -a claude`、进程 argv（ps）、pty.raw 与插件加载日志取证，先定位再修；能修则修根因，不加重试。

通用：先留真实入口的红态再修根因；真实 Claude 用 claude-haiku-5-5、尽量少；不写 ~/.claude、~/.codex 等全局配置，钩子只经每会话启动参数；agy 独立审查。

## Acceptance

- [ ] 写出根因并附证据（进程 argv、环境、复现命令）；未能复现时写 INCOMPLETE 与已排除的假设，不写成 PASS。
- [ ] 若可修：修前在真实应用（从 Dock/Finder 启动）复现钩子缺失，修后 Stop/UserPromptSubmit 送达后台、侧栏状态随之变化；用户自己在项目终端敲 claude 时同样生效。

## 不做

范围外问题经问题上报。
