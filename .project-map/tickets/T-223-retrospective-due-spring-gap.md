---
id: T-223
title: 复盘日程落在春季跳过的那一小时，due() 算出的时刻晚一小时
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

T-221 第二轮普查时查到的产品缺陷，与 T-221 的根因不同。

`workbench/src/retrospective.ts` 的 `due()` 先在查询当天调用 `setHours(日程小时, 分钟)`，再用 `setDate` 回退到日程所在的星期几。查询当天如果正好是春季跳过日，而日程时刻落在被跳过的那一小时里（例如 America/New_York 的 02:00～02:59），`setHours` 会先把这个不存在的时刻规范成一小时后，回退到目标日期后仍保留这个偏差。

实测（worker 直接调用真实的 `Retrospectives.due()`）：

- 时区 America/New_York，日程每周一 02:30，2026-03-01 起生效；
- 查询时刻 2026-03-08 12:00 EDT。此前最近的周一是 03-02，应得 02:30 EST，即 `2026-03-02T07:30:00.000Z`；
- 实际得到 `2026-03-02T08:30:00.000Z`，即 03:30 EST。

证据为 T-221 worker 证据中的 `r2-product-due-audit.log`，重跑入口 `r2_probe_due.ts`，已归档到 `/Volumes/WD-Elements/a2a-evidence/2026-10-31-batch29/T-221/worker-evidence/`。同一探针在秋季回拨前后的周一 09:00、10:00 两个对照都正确。

影响：只在日程时刻落在跳过的那一小时、且查询发生在跳过日当天时出现；`scheduled_for` 记成错误时刻后，同一周可能再按正确时刻补跑一次。

改法：先选定目标日历日期，再设置墙钟时刻；日程时刻在目标日期本身不存在时（目标日期就是跳过日），按什么规则取时刻要写明，并有对应反例。

## Acceptance

- [x] 修前经真实 `Retrospectives.due()` 留下红态：上面的春季条件下，算出的时刻比日历推算晚一小时。
- [x] 修后同一条件得到 `2026-03-02T07:30:00.000Z`；另核对：
  - 目标日期本身就是跳过日、日程时刻不存在时的取值（例如 America/New_York 的日程设在周日 02:30，查询在 2026-03-08 之后），规则写进代码注释和 README；
  - 秋季回拨日的重复时刻（如 01:30）取哪一次；
  - 普通日、月末、年末不受影响。
  期望值按日历手工推算，不取实现的输出。
- [x] `test_t136_retrospective_e2e.py`、`test_t137_reflect_e2e.py` 在当前日期仍通过。
- [x] 独立审查（agy 只读）无未处理的阻塞意见。

## 不做

改复盘日程的设置界面或存储格式；改 `scheduled_for` 的去重规则。

## Resolution

2026-11-01 关闭，PASS。worktree 提交 `3841c635d`，cherry-pick 到 main 为 `ed5ad223b`，内容与 worker 第三轮冻结候选相同。结果记录见 [evidence/2026-10-31-batch29/T-223/RESULTS.md](../../evidence/2026-10-31-batch29/T-223/RESULTS.md)。

- `due()` 只从查询时刻取本地年月日与星期，用 `new Date(年, 月, 日, 时, 分)` 一步构造目标时刻；未到点时按上周的日期重新构造。不再经过任何带查询时刻墙钟的中间值。规则按 ECMAScript UTC(t) 写进注释与 README：不存在的时刻按转换前偏移顺延，重复时刻取较早一次。
- 修前红态：基线在春季条件下得 `2026-03-02T08:30:00.000Z`，晚一小时。修后纽约 26 项、Nuuk 12 项、Scoresbysund 12 项全过，期望值按日历手写。
- 第二轮候选“先 setDate 再 setHours”在跳过段延到午夜的时区（Nuuk、Scoresbysund）会落到次日、同一周重复触发。agy 第一次审查判为非阻塞，主控扫描时区并经真实 `due()` 复现后改判阻塞；第三轮修好，第二轮候选作为已知坏实现在两组各失败 7 项。三个 worker 变异与主控的回退变异都被抓住。
- T-136 13 项、T-137 10 项在当前日期通过，worker 与主控各跑一次。
- agy 第二次审查的引用大量编造，作废；第三次拆成代码与证据两份，都无阻塞意见，主控逐条核对了引用。非阻塞意见是 worker 那次 T-136 清理 fixture 时 `home` 第一次没删净，只出现过一次，不另开票。
- 证据目录、主控目录、两个审查目录和 17 个测试现场已归档到 `/Volumes/WD-Elements/a2a-evidence/2026-10-31-batch29/T-223/`，清单在证据目录的 `archive/`。
