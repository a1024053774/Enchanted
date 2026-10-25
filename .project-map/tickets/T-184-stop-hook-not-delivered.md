---
id: T-184
title: 查明 lcu 实测中主控终端钩子与 a2a 插件都没生效的原因
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 2
---

## What to build

用户 2026-10-25 逐字：“1. 查明一下 3.装上钩子  5.发新 release,产品页也更新  新票:增加 antigravity,opencode 的支持吧,按理说应该不限 cli 的,但应该还要实测一下,”

对应 T-176 遗留与 T-181 观察（findings/2026-10-25-lcu-real-use.md）：真实 0.1.3、用户真实 Claude 下，主控终端一条钩子事件都没送到后台，技能里也没有 a2a；隔离复现时插件都能加载。待验证假设（不限于）：那一轮应用是从 Herdr 用 open 启动、继承了 HERDR_*/CLAUDECODE 等环境；用户 zsh 启动脚本让 claude 解析到包装脚本以外（PATH 顺序、hash、别名或函数）；插件目录在替换应用期间失效；Claude 2.1.310 对 --plugin-dir 的行为。用 `type -a claude`、进程 argv（ps）、pty.raw 与插件加载日志取证，先定位再修；能修则修根因，不加重试。

通用：先留真实入口的红态再修根因；真实 Claude 用 claude-haiku-5-5、尽量少；不写 ~/.claude、~/.codex 等全局配置，钩子只经每会话启动参数；agy 独立审查。

补充（ready_rev 2）：根因已定位为操作者（构思主控）用绝对路径 `~/.local/bin/claude` 启动，绕过包装脚本（见 inbox 20261025T132703Z-executor-ack-001）。用户 2026-10-25 选：“不加固，绕过时界面提示 (Recommended)”。即：保持 T-120 包装脚本做法；后台发现项目终端里前台的 claude/codex 进程没有带 Enchanted 的接入参数时，在窗格里提示“这个会话没接入 Enchanted，状态和主控命令不可用，直接敲 claude（或 codex）重启”，该会话状态显示未知，不显示假状态。只依据进程 argv 这一机械事实。

## Acceptance

- [x] 绕过提示：真实应用中用绝对路径启动 claude，修前无提示且显示假状态，修后窗格提示且状态为未知；正常敲 claude 不出现提示。

- [x] 写出根因并附证据（进程 argv、环境、复现命令）；未能复现时写 INCOMPLETE 与已排除的假设，不写成 PASS。
- [x] 若可修：修前在真实应用（从 Dock/Finder 启动）复现钩子缺失，修后 Stop/UserPromptSubmit 送达后台、侧栏状态随之变化；用户自己在项目终端敲 claude 时同样生效。

## 不做

范围外问题经问题上报。


## Resolution

2026-10-25，PASS。记录见 [RESULTS.md](../../evidence/2026-10-25-batch26/T-184/RESULTS.md)。根因：实测那轮前两次敲 claude 卡在 L01 的“文稿”权限弹窗，操作者第三次用绝对路径 /Users/luckye/.local/bin/claude 启动，绕过了包装脚本，没有 --plugin-dir，插件、钩子、a2a skill 都没加载（证据：仍在运行的主控进程 argv 与环境、该终端 pty.raw 的命令序列）。ready_rev 2（用户选“不加固，绕过时界面提示”）：后台在项目终端每次提交后读前台进程 argv（sysctl KERN_PROCARGS2，只判断不保存），被包装的 claude/codex 缺少接入参数时窗格提示“这个会话没接入 Enchanted…”，侧栏与窗格头状态“未知”，CLI 退出后撤下；判据集中在 terminalClis.ts。修前 main 复现 lcu 的“运行中”假状态（4 项失败），修后三次 PASS 8/8，两个变异被拒，T-174 回归通过。agy 两轮审查 PASS。第二条验收（真实应用中正常敲 claude 钩子送达）在 T-186 装好 0.1.4 后的 lcu 复看里核对。
