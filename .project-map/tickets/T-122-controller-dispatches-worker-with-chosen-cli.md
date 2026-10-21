---
id: T-122
title: 主控用 a2a 派发 worker，可选 CLI；worker 与 reviewer 启动即定身份，自动挂到侧栏
type: build
status: open
blocked_by: [T-121]
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：[T-119](T-119-herdr-style-terminals-claimed-roles.md)、[spec](../specs/herdr-style-claimed-roles-2026-10-21.md)。用户 2026-10-21 逐字：“现在只有主控能被我批准后认领,其他的 worker,reviewer 怎么认领呢?这些系统应该让模型通过 a2a 指令运行其他 cli 后自动识别放到侧边吧”。

已批准的执行主控用 `a2a` 派发：指定 CLI（Claude Code 或 Codex）、模型、强度和任务卡。后台在新窗格里带着 worker 角色的权限参数启动该 CLI：不弹批准窗口而越界即拒、可写路径限制、回合信号、会话可续接。每家 CLI 用一个启动适配提供这组能力。

worker 和 reviewer 不申请角色：后台启动时就把角色、任务、attempt 和派发它的主控写进启动记录。侧栏据此把 worker 挂在派发它的主控下面，reviewer 挂在对应任务下面，不需要用户批准，也不从终端文字推断。交付、独立审查、集成沿用现有门禁检查串。

T-121 独立审查指出、属于本票的两点（evidence/2026-10-21-batch19/T-121/review-01.md）：

- 经角色申请成为主控的项目终端不是已登记的会话线程，发给它的收件箱条目会停在 `role_session_missing`，收不到唤醒。
- 终端发起的门禁调用没有父 launch，它派出的 worker 在侧栏里会显示为“未归属”。本票要把派发关系记到这个终端上。

## Acceptance

- [ ] 真实入口：打包测试版里，T-121 经角色申请批准的真实 Claude Code 执行主控派发一个 Claude Code（Sonnet 5.5、medium）worker 到夹具仓库，经交付、独立审查、集成到夹具工作分支。截图、后台库事件读回、Git 引用读回、重现命令留证。
- [ ] 同一流程派发 Codex worker 仍然可用（回归）。
- [ ] 侧栏自动显示：worker 在派发它的主控下面，reviewer 在任务下面，角色、CLI、模型来自启动记录。
- [ ] Claude Code worker 的权限是强制的：越过任务卡路径的写入被拒并留下记录；启动 argv 完整记入启动记录。
- [ ] 没有已批准角色的会话、worker 自己都不能派发；修前版本（任务卡执行者只能是 Codex）跑同一入口失败。
- [ ] `project_map.py status` 0 问题。
