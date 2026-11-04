---
id: T-235
title: T-157/T-165 Stop 重叠场景里，窗格标题栏的状态落后于后台，检查读到“未知”或“运行中”
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by: executor
ready_rev: 1
---

## What to build

T-229 第十三轮回归发现，范围外（T-229 结果记录）：`test_t165_queued_stop_e2e.py --scenario unrelated-stop` 的 `positive_returns_idle_without_regular_recovery` 时好时坏。失败时后台的 `pane_status`、`sidebar_snapshot` 都是 `idle`，后台事件时间线与通过的那次完全相同；但界面里这一 worker 的侧栏行和窗格标题栏都还是“未知”。测试在后台回到空闲后只等 2 秒就读 DOM，之后的截图里已是“空闲”。

- 同一 harness（`test_t157_stop_input_e2e.py`）的三个场景都有：T-165 unrelated-stop、T-165 ordered、T-157 stop-input。T-229 第十四轮里后两者失败（标题栏分别为“未知”“运行中”），基线 `59815ea30` 上各跑 2 次全失败（`r14-base-t157-stop-input-{1,2}`、`r14-base-t165-ordered-{1,2}`）。
- unrelated-stop：基线 `59815ea30`（T-229 之前）上 3 次全失败（T-229 证据 `r13-base-t165-unrelated-stop-{1,2,3}.json`）；T-229 候选上 3 次失败 2 次（`r13-reg-t165-unrelated-stop-{1,3}`，`-2` 通过）。第十一、十二轮各跑一次都通过。所以不是 T-229 引入的。
- 标题栏取的是界面自己刷新的侧栏列表（`app/renderer.tsx` 的 `agentState`），没有在后台状态变化后及时刷新，或刷新时这一行算成了 `unknown`。没有核实是哪一种。

要做的：查清界面这一行为什么在后台已空闲后仍显示“未知”，修在根因处；不要靠加长测试的等待时间。

## Acceptance

- [x] 先写下可能出错的方式，测试对着它写。
- [ ] 修前留红态：上面的场景在基线上重复跑，记下失败次数与当时界面、后台各自的状态。
- [ ] 修后同一场景连续多次通过，且界面状态与后台一致的检查没有放宽。
- [ ] 独立审查（GPT 只读，新开干净会话）无未处理的阻塞意见。

## Resolution

2026-11-03 进展，**INCOMPLETE（未复现）**（[结果](../../evidence/2026-11-03-batch31/T-235/RESULTS.md)）。HEAD 上三个场景各 3 次、基线 `59815ea30` 上 T-157 stop-input 3 次全部通过；把 2 秒等待换成 100 毫秒采样的探针（HEAD 6 次、基线 3 次、满负载 3 次）里，标题栏与侧栏同时在后台空闲后 0–1.4 秒变为空闲。未改代码。审查同意不关闭。推断（未证实）：T-229 当时残留二十多对夹具 core，失败时多显示“未知”，与“侧栏读取出错时全部置为未知”相符。下次出现时记下 `catalogError` 与状态时间序列。

2026-11-04 状态：**INCOMPLETE，等待复现**。用户裁定：“T-235 的状态写好就行.等待发现该错误.”不再主动排查。保持 open：票面状态没有“等待”这一项，所以它仍会出现在可做列表里，但在下次复现之前不做。复现时按上一段记下 `catalogError` 与状态时间序列，再按 Acceptance 留红态、修复。
