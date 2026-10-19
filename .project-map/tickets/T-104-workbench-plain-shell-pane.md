---
id: T-104
title: 工作台：不调用模型的普通 zsh 窗格
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

来源同 T-103。现状：主进程只接受主控或当前 worker 的 launch（`main.ts:27`）；`panes.ts` 只有起 Claude 主控和起 Codex worker/reviewer 两条通路；界面里没有新建窗格的入口。AGENTS 第三阶段约束写明"窗格里跑用户的 zsh"，产品里目前没有这条路。

用户的方向：窗格是各家原生 CLI 的交互终端，也包括用户自己的 zsh，a2a 只做编排。

语义由构思主控定（用户未逐条确认，执行主控有硬冲突再上报）：
1. 普通 shell 窗格属于**项目**（cwd 为项目工作目录，也可选任务的 worktree 目录），不绑定 attempt，不是受管 worker，不经门禁认领/交付；它只是用户的终端。
2. 记录：窗格创建与关闭作为事件追加到现有事件流，角色记为 `shell`；窗格里的输入**不**当作对 agent 的用户输入，也不触发"人工介入"（它不是受管 worker 会话）。不采集输入内容到事件流（不是 agent 对话，避免记录密码等）。
3. 启动：用户登录 shell 的 zsh，不传模型相关参数，不写 `~/.zshrc` 等全局配置；环境变量只带项目号。
4. 界面：窗格栏有"新建终端"入口；关闭窗格结束其子进程（沿用现有窗格关闭与重开恢复的语义，普通 shell 不做自动续接，恢复后显示"已结束"）。
5. 同一窗口里这类窗格与 agent 窗格并存，不混淆标识。

## Acceptance

- [ ] 红态：当前无入口、主进程拒绝。绿态：真实 Electron，点"新建终端"出现可输入的 zsh，`echo` 与 `pwd` 正确，cwd 为项目目录。
- [ ] 反例：该窗格输入不进入 agent 的输入记录；关闭后子进程确实结束（进程核对）；重启后台后该窗格显示"已结束"而不是被重新拉起。
- [ ] 事件流里有创建/关闭事件，无输入内容。
- [ ] 不动门禁与受管 worker 窗格的"直接输入记为人工介入"语义；`project_map.py status` 0 问题。

## 不做

不做多标签管理、会话持久化、shell 主题。
