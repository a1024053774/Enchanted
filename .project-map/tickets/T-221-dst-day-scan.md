---
id: T-221
title: 夏令时回拨当天，按天扫描 Codex 记录的循环漏掉次日
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

T-219 第 6 项查到的产品缺陷。证据在 `a2a-worktrees/T-219-evidence/`（`baseline-06c.json`、`dst-america-02.log`、`dst-utc-02.log`），T-219 关闭时随它归档。

下面四处循环都从启动时刻起按本地日历每次加一天（`setDate(getDate() + 1)`），终点却是固定的 `Date.now() + 86_400_000`：

- `workbench/src/nativeLink.ts` 的 `codexRootThreads`
- `workbench/src/panes.ts` 中按天找 Codex 记录的循环（约 1244 行）
- `workbench/src/trajectoryArchive.ts` 的两处循环（约 82、100 行）

本地时间夏令时回拨的那一天，次日同一墙钟时刻距现在是 25 小时，不是 24 小时。所以在启动后的约一小时内，次日的目录不在扫描范围里。2026-10-31 晚间（America/New_York，次日回拨）跑 T-195 时就是这样：测试把次日目录设成不可读，`native_link` 仍报可用，没有置灰。

影响：Codex 按本地日期建记录目录，次日目录要到本地午夜后才会写入，而那时次日已在扫描范围内。所以平时影响很小，主要是 T-195 的“次日不可读即置灰”检查在回拨日会失败。四处循环共用同一个错误，改成一个按本地日历日期比较的扫描范围（从起始日期到本地“明天”，含两端），四处都用它。

## Acceptance

- [ ] 修前经真实入口留下红态：在 `TZ=America/New_York`、启动时刻取回拨日晚间的条件下，扫描范围不含次日（可用注入的时刻调用产品里的同一段日期计算，不另写一份）。
- [ ] 修后同一条件下扫描范围含次日；春季跳过、秋季回拨、月末、年末四种边界都核对起止日期，期望值按日历推算，不取实现的输出。
- [ ] 四处循环都改用同一段日期计算，代码里不再有“本地日历步长配固定 24 小时终点”的写法。
- [ ] `test_t195_native_link_e2e.py` 在当前日期正常运行通过；T-219 的第 6 项改判为已修复并附证据。
- [ ] 独立审查（agy 只读）无未处理的阻塞意见。

## 不做

改 Codex 记录目录的命名约定；改 `native_link` 的置灰规则。

## Resolution

（未开始）
