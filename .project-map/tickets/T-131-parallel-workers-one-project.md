---
id: T-131
title: 编排后台允许多个 worker 同时运行，同一项目可并行交付
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

来源：用户 2026-10-22 逐字：“107 吧多 worker 做出来，早期的调研票关掉，然后还缺的都做”。 T-107 的验收要求同一项目里有 2 个 worker，而后台在 `panes.ts` 的 `createThread` 里用 `single_worker_slice` 限制全后台同时只能有一个 worker 窗格（S1 留下的约束，README“运行时边界”一节有记）。

- 去掉这条限制。门禁已有的并行规则不变：允许路径与活跃 attempt 有交集时拒绝派发，除非主控给出 `overlap-reason`（spec 第 3 节第 1 步）。
- 两个 worker 各自的 worktree、启动记录、钩子信号、提交尾注、交付、审查与集成互不串扰；第二个集成时工作分支已变，按既有规则在新头上重新验收（spec 第 3 节第 7 步）。
- 不加并发上限设置（spec 没有要求）。

## Acceptance

- [ ] 真实入口（真实后台、socket、终端主控，真实 Claude Code 加脚本化接口）：同一项目两张任务卡、路径不相交，两个 Claude worker 同时在跑（两个窗格同时存活），各自交付、审查、打分、集成到工作分支；两份提交尾注各自对应自己的启动记录；侧栏两个 worker 都挂在终端主控下。修前版本在第二次派发上被拒（`single_worker_slice`）。
- [ ] 反例：第三张卡与第一张路径相交、不给理由时派发被拒（`path_overlap`）。
- [ ] T-122 正常流程回归通过。

## 不做

不改门禁的交集规则与锁语义；不做并发上限；不改界面。
