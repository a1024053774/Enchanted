---
id: T-223
title: 复盘日程落在春季跳过的那一小时，due() 算出的时刻晚一小时
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

- [ ] 修前经真实 `Retrospectives.due()` 留下红态：上面的春季条件下，算出的时刻比日历推算晚一小时。
- [ ] 修后同一条件得到 `2026-03-02T07:30:00.000Z`；另核对：
  - 目标日期本身就是跳过日、日程时刻不存在时的取值（例如 America/New_York 的日程设在周日 02:30，查询在 2026-03-08 之后），规则写进代码注释和 README；
  - 秋季回拨日的重复时刻（如 01:30）取哪一次；
  - 普通日、月末、年末不受影响。
  期望值按日历手工推算，不取实现的输出。
- [ ] `test_t136_retrospective_e2e.py`、`test_t137_reflect_e2e.py` 在当前日期仍通过。
- [ ] 独立审查（agy 只读）无未处理的阻塞意见。

## 不做

改复盘日程的设置界面或存储格式；改 `scheduled_for` 的去重规则。

## Resolution

（未开始）
