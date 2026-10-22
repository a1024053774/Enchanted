---
id: T-131
title: 编排后台允许多个 worker 同时运行，同一项目可并行交付
type: build
status: closed
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

- [x] 真实入口（真实后台、socket、终端主控，真实 Claude Code 加脚本化接口）：同一项目两张任务卡、路径不相交，两个 Claude worker 同时在跑（两个窗格同时存活），各自交付、审查、打分、集成到工作分支；两份提交尾注各自对应自己的启动记录；侧栏两个 worker 都挂在终端主控下。修前版本在第二次派发上被拒（`single_worker_slice`）。
- [x] 反例：第三张卡与第一张路径相交、不给理由时派发被拒（`path_overlap`）。
- [x] T-122 正常流程回归通过。

## 不做

不改门禁的交集规则与锁语义；不做并发上限；不改界面。

## Resolution

2026-10-22 关闭，PASS。

- 代码：`5d4fcd26c`（去掉 `single_worker_slice`）、`8f584d45c`（候选 1：审查的共享引用核对放过别的任务经门禁写的引用和工作分支的集成推进）、`c6921bf44`（候选 2：只认门禁给别的任务起的名字，attempt 序号不超过其 fence）、`d436fd390`（候选 3：认验收冲突保留的 `-candidate`/`-base`）；README `85b212a60`、`d436fd390`。
- 证据：`evidence/2026-10-22-batch20/T-131/`。discovery 是去掉限制后第一次真实运行暴露的 `review_shared_refs_changed`；候选 3 的 green、retained-ref、两种外来引用反例 PASS，4 个变异与候选 2 上的红态失败，T-122 回归 23 项 PASS；修前 `03b2d66a3` 在第二次派发被拒（`single_worker_slice`），见候选 2。
- 独立审查（agy gemini-3.8-flash-high）：review-01 PASS 附 P2（前缀放行过宽），review-02 INCOMPLETE（P1 冲突保留引用被误拒），review-03 PASS。
- 已知边界（README）：审查期间用户自己往工作分支提交仍按引用被改拒收；同一仓库登记为两个项目且有同名任务时误拒。冲突保留引用的场景由测试按门禁命名写入，没有真造一次并发合并冲突。
