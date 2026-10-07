---
id: T-035
title: 门禁 tracer bullet：一次受管任务的正常路径
type: build
status: open
blocked_by: [T-034]
claimed_by:
supersedes:
---

## What to build

用户（或主控 agent）在 Synara 里为一个项目新建受管任务：门禁冻结任务输入与独立 oracle，经 Synara 派出一个 Codex worker 会话（worktree 环境，起点为集成头）；worker 改好代码、本地提交后，用 `a2a_submit` 工具显式交付；门禁在独立 worktree 中运行 oracle，通过后以 CAS 写入集成引用，回收 worker 会话；任务窗口上显示 accepted。本切片只走正常路径；第一步核实 Synara 是否已有 thread 分组、turn 完成信号与内部创建 thread 的接入点。设计见 [spec](../specs/synara-m1-2026-10-07.md) 的"层级模型""门禁""界面"。

## Acceptance

- [ ] 门禁核心位于独立 package，状态变更只经该核心；对上游文件的改动有清单。
- [ ] 在隔离数据目录中，真实 Codex worker 会话完成分页夹具并经 `a2a_submit` 交付；thread 结束或空闲本身不推进状态。
- [ ] 独立 oracle 在新 worktree 中运行通过，集成引用经 CAS 更新并能独立读回；worker 会话被回收。
- [ ] 任务窗口显示该任务的门禁状态变化（截图或录屏存档）。
- [ ] 反例：未调用 `a2a_submit`、或提交身份不符时，任务不会进入验收或集成。

## Resolution

未执行。
