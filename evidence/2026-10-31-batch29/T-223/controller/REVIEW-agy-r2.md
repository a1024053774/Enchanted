# T-223 独立审查报告（第二次审查 / 第三轮候选）

---

## 一、审查意见汇总

本次对第三轮候选进行了全量代码、差异与原始证据核对，**无阻塞意见，无非阻塞意见**。

- **阻塞意见**：0 条
- **非阻塞意见**：0 条

---

## 二、逐项核对

### 1. 根因与改动

- **`due()` 如何确定目标日期与时刻、如何处理本周未到点回退一周**：
  在 [retrospective.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L55-L70)（对应 [change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/change.diff#L20-L40)）中，[`Retrospectives.due`](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L55-L70) 的核心实现为（第 63–66 行）：
  ```ts
  const year = now.getFullYear(), month = now.getMonth();
  const day = now.getDate() - ((now.getDay() - schedule.weekday + 7) % 7);
  let slot = new Date(year, month, day, schedule.hour, schedule.minute, 0, 0);
  if (slot > now) slot = new Date(year, month, day - 7, schedule.hour, schedule.minute, 0, 0);
  ```
  1. 先从查询时刻 `now` 提取本地日历年 `year`、月 `month`，并用纯整数算术 `now.getDate() - ((now.getDay() - schedule.weekday + 7) % 7)` 算出本周目标星期对应的日历日期数字 `day`（[retrospective.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L63-L64)）。
  2. 直接通过多参数构造函数 `new Date(year, month, day, schedule.hour, schedule.minute, 0, 0)` 一步合成目标日历日期与日程墙钟时刻（[retrospective.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L65)）。
  3. 当本周目标槽位尚未到达（`slot > now`）时，**不依赖 `slot` 上可能已被夏令时跳过归一化的日期或时分**，而是直接用未归一化的日历日数字 `day - 7` 与原始 `schedule.hour, schedule.minute` 重新构造上一周槽位：`new Date(year, month, day - 7, schedule.hour, schedule.minute, 0, 0)`（[retrospective.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L66)）。

- **是否还有任何一步依赖查询时刻的墙钟时间**：
  **完全没有**。在 [retrospective.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L55-L70) 中，对 `now` 只调用了 `now.getFullYear()`、`now.getMonth()`、`now.getDate()`、`now.getDay()`（第 63–64 行）以及与 `slot` 的 epoch 毫秒大小比较 `slot > now`（第 66 行）和 `slot < new Date(schedule.effective)`（第 67 行）。既不再调用 `new Date(now)` 携带查询时分秒，也不再调用 `setDate` / `setHours` 或读取 `slot.getDate()`。

- **改动范围与调用方核对**：
  核对 [change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/change.diff#L1-L160)、[candidate-round3.patch](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/candidate-round3.patch#L1-L160) 与 [r3-git-status.log](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-git-status.log#L1-L6)，候选仅改动 3 个文件：
  1. [retrospective.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L58-L66)（仅修改 `due()` 内计算 `slot` 的 9 行注释与代码）；
  2. [README.md](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/README.md#L1186-L1189)（补充 4 行关于 `due()` 日历与 DST 规则的说明）；
  3. [test_t223_retrospective_due.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L1-L115)（新增 115 行回归测试）。
  去重比较 `const ran = this.runs(project).some(run => run.scheduled_for === slot.toISOString());`（[retrospective.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L68)）、SQLite 存储层（[retrospective.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L31-L35)、[L90](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L90)）以及守护进程调用方 [`WorkbenchDaemon.checkRetrospectives`](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/daemon.ts#L105-L120) 均未改动。

---

### 2. 规则与边界（基于 ECMAScript `MakeDay`、`MakeDate`、`UTC(t)` 推理）

代码注释（[retrospective.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L58-L62)）与文档（[README.md](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/README.md#L1186-L1189)）写明的规则与代码实际行为完全一致。按照 ECMAScript 规范，`new Date(year, month, date, hours, minutes, 0, 0)` 先在纯数学日历轴上执行 `MakeDay(year, month, date)` 与 `MakeTime(hours, minutes, 0, 0)`，合成 `t = MakeDate(day, time)`，最后调用一次 `UTC(t)` 将本地墙钟时间转换为 UTC epoch 毫秒：

1. **日期数字小于 `1` 或超过当月天数（跨月、跨年回退）**：
   - `MakeDay(year, month, date)` 先求 `(year, month, 1)` 对应的公历日序号，再做纯整数日偏移 `+ (date - 1)`，每一步都在未施加任何时区偏移的纯格里高利日历天（固定 `86400000 ms`）上完成，随后才与 `MakeTime(schedule.hour, schedule.minute, 0, 0)` 合成为目标日历日的墙钟时间并调用一次 `UTC(t)`。
   - 例如跨月回退（`F7/month-boundary`，[test_t223_retrospective_due.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L40)）：`now = 2026-04-01T12:00:00-04:00`（周三），目标周一（`weekday = 1`），`day = 1 - 2 = -1`；`MakeDay(2026, 3, -1)` 精确落到 `2026-03-30`（3 月有 31 天，`1 + (-1 - 1) = -1` 即 3 月 30 日），再合成 `02:30` 得到 `2026-03-30T02:30:00-04:00 = 2026-03-30T06:30:00.000Z`。
   - 跨年回退（`F8/year-boundary`，[test_t223_retrospective_due.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L41)）：`now = 2027-01-01T12:00:00-05:00`（周五），`day = 1 - 4 = -3`；`MakeDay(2027, 0, -3)` 精确落到 `2026-12-28`，合成 `02:30` 得到 `2026-12-28T02:30:00-05:00 = 2026-12-28T07:30:00.000Z`。
   - 同理，若 `date` 超过当月天数，也会在纯日历轴上顺延至下月对应日期，不会受中间某天时长为 23 小时或 25 小时的影响。

2. **目标日期上日程时刻不存在：跳过 1 小时，以及半小时跳过（如 `Australia/Lord_Howe`）**：
   - 当目标日期为正常存在该时刻的日期（如 `America/New_York` 周一 `2026-03-09 02:30`），`MakeDay` 先锁定周一 `2026-03-09`，完全不经过周日 `2026-03-08` 的缺失窗口，`UTC(t)` 按周一 EDT（`-04:00`）解析出 `2026-03-09T06:30:00.000Z`。
   - 当日程本身定在切换日且时刻落在缺失段内：按 ECMAScript / V8 对 `UTC(t)` 的标准实现，缺失段内的本地墙钟时刻 `t` 按跳变前的旧偏移解释（等价于沿跳变方向顺延一个跳变跨度）：
     - **跳过 1 小时**（如 `America/New_York` 周日 `2026-03-08`，`02:00 EST (-05:00) -> 03:00 EDT (-04:00)`）：日程 `02:30` 按跳变前 `-05:00` 折算为 `2026-03-08T07:30:00.000Z`（即本地 `03:30 EDT`，见 `F4/gap-target-after-normalized-slot`，[test_t223_retrospective_due.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L28)）。
     - **跳过半小时**（如 `Australia/Lord_Howe` 春季跳变 `02:00 (+10:30) -> 02:30 (+11:00)`，跳过 30 分钟）：若日程设在缺失段内（如 `02:15`），`MakeDate` 合成目标日 `02:15`，`UTC(t)` 按跳变前偏移 `+10:30` 解释，得到跳变后 `+11:00` 下的 `02:45`（顺延 30 分钟）；若在顺延后的时刻前查询触发 `slot > now`，第 66 行用 `new Date(year, month, day - 7, schedule.hour, schedule.minute, 0, 0)` 重新以原始 `02:15` 和 `day - 7` 构造上一周槽位，上一周仍保持 `02:15 (+10:30)`，不会把这 30 分钟偏移带回上一周。

3. **跳过段一直延到本地午夜（`America/Nuuk` / `America/Scoresbysund`）**：
   - 在 `America/Nuuk`（及 `America/Scoresbysund`），2026 年夏令时于周六 `2026-03-28 23:00 (-02:00)` 直接跳至周日 `2026-03-29 00:00 (-01:00)`，周六本地 `23:00–23:59:59.999` 不存在（[nuuk-probe.log](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/nuuk-probe.log#L2-L6)）。
   - **情况 A（日程在周六正常时刻如 `10:00`，在周日或周四深夜 `23:30` 查询）**：`due()` 只取 `now` 的年月日与星期算出 `day = 28`，直接构造 `new Date(2026, 2, 28, 10, 0, 0, 0)`，从未在 `2026-03-28` 上构造过 `23:30`，因此精确得到周六 `2026-03-28T10:00:00-02:00 = 2026-03-28T12:00:00.000Z`。
   - **情况 B（日程本身在周六缺失段 `23:30`）**：`day = 28`，`slot = new Date(2026, 2, 28, 23, 30, 0, 0)` 被 `UTC(t)` 按跳变前 `-02:00` 归一化为 `2026-03-29T01:30:00.000Z`（本地周日 `2026-03-29 00:30 -01:00`，此时 `slot.getDate()` 已变成 `29`）。
     - 若在周日 `2026-03-29T00:15:00-01:00`（`01:15Z`）查询，此时 `slot (01:30Z) > now (01:15Z)`，触发回退一周分支（[retrospective.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L66)）。因为回退使用的是未归一化的 `day - 7 = 28 - 7 = 21` 和原始 `23:30`，而非 `slot.getDate() - 7`（`29 - 7 = 22`），所以回退到上周六 `2026-03-21T23:30:00-02:00 = 2026-03-22T01:30:00.000Z`，既没有污染时分，也没有因跨午夜归一化而错退到上周日 `2026-03-22T23:30:00-02:00 = 2026-03-23T01:30:00.000Z`。

4. **秋季重复时刻（Fall-back overlap）**：
   - 如 `America/New_York` 周日 `2026-11-01`，本地 `01:00–01:59:59.999` 出现两次（第一次 EDT `-04:00`，第二次 EST `-05:00`）。
   - 对于 `new Date(2026, 10, 1, 1, 30, 0, 0)`，`UTC(t)` 确定性地选择第一次出现的 `2026-11-01T01:30:00-04:00 = 2026-11-01T05:30:00.000Z`（见 [README.md](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/README.md#L1189) 及 `F5` 用例组 [test_t223_retrospective_due.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L33-L37)）。
   - 在第一次 `01:30 EDT`（`05:30Z`）之前查询（如 `01:15 EDT = 05:15Z`），`slot > now` 为真，回退到上周日 `2026-10-25T01:30:00-04:00 = 2026-10-25T05:30:00.000Z`；在第一次 `01:30 EDT` 之后（包括第二次 `01:15 EST = 06:15Z` 及第二次 `01:30 EST = 06:30Z`），`slot` 恒为 `'2026-11-01T05:30:00.000Z'` 且 `slot <= now`，一旦第一次触发记录了 `scheduled_for = '2026-11-01T05:30:00.000Z'`，第二次经过 `01:30 EST` 时去重检查（[retrospective.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L68)）会返回 `null`，不会重复执行。

5. **是否有遗漏边界、是否会阻塞本票**：
   - 闰年 2 月 29 日跨月由 `MakeDay` 的格里高利历规则原生处理；全 IANA 时区扫描（[scan_midnight_gaps.mjs](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/scan_midnight_gaps.mjs#L1-L24)、[nuuk-probe.log](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/nuuk-probe.log#L1-L6)）证实 2026–2028 年间跨午夜 DST 跳变仅有 `America/Nuuk` 与 `America/Scoresbysund`。没有任何遗漏边界会阻塞本票。

---

### 3. 测试 [`test_t223_retrospective_due.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts) 核对

- **Nuuk / Scoresbysund 组（`midnightGapCases`，共 12 项）全量日历手算推算**：
  在 [test_t223_retrospective_due.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L61-L81) 中，`America/Nuuk` 与 `America/Scoresbysund` 共享 `midnightGapCases`（第 61–77 行），默认日程为 `weekday: 6`（周六）、`hour: 10`、`minute: 0`、`effective: '2026-03-01T00:00:00-02:00'`（第 80–81 行）。两时区规则在该区间一致：2026 年于周六 `2026-03-28 23:00 (-02:00)` 跳至周日 `2026-03-29 00:00 (-01:00)`；2027 年于周六 `2027-03-27 23:00 (-02:00)` 跳至周日 `2027-03-28 00:00 (-01:00)`。逐项手算如下：
  1. `F12/sunday-late-query`（[L62](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L62)）：`now = 2026-03-29T23:30:00-01:00`（周日，`getDay()=0`），日程周六 `10:00`。`day = 29 - ((0 - 6 + 7) % 7) = 28`。目标周六 `2026-03-28 10:00` 处于跳变前 `-02:00`，換算 UTC 为 `2026-03-28T12:00:00.000Z`（`<= now`）。与 `expected: '2026-03-28T12:00:00.000Z'` 一致。
  2. `F12/thursday-late-query`（[L63](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L63)）：`now = 2026-04-02T23:30:00-01:00`（周四，`getDay()=4`），日程周六 `10:00`。`day = 2 - ((4 - 6 + 7) % 7) = 2 - 5 = -3`。`MakeDay(2026, 3, -3)` 为 3 月 `31 - 3 = 28` 日（周六 `2026-03-28`），`10:00 -02:00` 换算 UTC 为 `2026-03-28T12:00:00.000Z`。与 `expected: '2026-03-28T12:00:00.000Z'` 一致。
  3. `F12/already-ran-Saturday`（[L64-L66](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L64-L66)）：`now = 2026-03-29T23:30:00-01:00`，已存 `scheduled_for: '2026-03-28T12:00:00.000Z'`。目标槽位为 `'2026-03-28T12:00:00.000Z'`，命中去重返回 `null`。与 `expected: null` 一致。
  4. `F12/Saturday-query-control`（[L67](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L67)）：`now = 2026-03-28T10:30:00-02:00`（周六 `10:30`），日程周六 `10:00`。`day = 28`，`2026-03-28 10:00 -02:00 = 2026-03-28T12:00:00.000Z <= now (12:30Z)`。与 `expected: '2026-03-28T12:00:00.000Z'` 一致。
  5. `F12/gap-target-after-normalized-slot`（[L68](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L68)）：日程周六 `23:30`（位于周六 `23:00 -> 周日 00:00` 缺失段），`now = 2026-03-29T12:00:00-01:00`（周日 `13:00Z`）。`day = 28`，`2026-03-28 23:30` 按跳变前 `-02:00` 归一化为 `2026-03-29T01:30:00.000Z`（`<= 13:00Z`）。与 `expected: '2026-03-29T01:30:00.000Z'` 一致。
  6. `F12/before-normalized-slot`（[L69](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L69)）：日程周六 `23:30`，`now = 2026-03-29T00:15:00-01:00`（周日 `01:15Z`）。本周槽位归一化后为 `2026-03-29T01:30:00.000Z > now (01:15Z)`，未到点回退至上周六 `day - 7 = 21`，即 `2026-03-21 23:30 -02:00 = 2026-03-22T01:30:00.000Z`。与 `expected: '2026-03-22T01:30:00.000Z'` 一致。
  7. `F12/exact-normalized-slot`（[L70](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L70)）：日程周六 `23:30`，`now = 2026-03-29T00:30:00-01:00`（`01:30Z`）。`slot` 为 `2026-03-29T01:30:00.000Z`，`slot > now` 为假，返回 `'2026-03-29T01:30:00.000Z'`。与 `expected` 一致。
  8. `F12/next-week-before-slot`（[L71](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L71)）：日程周六 `23:30`，`now = 2026-04-04T23:29:59.999-01:00`（下周六到点前 1 毫秒）。本周六 `2026-04-04 23:30 -01:00 = 2026-04-05T00:30:00.000Z > now`，回退至 `day - 7 = 4 - 7 = -3` 即上周六 `2026-03-28 23:30`，经跳变归一化后为 `'2026-03-29T01:30:00.000Z'`。与 `expected` 一致。
  9. `F12/next-week-exact-slot`（[L72](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L72)）：日程周六 `23:30`，`now = 2026-04-04T23:30:00-01:00`。本周六 `2026-04-04 23:30 -01:00 = 2026-04-05T00:30:00.000Z <= now`。与 `expected: '2026-04-05T00:30:00.000Z'` 一致。
  10. `F12/gap-target-already-ran`（[L73-L74](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L73-L74)）：日程周六 `23:30`，`now = 2026-03-29T12:00:00-01:00`，已存 `scheduled_for: '2026-03-29T01:30:00.000Z'`，去重命中返回 `null`。与 `expected: null` 一致。
  11. `F12/2027-sunday-late-query`（[L75](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L75)）：`now = 2027-03-28T23:30:00-01:00`（周日），日程周六 `10:00`。`day = 27`，`2027-03-27 10:00 -02:00 = 2027-03-27T12:00:00.000Z`。与 `expected: '2027-03-27T12:00:00.000Z'` 一致。
  12. `F12/2027-before-normalized-slot`（[L76](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L76)）：日程周六 `23:30`，`now = 2027-03-28T00:15:00-01:00`（`01:15Z`）。本周六 `2027-03-27 23:30` 归一化为 `2027-03-28T01:30:00.000Z > now`，回退至 `day - 7 = 20` 即上周六 `2027-03-20 23:30 -02:00 = 2027-03-21T01:30:00.000Z`。与 `expected: '2027-03-21T01:30:00.000Z'` 一致。

- **纽约组与第一次审查时相比有没有改动**：
  核对 [test_t223_retrospective_due.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L19-L55) 与 [REVIEW-agy-r1.md](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/REVIEW-agy-r1.md#L58-L86)，`newYorkCases` 的 26 个用例名称、输入时间、预设记录与期望值**完全未改动**。

- **真实 `Retrospectives.due()` 调用与显式 TZ 校验**：
  - 测试在 [test_t223_retrospective_due.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L15) 动态导入目标 `retrospective.ts` 的 `Retrospectives` 类，第 90–92 行实例化并调用 `retrospectives.saveSchedule(...)`，第 102 行调用真实的 `retrospectives.due('demo', now)`。
  - 第 11–13 行拿到命令行传入的 `zone`（默认 `'America/New_York'`），在 [第 12 行](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L12) 强制执行 `assert.equal(process.env.TZ, zone, 'the requested case group must match explicit TZ');`，并在 [第 83 行](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L83) 校验 `assert(Object.hasOwn(groups, zone), 'unknown TZ group: ' + zone);`。
  - 负向证据 [r3-wrong-tz.log](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-wrong-tz.log#L1-L27) 验证了当 `TZ=UTC` 运行默认组 `'America/New_York'` 时，立即在第 12 行抛出 `AssertionError [ERR_ASSERTION]: the requested case group must match explicit TZ`（`+ 'UTC'` vs `- 'America/New_York'`），并以 `exit_code=1` 拒绝运行（第 27 行）。

- **断言是否会被放宽、跳过或吞掉**：
  **不会**。每个用例在 [第 103–104 行](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L103-L104) 执行严格相等断言 `assert.equal(actual, c.expected, c.name)` 与入参不可变断言 `assert.equal(now.toISOString(), originalNow, 'due() must not mutate the caller Date')`；若抛出异常，`catch` 块（第 106–107 行）将 `pass: false` 记录进 `results`，并在 [第 110 行](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L110) 汇总 `const pass = results.every(row => row.pass)`，在 [第 115 行](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L115) 设置 `process.exitCode = pass ? 0 : 1`。没有任何跳过或吞异常分支。

---

### 4. 红绿态与变异核对

#### （1）Worker 证据

1. **`evidence/r3-baseline/`（基线 `76f969963` 红态）**：
   见 [evidence/r3-baseline/summary.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-baseline/summary.json#L1-L127)：
   - `America/New_York`（[America--New_York.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-baseline/America--New_York.json#L196-L350)，`exit_code: 1`，20 通过 / **6 失败**）：
     - `F1/spring-forward-monday-after-sunday-gap`：`actual = '2026-03-09T07:30:00.000Z'`，`expected = '2026-03-09T06:30:00.000Z'`（[L202-L204](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-baseline/America--New_York.json#L202-L204)）；
     - `F4/gap-target-before-normalized-slot`：`actual = '2026-03-01T08:30:00.000Z'`，`expected = '2026-03-01T07:30:00.000Z'`（[L235-L237](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-baseline/America--New_York.json#L235-L237)）；
     - `F4/2027-gap-target-before-normalized-slot`：`actual = '2027-03-07T08:30:00.000Z'`，`expected = '2027-03-07T07:30:00.000Z'`（[L248-L250](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-baseline/America--New_York.json#L248-L250)）；
     - `F11/already-ran-canonical-slot`：`actual = '2026-03-09T07:30:00.000Z'`，`expected = null`（[L316-L318](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-baseline/America--New_York.json#L316-L318)）；
     - `F11/2027-spring-forward-monday-after-sunday-gap`：`actual = '2027-03-15T07:30:00.000Z'`，`expected = '2027-03-15T06:30:00.000Z'`（[L339-L341](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-baseline/America--New_York.json#L339-L341)）；
     - `F11/2027-already-ran-canonical-slot`：`actual = '2027-03-15T07:30:00.000Z'`，`expected = null`（[L347-L349](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-baseline/America--New_York.json#L347-L349)）。
   - `America/Nuuk`（[America--Nuuk.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-baseline/America--Nuuk.json#L103-L170)，`exit_code: 1`，10 通过 / **2 失败**）与 `America/Scoresbysund`（[America--Scoresbysund.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-baseline/America--Scoresbysund.json#L103-L170)，`exit_code: 1`，10 通过 / **2 失败**）：
     - `F12/before-normalized-slot`：`actual = '2026-03-22T02:30:00.000Z'`，`expected = '2026-03-22T01:30:00.000Z'`（[America--Nuuk.json#L134-L136](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-baseline/America--Nuuk.json#L134-L136)）；
     - `F12/2027-before-normalized-slot`：`actual = '2027-03-21T02:30:00.000Z'`，`expected = '2027-03-21T01:30:00.000Z'`（[America--Nuuk.json#L167-L169](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-baseline/America--Nuuk.json#L167-L169)）。
     - **原因符合预期**：基线先 `setHours(23, 30)` 再 `setDate`，在周日 `00:15`（`now`）上先 `setHours(23, 30)` 变成周日 `23:30 (-01:00)`，再退 8 天到上周六 `23:30 (-02:00)` 时只执行 `setDate`，没有重设 `schedule.hour`，或在跳变日先归一化到 `00:30` 再 `setDate(slot.getDate() - 7)` 污染了时分，导致多偏 1 小时（`02:30Z` 而非 `01:30Z`）。

2. **`evidence/r3-round2-red/`（第二轮候选红态：使用查询时分秒回退日期，再 `setHours`）**：
   见 [evidence/r3-round2-red/summary.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-round2-red/summary.json#L1-L158)：
   - `America/New_York`（[America--New_York.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-round2-red/America--New_York.json#L196-L333)）：26 项全部通过（`exit_code: 0`）。
   - `America/Nuuk`（[America--Nuuk.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-round2-red/America--Nuuk.json#L103-L185)）与 `America/Scoresbysund`（[America--Scoresbysund.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-round2-red/America--Scoresbysund.json#L103-L185)）各 `exit_code: 1`，5 通过 / **7 失败**：
     - `F12/sunday-late-query`：`actual = '2026-03-29T11:00:00.000Z'`，`expected = '2026-03-28T12:00:00.000Z'`（[America--Nuuk.json#L109-L110](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-round2-red/America--Nuuk.json#L109-L110)）；
     - `F12/thursday-late-query`：`actual = '2026-03-29T11:00:00.000Z'`，`expected = '2026-03-28T12:00:00.000Z'`（[L117-L118](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-round2-red/America--Nuuk.json#L117-L118)）；
     - `F12/already-ran-Saturday`：`actual = '2026-03-29T11:00:00.000Z'`，`expected = null`（[L125-L126](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-round2-red/America--Nuuk.json#L125-L126)）；
     - `F12/before-normalized-slot`：`actual = '2026-03-23T01:30:00.000Z'`，`expected = '2026-03-22T01:30:00.000Z'`（[L143-L144](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-round2-red/America--Nuuk.json#L143-L144)）；
     - `F12/next-week-before-slot`：`actual = '2026-03-30T00:30:00.000Z'`，`expected = '2026-03-29T01:30:00.000Z'`（[L156-L157](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-round2-red/America--Nuuk.json#L156-L157)）；
     - `F12/2027-sunday-late-query`：`actual = '2027-03-28T11:00:00.000Z'`，`expected = '2027-03-27T12:00:00.000Z'`（[L174-L175](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-round2-red/America--Nuuk.json#L174-L175)）；
     - `F12/2027-before-normalized-slot`：`actual = '2027-03-22T01:30:00.000Z'`，`expected = '2027-03-21T01:30:00.000Z'`（[L182-L183](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-round2-red/America--Nuuk.json#L182-L183)）。
     - **原因符合预期**：第二轮候选带着查询时刻 `23:30` 回退到周六 `2026-03-28 23:30` 时撞入跨午夜缺失段，被推到周日 `2026-03-29 00:30`，再 `setHours(10, 0)` 就错算成周日 `2026-03-29 10:00 (-01:00) = 11:00Z`；而在 `before-normalized-slot` 中，因 `slot.getDate()` 已变成周日 `29`，`slot.setDate(slot.getDate() - 7)` 退到了上周日 `22` 日 `23:30 (-02:00) = 2026-03-23T01:30:00.000Z`（错了一整天）。

3. **`evidence/r3-green/`（第三轮候选绿态）**：
   见 [evidence/r3-green/summary.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-green/summary.json#L1-L44) 及 [America--New_York.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-green/America--New_York.json#L1-L334)（26/26 通过）、[America--Nuuk.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-green/America--Nuuk.json#L1-L165)（12/12 通过）、[America--Scoresbysund.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-green/America--Scoresbysund.json#L1-L165)（12/12 通过）：三组共 50 次断言全部 `status: "PASS"`，`exit_code: 0`。

4. **`evidence/r3-mutants/`（三个变异体全部被杀死）**：
   见 [evidence/r3-mutants/summary.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-mutants/summary.json#L1-L397)（定义见 [r3_mutants.py](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3_mutants.py#L9-L26)）：
   - `hours-before-date`（先设时分再减天数，但回退分支重设时分，[summary.json#L2-L133](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-mutants/summary.json#L2-L133)）：
     - `America/New_York` 失败 4 项（`F1/spring-forward-monday-after-sunday-gap` `'2026-03-09T07:30:00.000Z'`、`F11/already-ran-canonical-slot` `'2026-03-09T07:30:00.000Z'`、`F11/2027-spring-forward-monday-after-sunday-gap` `'2027-03-15T07:30:00.000Z'`、`F11/2027-already-ran-canonical-slot` `'2027-03-15T07:30:00.000Z'`）；
     - `America/Nuuk` 与 `America/Scoresbysund` 各失败 3 项（`F12/before-normalized-slot` `'2026-03-23T01:30:00.000Z'`、`F12/next-week-before-slot` `'2026-03-30T00:30:00.000Z'`、`F12/2027-before-normalized-slot` `'2027-03-22T01:30:00.000Z'`）。
   - `date-only-rollback`（`slot > now` 分支只调 `slot.setDate(slot.getDate() - 7)` 不重设时分，[summary.json#L135-L232](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-mutants/summary.json#L135-L232)）：
     - `America/New_York` 失败 2 项（`F4/gap-target-before-normalized-slot` `'2026-03-01T08:30:00.000Z'` vs `'2026-03-01T07:30:00.000Z'`、`F4/2027-gap-target-before-normalized-slot` `'2027-03-07T08:30:00.000Z'` vs `'2027-03-07T07:30:00.000Z'`）；
     - `America/Nuuk` 与 `America/Scoresbysund` 各失败 2 项（`F12/before-normalized-slot` `'2026-03-22T02:30:00.000Z'` vs `'2026-03-22T01:30:00.000Z'`、`F12/2027-before-normalized-slot` `'2027-03-21T02:30:00.000Z'` vs `'2027-03-21T01:30:00.000Z'`）。
   - `query-clock-round2`（即第二轮写法，[summary.json#L234-L396](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-mutants/summary.json#L234-L396)）：
     - `America/New_York` 失败 0 项；`America/Nuuk` 与 `America/Scoresbysund` 各失败 7 项（与上述 `r3-round2-red` 完全一致）。

#### （2）主控独立复跑证据（`controller/r3/`）

见 [controller/r3/runs.log](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/runs.log#L1-L34) 与 [run-ctl-r3.sh](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/run-ctl-r3.sh#L1-L59)：
1. **`green-*` 三组**：[green-New_York.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/green-New_York.json#L1-L334)、[green-Nuuk.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/green-Nuuk.json#L1-L165)、[green-Scoresbysund.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/green-Scoresbysund.json#L1-L165) 全部 `status: "PASS"`，`exit=0`（[runs.log#L1-L6](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/runs.log#L1-L6)）。
2. **`base-red-*` 三组**：[base-red-New_York.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/base-red-New_York.json#L196-L350)（失败 6 项）、[base-red-Nuuk.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/base-red-Nuuk.json#L103-L170)（失败 2 项）、[base-red-Scoresbysund.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/base-red-Scoresbysund.json#L103-L170)（失败 2 项），全部 `exit=1`（[runs.log#L7-L12](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/runs.log#L7-L12)），失败项与失败值同 worker `r3-baseline` 完全一致。
3. **`round2-red-*` 三组**：[round2-red-New_York.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/round2-red-New_York.json#L1-L334)（`exit=0`），[round2-red-Nuuk.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/round2-red-Nuuk.json#L103-L185)（失败 7 项，`exit=1`），[round2-red-Scoresbysund.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/round2-red-Scoresbysund.json#L103-L185)（失败 7 项，`exit=1`），失败项与失败值同 worker `r3-round2-red` 完全一致。
4. **`mutant-slot-rollback-*` 三组**：
   见 [mutant-slot-rollback.diff](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/mutant-slot-rollback.diff#L1-L11)，该变异将第 66 行 `day - 7` 改为读取归一化后的 `slot.getDate() - 7`：
   ```ts
   if (slot > now) slot = new Date(slot.getFullYear(), slot.getMonth(), slot.getDate() - 7, schedule.hour, schedule.minute, 0, 0);
   ```
   - [mutant-slot-rollback-New_York.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/mutant-slot-rollback-New_York.json#L1-L334)：26/26 通过（`exit=0`，因纽约 `02:30 -> 03:30` 不跨午夜，`slot.getDate()` 未变）。
   - [mutant-slot-rollback-Nuuk.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/mutant-slot-rollback-Nuuk.json#L131-L170) 与 [mutant-slot-rollback-Scoresbysund.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/mutant-slot-rollback-Scoresbysund.json#L131-L170)：各 `exit=1`，失败 2 项：
     - `F12/before-normalized-slot`：`actual = '2026-03-23T01:30:00.000Z'`，`expected = '2026-03-22T01:30:00.000Z'`（[mutant-slot-rollback-Nuuk.json#L135-L136](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/mutant-slot-rollback-Nuuk.json#L135-L136)）；
     - `F12/2027-before-normalized-slot`：`actual = '2027-03-22T01:30:00.000Z'`，`expected = '2027-03-21T01:30:00.000Z'`（[mutant-slot-rollback-Nuuk.json#L168-L169](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/mutant-slot-rollback-Nuuk.json#L168-L169)）。
     - **证明了第 66 行必须使用未归一化的 `day - 7` 而不能读 `slot.getDate()`**。
5. **`nuuk-probe-candidate.log`**：
   见 [nuuk-probe-candidate.log](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/nuuk-probe-candidate.log#L1-L8)（[runs.log#L28-L29](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/runs.log#L28-L29)），4 个探测用例（`sunday_late_query`、`thursday_late_query`、`already_ran_saturday`、`saturday_query_control`）全部 `ok: true`，`exit=0`。

---

### 5. T-136、T-137 当前日期端到端与清理异常判断

- **Worker 的 E2E 结果**：
  - [evidence/r3-t136-summary.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-t136-summary.json#L1-L244)（日志 [r3-t136.log](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-t136.log#L1-L3)，`exit_code=0`）：`status: "PASS"`，当前日期 `2026-11-01`（`due` 算出 `'2026-11-01T00:00:00.000Z'`，[L73](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-t136-summary.json#L73)），全部 13 项检查（`schedule_triggered_once`、`retrospective_row_persisted`、`artifact_has_evidence_and_findings`、`dispatch_created_and_adopted`、`adopted_dispatch_creates_card`、`second_due_check_deduped`、`failing_command_rejected`、`failing_command_left_no_card`、`Dismiss_updates_status`、`Snooze_keeps_snoozed_until`、`manual_run_retrospective_now`、`real_electron_ui_renders_retrospectives`、`sqlite_counts_match_flow`）均为 `pass: true`（第 189–242 行）。
  - [evidence/r3-t137-summary.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-t137-summary.json#L1-L252)（日志 [r3-t137.log](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-t137.log#L1-L3)，`exit_code=0`）：`status: "PASS"`，全部 10 项检查（`trigger_to_report_under_60s`、`report_sections_and_4_citations`、`three_distinct_proposals_with_evidence`、`two_supported_apply_kinds_present`、`apply_skill_edit_writes_and_reloads_within_1s`、`apply_task_card_creates_board_card`、`applied_proposals_linked_in_sqlite`、`rejected_proposal_writes_nothing`、`dismissed_proposal_keeps_note`、`real_electron_ui_renders_reflect`）均为 `pass: true`（第 210–251 行）。

- **主控的 E2E 独立复跑结果**：
  - [controller/r3/t136-summary.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/t136-summary.json#L1-L244)（[runs.log#L30-L31](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/runs.log#L30-L31) `exit=0`）：`status: "PASS"`，13 项检查全部 `pass: true`。
  - [controller/r3/t137-summary.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/t137-summary.json#L1-L252)（[runs.log#L32-L33](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/runs.log#L32-L33) `exit=0`）：`status: "PASS"`，10 项检查全部 `pass: true`。

- **对 `evidence/r3-t136-cleanup-anomaly.json` 的判断**：
  核对 [r3-t136-cleanup-anomaly.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-t136-cleanup-anomaly.json#L1-L382)、[r3-t136-cleanup.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-t136-cleanup.json#L1-L386) 以及测试脚本 [test_t136_retrospective_e2e.py](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t136_retrospective_e2e.py#L325-L350)：
  1. 在 [test_t136_retrospective_e2e.py](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t136_retrospective_e2e.py#L325-L347) 中，全部 13 项产品检查在 `try` 块内完成后，`finally` 块先关闭了 Electron 与 Workbench 守护进程（`electron.stop()`、`daemon.stop()`，第 341–346 行），随后写出 `summary.json` 并返回退出码 `0`（[r3-t136.log](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-t136.log#L3) `exit_code=0`）。
  2. 清理异常发生在测试进程已正常退出之后，外层辅助脚本对临时夹具目录 `/private/tmp/t136-nm7m0cmw` 调用 `shutil.rmtree()` 时抛出 `OSError: [Errno 66] Directory not empty: 'home'`（[r3-t136-cleanup-anomaly.json#L367-L380](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-t136-cleanup-anomaly.json#L367-L380)），属于 macOS 下 Electron（Chromium 子进程）退出瞬间异步释放临时 `HOME` 目录句柄的已知宿主文件系统竞态。
  3. Worker 保留了完整的现场文件与重跑对比（[r3-t136-cleanup.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-t136-cleanup.json#L1-L386)），且主控独立复跑 [controller/r3/t136-summary.json](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/t136-summary.json#L1-L244) 也零异常通过。因此**该异常不可能掩盖任何产品问题**。

---

### 6. 第一次审查意见与主控改判核对

- **主控改判依据在证据里完全成立**：
  1. 第一次审查报告 [REVIEW-agy-r1.md](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/REVIEW-agy-r1.md#L15-L36) 指出第二轮候选 `slot.setDate(now.getDate() - ...)` 仍携带查询时刻 `now` 的时分秒做日期回退，但在仅考虑 `00:00–04:00` 切换的前提下标为“非阻塞”。
  2. 主控在 [REVIEW-agy-r1-controller-check.md](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/REVIEW-agy-r1-controller-check.md#L11-L20) 中通过 [scan_midnight_gaps.mjs](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/scan_midnight_gaps.mjs#L1-L24) 扫描全部 `Intl.supportedValuesOf('timeZone')`，并用 [nuuk-probe.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/nuuk-probe.ts#L1-L24) 生成原始输出 [nuuk-probe.log](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/nuuk-probe.log#L1-L27)：在真实 IANA 时区 `America/Nuuk` 与 `America/Scoresbysund` 下，2026-03-28 周六 `23:00 (-02:00)` 跳至周日 `00:00 (-01:00)`，第二轮候选在周日或周四 `23:30` 查询周六 `10:00` 的日程时，真实算出 `'2026-03-29T11:00:00.000Z'`（周日 `10:00`），相比正确的 `'2026-03-28T12:00:00.000Z'`（周六 `10:00`）整整偏了 23 小时且使周六已跑过的复盘去重失效（[nuuk-probe.log#L8-L25](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/nuuk-probe.log#L8-L25)）。因此主控将该条改判为**阻塞**完全成立。
- **第三轮是否解决了它**：
  **已彻底解决**。第三轮候选不再使用任何中间时刻锚点（也没有采用正午 `12:00` 这种折中锚点），而是直接以 `new Date(year, month, day, schedule.hour, schedule.minute, 0, 0)` 和 `new Date(year, month, day - 7, schedule.hour, schedule.minute, 0, 0)` 一步合成目标日历日期与日程时刻（[retrospective.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L63-L66)），在 [nuuk-probe-candidate.log](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/nuuk-probe-candidate.log#L1-L8) 及 `America/Nuuk`、`America/Scoresbysund` 全部 24 次测试断言中 100% 通过。

---

### 7. 设计核对

核对 [change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/change.diff#L1-L160) 与 [retrospective.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L55-L70)：
- 代码在根因层直接用 4 行日历构造替换了原先有缺陷的 5 行 `new Date(now)` + `setDate`/`setHours` 顺序修改；
- **没有任何**为兼容或“保险”添加的 fallback、重试、双写、平行 API 或吞异常。

---

### 8. 环境与数据边界核对

- [test_t223_retrospective_due.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L88-L108) 全程仅使用 `new DatabaseSync(':memory:')` 内存 SQLite，並在 `finally` 中调用 `db.close()`。
- [test_t136_retrospective_e2e.py](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t136_retrospective_e2e.py#L29-L115) 与 [test_t137_reflect_e2e.py](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t137_reflect_e2e.py#L36-L102) 均在 `/private/tmp` 下的独立临时目录中创建隔离的 `HOME`、`workbench.sqlite` 与本地脚本化 fake-claude，完全不触碰真实用户数据、Herdr 或 `hc`。

---

## 三、`ticket.md` 验收条目核对表

严格对照 [ticket.md](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/ticket.md#L34-L41) 的 6 条验收条件逐条判定：

| # | `ticket.md` 验收条目 | 状态 | 依据文件与行号 |
| :- | :--- | :-: | :--- |
| 1 | 在跨春令时切换周（例如 `America/New_York` 2026-03-08 切换后，周一 02:30 的日程在周一 12:00 检查）下，`due()` 返回的 `scheduled_for` 对应当地 02:30（`2026-03-09T06:30:00.000Z`），而不是偏移到 03:30（`07:30Z`）。 | `PASS` | 代码：[retrospective.ts#L63-L66](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L63-L66)；测试定义：[test_t223_retrospective_due.ts#L20](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L20)；绿态输出：[evidence/r3-green/America--New_York.json#L198-L201](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-green/America--New_York.json#L198-L201)、[controller/r3/green-New_York.json#L198-L201](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/green-New_York.json#L198-L201) |
| 2 | 在跨秋令时切换周、跨月/跨年回退、以及同日“尚未到点 vs 已到点”边界下，`due()` 返回的 `scheduled_for` 与当地日历和配置时刻一致。 | `PASS` | 测试定义：[test_t223_retrospective_due.ts#L22-L54](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L22-L54)、[L61-L77](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L61-L77)；绿态输出：[evidence/r3-green/America--New_York.json#L203-L332](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-green/America--New_York.json#L203-L332)、[evidence/r3-green/America--Nuuk.json#L103-L163](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-green/America--Nuuk.json#L103-L163)、[evidence/r3-green/America--Scoresbysund.json#L103-L163](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-green/America--Scoresbysund.json#L103-L163) |
| 3 | 当日程时刻本身落在春令时缺失窗口内（例如周日 02:30 在春令时切换日不存在）时，明确规定并测试其确定性行为，且同周重复调用 `due()` 与 `runScheduled()` 去重一致、不会重复触发或漏触发。 | `PASS` | 规则文档与注释：[README.md#L1186-L1189](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/README.md#L1186-L1189)、[retrospective.ts#L58-L62](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L58-L62)；测试定义：[test_t223_retrospective_due.ts#L28-L32](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L28-L32)、[L47-L54](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L47-L54)、[L64-L74](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L64-L74)；绿态输出：[evidence/r3-green/America--New_York.json#L223-L246](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-green/America--New_York.json#L223-L246)、[L298-L332](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-green/America--New_York.json#L298-L332)、[evidence/r3-green/America--Nuuk.json#L113-L153](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-green/America--Nuuk.json#L113-L153) |
| 4 | 新增回归测试在修复前（或回退修复后）因 `07:30Z` vs `06:30Z` 失败，在修复后通过。 | `PASS` | 基线红态：[evidence/r3-baseline/America--New_York.json#L198-L205](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-baseline/America--New_York.json#L198-L205)、[controller/r3/base-red-New_York.json#L198-L205](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/base-red-New_York.json#L198-L205)；第二轮红态：[evidence/r3-round2-red/America--Nuuk.json#L105-L184](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-round2-red/America--Nuuk.json#L105-L184)、[controller/r3/round2-red-Nuuk.json#L105-L184](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/round2-red-Nuuk.json#L105-L184)；变异红态：[evidence/r3-mutants/summary.json#L2-L396](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-mutants/summary.json#L2-L396)、[controller/r3/mutant-slot-rollback-Nuuk.json#L131-L170](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/mutant-slot-rollback-Nuuk.json#L131-L170)；修复后绿态：[evidence/r3-green/summary.json#L1-L44](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-green/summary.json#L1-L44)、[controller/r3/runs.log#L1-L6](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/runs.log#L1-L6) |
| 5 | 现有复盘端到端测试（`workbench/tests/test_t136_retrospective_e2e.py`、`workbench/tests/test_t137_reflect_e2e.py`）在当前日期（2026-11-01，美国秋令时切换日）继续通过。 | `PASS` | Worker 输出：[evidence/r3-t136-summary.json#L1-L244](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-t136-summary.json#L1-L244)、[evidence/r3-t137-summary.json#L1-L252](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/evidence/r3-t137-summary.json#L1-L252)；主控复跑：[controller/r3/t136-summary.json#L1-L244](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/t136-summary.json#L1-L244)、[controller/r3/t137-summary.json#L1-L252](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/t137-summary.json#L1-L252)、[controller/r3/runs.log#L30-L33](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/r3/runs.log#L30-L33) |
| 6 | 独立审查（设计完整性与行为验收）通过。 | `PASS` | 本独立审查报告（基于 [change.diff#L1-L160](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/change.diff#L1-L160)、[retrospective.ts#L55-L70](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L55-L70)、[test_t223_retrospective_due.ts#L1-L115](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L1-L115) 及 `evidence/`、`controller/r3/` 全量证据核对） |

PASSZ