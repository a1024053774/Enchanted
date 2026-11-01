---
id: T-227
title: trace 写入失败后的善后：初次打开失败的终端仍在运行，失败后每帧重复记事件
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

T-212 第三轮独立审查查到两处，主控核对属实，均不阻塞 T-212（[核对记录](../../evidence/2026-10-31-batch29/T-212/controller/REVIEW-agy-r3-controller-check.md)）。两处都在写 trace 失败之后发生；磁盘写满时会走到这里，2026-10-31 晚内置盘就满过一次。

1. **初次打开项目终端时 trace 写入失败，终端仍在运行。**
   - 流程：`workbench/src/panes.ts` 的 `startShell` 先登记 launch，经 `hc.run` 起终端并记 `shell_created`，再 `attachShell`；
   - 初次 attach 的 paint 写 trace 失败时，`attachShell` 明确拒绝（`pane_unavailable`），`startShell` 后面的 `rememberOpen` 不再执行；
   - 结果：hc 终端和其中的 zsh 留在私有 core 里，用户没有拿到窗格；
   - 这个终端仍有记录，`shell_close`、界面的 `pane_layout_close`（对项目终端调用 `closeShell`）和移除项目时回收都能清掉。从侧栏点开它再关掉这条路径还没实测。
2. **窗格记为失败后，每个 DATA 帧仍写 trace，失败一次就再记一条 `trace_write_failed`。**
   - `attachShell` 的 data 处理不因 `pane.failed` 提前返回，`recordFailure` 也不去重；
   - 这不是 T-212 引入的：基线 `4cb88bba7` 里 node-pty 项目终端和受管窗格写 trace 失败时，同样每帧记一次；
   - 影响：程序持续输出时，事件表会一直增长；数据库也写不进时，每帧报一次 `event_write_failed`。

改法要先定：

- 第 1 项：初次打开失败是“没建成”（当场销毁刚起的 hc 终端），还是“建成但失败”（留着供排查，保证界面能看到并关掉）。只选一种，写进代码注释。
- 第 2 项：同一窗格同一种失败只记一次；记为失败后，trace 是否继续写由第 1 项的选择决定。项目终端与受管窗格用同一规则，不留两套。

## Acceptance

- [ ] 先写下这两处可能出错的方式，测试对着它写。
- [ ] 修前经真实入口留下红态，沿用 `workbench/tests/test_t212_trace_failure_e2e.py` 的注入方式：
  - 初次 attach 失败后，私有 core 里仍有该终端，或界面看不到、关不掉它（以所选规则为准）；
  - 窗格失败后继续输出 N 帧，事件表里 `trace_write_failed` 超过 1 条。
- [ ] 修后同一场景：
  - 第 1 项按所选规则成立，并用私有 core 的终端列表与进程表核对；
  - 第 2 项每个窗格只记 1 条；
  - 另一个项目终端照常可用，hc 连接不断。
- [ ] 受管窗格写 trace 失败也只记 1 条，T104 与 T107 回归通过。
- [ ] 独立审查（agy 只读）无未处理的阻塞意见。

## Resolution

（未开始）
