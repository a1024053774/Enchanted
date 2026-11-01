---
id: T-221
title: 夏令时回拨当天，按天扫描 Codex 记录的循环漏掉次日
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

T-219 第 6 项查到的产品缺陷。证据为 T-219 worker 证据中的 `baseline-06c.json`、`dst-america-02.log`、`dst-utc-02.log`，已随 T-219 归档到 `/Volumes/WD-Elements/a2a-evidence/2026-10-31-batch29/T-219/worker-evidence/`。

下面四处循环都从启动时刻起按本地日历每次加一天（`setDate(getDate() + 1)`），终点却是固定的 `Date.now() + 86_400_000`：

- `workbench/src/nativeLink.ts` 的 `codexRootThreads`
- `workbench/src/panes.ts` 中按天找 Codex 记录的循环（约 1244 行）
- `workbench/src/trajectoryArchive.ts` 的两处循环（约 82、100 行）

本地时间夏令时回拨的那一天，次日同一墙钟时刻距现在是 25 小时，不是 24 小时。所以在启动后的约一小时内，次日的目录不在扫描范围里。2026-10-31 晚间（America/New_York，次日回拨）跑 T-195 时就是这样：测试把次日目录设成不可读，`native_link` 仍报可用，没有置灰。

影响：Codex 按本地日期建记录目录，次日目录要到本地午夜后才会写入，而那时次日已在扫描范围内。所以平时影响很小，主要是 T-195 的“次日不可读即置灰”检查在回拨日会失败。四处循环共用同一个错误，改成一个按本地日历日期比较的扫描范围（从起始日期到本地“明天”，含两端），四处都用它。

第一轮回归又发现同类问题：`test_t136` 的测试时钟用 `datetime.now().astimezone()` 取得固定偏移，再加两天。跨过回拨后，日程时刻差了一小时，定时检查失败（基线同样失败，证据 `diagnostic-t136.log`，已归档到 `/Volumes/WD-Elements/a2a-evidence/2026-10-31-batch29/T-221/worker-evidence/`）。同一类失败已经出现第二次，所以本票连同这一类一起处理：T-136 的测试时钟改为按具名本地时区推算；再在产品和测试代码里普查同类写法（本地日历步长配固定 24 小时、固定偏移跨日推算），逐处判定，能在本票修的修，修不了的登记。

## Acceptance

- [x] 修前经真实入口留下红态：在 `TZ=America/New_York`、启动时刻取回拨日晚间的条件下，扫描范围不含次日（可用注入的时刻调用产品里的同一段日期计算，不另写一份）。
- [x] 修后同一条件下扫描范围含次日；春季跳过、秋季回拨、月末、年末四种边界都核对起止日期，期望值按日历推算，不取实现的输出。
- [x] 四处循环都改用同一段日期计算，代码里不再有“本地日历步长配固定 24 小时终点”的写法。
- [x] `test_t195_native_link_e2e.py` 在当前日期正常运行通过；T-219 的第 6 项改判为已修复并附证据。
- [x] `test_t136` 的定时检查跨夏令时仍按本地墙钟推算日程时刻：修前在跨回拨的条件下失败，修后通过；同类写法的普查结果逐处列出判定。
- [x] 独立审查（agy 只读）无未处理的阻塞意见。

## 不做

改 Codex 记录目录的命名约定；改 `native_link` 的置灰规则。

## Resolution

2026-10-31 关闭，PASS。worktree 提交 `b18af793f`，cherry-pick 到 main 为 `b54b691f7`，树与 worker 第二轮冻结候选相同。结果记录见 [evidence/2026-10-31-batch29/T-221/RESULTS.md](../../evidence/2026-10-31-batch29/T-221/RESULTS.md)。

- 新增 `workbench/src/codexScanDays.ts`：按本地日历日期比较起止，扫到本地明天，含两端。原生链接与窗格扫描从启动当天开始，两处轨迹归档从启动前一天开始。四处循环都改用它，旧的固定 24 小时终点已删除。
- 修前红态：原循环原样抽出后，在 T-219 的实际启动时刻下 196 项检查失败 38 项。修后 196 项全过；8 组用例的期望日期按日历写死，覆盖春季跳过、秋季回拨、月末、年末。四个漏改变异和去掉“前一天”的变异都只在对应检查失败。
- T-195 在回拨前夜运行，16 项全过。T-219 第 6 项据此改判为已修复。
- T-136、T-137 的测试时钟改用 `tests/local_calendar.py`，取与后台 Node 相同的具名时区。修前 T-136 `schedule_fires_once_at_its_time` 失败，修后 T-136 13 项、T-137 10 项全过；固定偏移变异在四个跨切换用例失败。同类写法普查 48 处逐行判定，见证据目录的 `r2-audit-decisions.md`。
- 普查查到 `Retrospectives.due()` 在春季跳过时刻晚一小时，按任务书不改定时产品，登记为 [T-223](T-223-retrospective-due-spring-gap.md)。
- agy 只读审查无阻塞意见。主控核对出几处引用与原始输出对不上，不影响结论。
- 主控独立复跑了日期单测、时钟检查及其变异、T-136、T-137 完整 E2E，结果与 worker 一致。证据目录、主控目录和 25 个测试现场已归档到 `/Volumes/WD-Elements/a2a-evidence/2026-10-31-batch29/T-221/`，清单在证据目录的 `archive/`。
