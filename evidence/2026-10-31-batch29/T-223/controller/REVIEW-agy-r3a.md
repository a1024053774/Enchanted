# T-223 第三轮候选独立只读审查报告（代码、规则与测试）

---

## 一、逐项核对

### 1. 根因与改动

- **根因回顾**：
  - **基线 `76f969963`**（见 [change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/change.diff#L24-L27)）：`Retrospectives.due()` 先在查询当天的 `slot = new Date(now)` 上调用 `slot.setHours(schedule.hour, schedule.minute, 0, 0)`，再调用 `slot.setDate(...)` 回退到目标星期几（`slot > now` 时只做 `slot.setDate(slot.getDate() - 7)`）。若查询当天是春季夏令时跳过日且日程时刻落在被跳过的时段（如 `America/New_York` 在 `2026-03-08` 跳过 `02:00`～`02:59`，日程为 `02:30`），`setHours` 先把该不存在的时刻规范到一小时后（`03:30`），再回退到目标日期后仍保留这一小时偏差。
  - **第二轮候选回归**（见 [brief.md](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/brief.md#L80-L85)、[REVIEW-agy-r1-controller-check.md](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/REVIEW-agy-r1-controller-check.md#L13-L17)）：改成了先 `const slot = new Date(now)` 再 `slot.setDate(...)` 后 `slot.setHours(...)`。`setDate` 这一步仍带着查询时刻 `now` 的墙钟时分；当目标日期存在一直延到本地午夜的跳过段（如 `America/Nuuk`、`America/Scoresbysund` 在 `2026-03-28` 周六 `23:00` `-02` 直接跳到周日 `00:00` `-01`），且查询时刻 `now` 的墙钟时间落在 `23:00`～`23:59:59.999` 时，`setDate` 会把中间时刻规范到次日（周日 `03-29` `00:xx`），导致随后的 `setHours` 落在错误的一天。
- **`due()` 现在怎样确定目标日期与时刻**（[retrospective.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L55-L70)、[change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/change.diff#L28-L36)）：
  - 在 [`Retrospectives.due()`](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L55-L70) 的第 [63-65](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L63-L65) 行：
    ```ts
    const year = now.getFullYear(), month = now.getMonth();
    const day = now.getDate() - ((now.getDay() - schedule.weekday + 7) % 7);
    let slot = new Date(year, month, day, schedule.hour, schedule.minute, 0, 0);
    ```
    只从 `now` 提取本地日历年（`getFullYear()`）、月（`getMonth()`）、日（`getDate()`）与星期几（`getDay()`），计算出本周目标日历日数字 `day`，然后直接通过 `new Date(year, month, day, schedule.hour, schedule.minute, 0, 0)` 一步构造目标日期上的日程时刻。
- **本周未到点回退一周的分支怎样处理**（[retrospective.ts:66](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L66)）：
  - 第 [66](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L66) 行：
    ```ts
    if (slot > now) slot = new Date(year, month, day - 7, schedule.hour, schedule.minute, 0, 0);
    ```
    当本周日程尚未到点（`slot > now`）时，不修改原 `slot` 对象，而是以 `day - 7` 和原日程的 `schedule.hour, schedule.minute, 0, 0` 重新调用 `new Date(...)` 构造上一周的目标时刻，因此本周目标日若发生过跳过顺延，顺延后的墙钟时刻绝不会残留到上一周。
- **是否还有任何一步依赖查询时刻的墙钟时间**：
  - **没有。** 在构造候选槽位 `slot` 的全过程中，未调用 `new Date(now)`，也未读取 `now` 的小时、分钟、秒、毫秒。`now` 的精确时间戳仅在第 [66](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L66) 行 `if (slot > now)` 中与已构造完成的 `slot` 比较先后，不参与任何中间日期或墙钟时刻的合成。
- **改动范围核对**：
  - 核对 [change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/change.diff#L1-L160)，全部改动仅在以下 3 个文件：
    1. [candidate/workbench/README.md](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/README.md#L1186-L1189)（对应 [change.diff:1-15](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/change.diff#L1-L15)）
    2. [candidate/workbench/src/retrospective.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L58-L66)（对应 [change.diff:16-40](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/change.diff#L16-L40)）
    3. [candidate/workbench/tests/test_t223_retrospective_due.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L1-L115)（对应 [change.diff:41-160](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/change.diff#L41-L160)）
  - 去重逻辑（[retrospective.ts:68](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L68) `const ran = this.runs(project).some(run => run.scheduled_for === slot.toISOString());`）、存储格式与表结构（[retrospective.ts:29-39](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L29-L39)、[retrospective.ts:50](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L50)、[retrospective.ts:90](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L90)）以及唯一调用方 [daemon.ts:109](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/daemon.ts#L109) 均未改动。

---

### 2. 规则与边界

- **注释与 README 是否与代码行为一致**：
  - 代码注释（[retrospective.ts:58-62](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L58-L62)）：
    > `// MakeDay resolves the numeric calendar date before UTC(t) applies the scheduled wall time.`
    > `// Never carry the query's wall time into the target date: a gap ending at midnight could`
    > `// normalize that intermediate time onto the next day. Reconstruct last week's date too.`
    > `// ECMAScript UTC(t) uses the pre-transition offset for gaps (advance by the gap) and the`
    > `// earlier instant for overlaps.`
  - 文档（[README.md:1186-1189](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/README.md#L1186-L1189)）：
    > `定期复盘按后台的本地日历日期和墙钟时刻计算，取当前时刻之前或恰好到点的最近一次日程；本周未到点时取上周。`
    > `目标时刻直接由目标日历日期与日程设置的时分构造，不携带查询时刻的时分；回退一周时，也重新按上周的日历日期与所设时分构造。`
    > `夏令时规则遵循 [ECMAScript 的 UTC(t)](https://tc39.es/ecma262/multipage/numbers-and-dates.html#sec-utc-t)：目标日期上的墙钟时刻不存在时，按转换前的偏移解释，向前顺延跳过的时长；时刻重复时，取较早的一次。`
    > `例如 America/New_York 的 2026-03-08 02:30 顺延为 03:30 EDT（07:30Z），2026-11-01 01:30 取第一次 EDT（05:30Z）。同一项目已记录的 scheduled_for 按完整 ISO 时刻去重。`
  - **一致性判断**：完全一致，且 `README.md` 只写现行规则，未混入历史缺陷说明。
- **依据 ECMAScript 的 `MakeDay`、`MakeDate`、`UTC(t)` 逐项推理**：
  在 ECMAScript 中，`new Date(year, month, date, hours, minutes, 0, 0)`（当 `year` 为四位年份如 `2026` 时）依次执行 `finalDate = MakeDate(MakeDay(year, month, date), MakeTime(hours, minutes, 0, 0))` 与 `TimeClip(UTC(finalDate))`：
  1. **日期数字小于 1 或超过当月天数（跨月、跨年回退）**：
     - `MakeDay(year, month, date)` 先按 `ym = year + floor(month / 12)`、`mn = month modulo 12` 定位公历 `(ym, mn, 1)`（当月 1 日）对应的纪元日整数 `Day(t)`，再直接返回整数 `Day(t) + date - 1`；这一步是纯公历整数日运算（每天恒为 `86,400,000 ms`），完全不经过本地时区偏移或夏令时转换。
     - **当 `date < 1` 时**（在 `due()` 中，`day = now.getDate() - back` 或 `day - 7` 可取 `0` 到 `-12`）：`Day(t) + date - 1` 从当月 1 日向前扣减整数个公历日，自动按上月实际天数跨月回退（例如推算：`2026-04-01` 周三找周一，`month = 3`，`day = 1 - 2 = -1`，`MakeDay(2026, 3, -1)` 得到 `(2026, 3, 1)` 减 2 天即 `2026-03-30`）；若 `month = 0`（1 月）且 `date < 1`，则从 `(year, 0, 1)` 向前扣减整数天，自动跨年落到 `year - 1` 年 12 月对应日（例如推算：`2027-01-01` 周五找周一，`month = 0`，`day = 1 - 4 = -3`，`MakeDay(2027, 0, -3)` 得到 `(2027, 0, 1)` 减 4 天即 `2026-12-28`）。
     - **当 `date > 当月天数` 时**（`due()` 只做减法不会传入大于当月天数的 `date`；若按 `MakeDay` 规则传入）：`Day(t) + date - 1` 同样按当月实际公历天数自动向后溢入下月（或次年 1 月）的对应日历日。
     - 选定精确的目标日历日后，`MakeDate` 才把该日与 `MakeTime(schedule.hour, schedule.minute, 0, 0)` 合成为本地时间值 `t` 并交给 `UTC(t)`，跨月、跨年不会受中间日期夏令时转换的干扰。
  2. **目标日期上日程时刻不存在（跳过 1 小时，以及 `Australia/Lord_Howe` 的半小时跳过）**：
     - `MakeDate` 合成目标日历日期与日程墙钟时刻 `t` 后，若该墙钟时刻落在目标日期的向前跳过段内（对应 0 个 UTC 时刻），ECMAScript `UTC(t)` 按转换前的时区偏移 $\text{offset}_{\text{before}}$ 解释 `t`，即返回 $\text{UTC}(t) = t - \text{offset}_{\text{before}}$；在转换后的新偏移 $\text{offset}_{\text{after}} = \text{offset}_{\text{before}} + \Delta_{\text{gap}}$ 下，其本地墙钟时间恰好为 $t + \Delta_{\text{gap}}$（向前顺延跳过的时长 $\Delta_{\text{gap}}$）。
     - **跳过 1 小时**（如 `America/New_York` 在 `2026-03-08` 周日 `02:00 EST (-05:00) -> 03:00 EDT (-04:00)`）：目标日期 `2026-03-08` 上的 `02:30` 按转换前偏移 `-05:00` 解释，得到 `2026-03-08T07:30:00.000Z`（即 `03:30 EDT`，顺延 1 小时）。若查询时刻 `now` 早于 `07:30Z`（如 `03:00 EDT = 07:00Z`），`slot > now` 触发回退一周分支，重新用 `day - 7` 构造 `2026-03-01 02:30 EST`，得到 `2026-03-01T07:30:00.000Z`。
     - **`Australia/Lord_Howe` 的半小时跳过**（推算：`Australia/Lord_Howe` 标准时为 `UTC+10:30`，夏令时为 `UTC+11:00`，春季在 `2026-10-04` 周日 `02:00 (+10:30) -> 02:30 (+11:00)` 跳过 30 分钟）：若日程设在周日 `02:15`（落在被跳过的 30 分钟内），`MakeDate` 合成 `2026-10-04T02:15:00`，`UTC(t)` 按转换前偏移 `+10:30` 解释，减去 10 小时 30 分钟得到推算值 `2026-10-03T15:45:00.000Z`，对应转换后 `+11:00` 下的本地时刻 `2026-10-04 02:45 (+11:00)`，即顺延跳过的半小时（30 分钟）。这与注释“advance by the gap”和 README“向前顺延跳过的时长”完全一致。
  3. **跳过段延到本地午夜（`America/Nuuk`）**：
     - `America/Nuuk`（及 `America/Scoresbysund`）在 `2026-03-28` 周六 `23:00 (-02:00)` 直接跳到 `2026-03-29` 周日 `00:00 (-01:00)`。
     - **日程时刻不在跳过段（如周六 `10:00`），而在周日或周四的 `23:30 (-01:00)` 查询**：`MakeDay` 先由 `day = now.getDate() - back` 算出 `2026-03-28`，`MakeTime` 直接取 `10:00`，`UTC(t)` 在 `2026-03-28 10:00 (-02:00)` 上算出 `2026-03-28T12:00:00.000Z`。因全程不经过 `2026-03-28 23:30` 这个中间时刻，不会被推到周日 `2026-03-29`。
     - **日程时刻本身就在跨午夜跳过段内（如周六 `23:30`）**：`MakeDate` 合成 `2026-03-28T23:30:00`，`UTC(t)` 按转换前偏移 `-02:00` 解释，算得 `2026-03-29T01:30:00.000Z`（对应 `-01:00` 下的周日 `2026-03-29 00:30:00-01:00`）。若在周日 `00:15-01:00`（`01:15Z`，早于顺延后的 `01:30Z`）查询，`slot > now` 成立，回退一周重新构造 `new Date(2026, 2, 21, 23, 30, 0, 0)`，得到上一周六 `2026-03-21 23:30 (-02:00)` = `2026-03-22T01:30:00.000Z`；在周日 `00:30-01:00`（`01:30Z`）及之后查询，返回 `2026-03-29T01:30:00.000Z`。
  4. **秋季重复时刻**：
     - 当目标日期上的墙钟时刻 `t` 因秋季回拨重复出现两次（如 `America/New_York` 在 `2026-11-01` 周日 `02:00 EDT (-04:00) -> 01:00 EST (-05:00)`，日程为周日 `01:30`）时，ECMAScript `UTC(t)` 按转换前偏移 `-04:00` 取较早的一次候选时刻，恒得到第一次出现的 `2026-11-01T05:30:00.000Z`（`01:30 EDT`）。
     - 在第一次 `01:30 EDT`（`05:30Z`）之前查询时，`slot > now` 触发回退一周到 `2026-10-25 01:30 EDT`（`2026-10-25T05:30:00.000Z`）；在第一次 `01:30 EDT` 及之后（含第二次 `01:30 EST = 06:30Z`）查询时，`slot` 恒为 `2026-11-01T05:30:00.000Z`，去重 key 稳定唯一。
- **是否有遗漏边界、是否会阻塞本票**：
  - 无遗漏边界，无阻塞本票的问题。

---

### 3. 测试 [`test_t223_retrospective_due.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L1-L115) 核对

#### (a) `America/Nuuk` 与 `America/Scoresbysund` 组每个期望值的日历手算推算

在 [test_t223_retrospective_due.ts:78-82](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L78-L82) 中，`'America/Nuuk'` 与 `'America/Scoresbysund'` 两组共用 `midnightGapCases`（[L61-L77](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L61-L77)），组默认参数为：`weekday: 6`（周六）、`hour: 10`、`minute: 0`、`effective: '2026-03-01T00:00:00-02:00'`（推算：即 `2026-03-01T02:00:00.000Z`）。这两个时区冬季为 `UTC-02:00`（`-02`），夏季为 `UTC-01:00`（`-01`），2026 年在 `2026-03-28`（周六）`23:00 (-02)` 直接跳到 `2026-03-29`（周日）`00:00 (-01)`，2027 年在 `2027-03-27`（周六）`23:00 (-02)` 直接跳到 `2027-03-28`（周日）`00:00 (-01)`。

12 个用例的独立手算推算如下：

| 序号 | 行号 | 用例名 (`name`) | 输入条件 (`now` / 覆盖参数) | 日历手算推算 | 推算结果 vs 文件原文 `expected` |
| --- | --- | --- | --- | --- | --- |
| 1 | [L62](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L62) | `F12/sunday-late-query` | `now: '2026-03-29T23:30:00-01:00'`，默认周六 `10:00` | 推算：`2026-03-29` 是周日，此前最近周六为 `2026-03-28`；周六 `10:00` 仍在转换（当晚 `23:00`）之前，偏移为 `-02:00`，`10:00 + 02:00 = 12:00Z`，即 `2026-03-28T12:00:00.000Z`，早于 `now`（`2026-03-30T00:30:00.000Z`） | `'2026-03-28T12:00:00.000Z'`（一致） |
| 2 | [L63](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L63) | `F12/thursday-late-query` | `now: '2026-04-02T23:30:00-01:00'`，默认周六 `10:00` | 推算：`2026-03-28` 为周六，3 月有 31 天，故 `2026-04-02` 为周四；跨月末回退 5 天仍为周六 `2026-03-28`，当天 `10:00 (-02:00)` = `2026-03-28T12:00:00.000Z` | `'2026-03-28T12:00:00.000Z'`（一致） |
| 3 | [L64-L65](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L64-L65) | `F12/already-ran-Saturday` | `now: '2026-03-29T23:30:00-01:00'`，已存 `demo` 的 `'2026-03-28T12:00:00.000Z'` | 推算：算得槽位 `2026-03-28T12:00:00.000Z` 与 `demo` 已存 `scheduled_for` 精确相等，去重返回 `null` | `null`（一致） |
| 4 | [L66](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L66) | `F12/Saturday-query-control` | `now: '2026-03-28T10:30:00-02:00'`，默认周六 `10:00` | 推算：周六当天 `10:30 (-02:00)` 查询，已过当天 `10:00 (-02:00)`，返回当天 `2026-03-28T12:00:00.000Z` | `'2026-03-28T12:00:00.000Z'`（一致） |
| 5 | [L67](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L67) | `F12/gap-target-after-normalized-slot` | `hour: 23, minute: 30`，`now: '2026-03-29T12:00:00-01:00'` | 推算：周日 `03-29 12:00 (-01:00)`（`13:00Z`）查询周六 `23:30` 日程；目标日 `2026-03-28` 的 `23:30` 落在跳过段内，按转换前 `-02:00` 解释：`2026-03-28 23:30 + 02:00 = 2026-03-29T01:30:00.000Z`（即周日 `00:30-01:00`），早于 `now`（`13:00Z`） | `'2026-03-29T01:30:00.000Z'`（一致） |
| 6 | [L68](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L68) | `F12/before-normalized-slot` | `hour: 23, minute: 30`，`now: '2026-03-29T00:15:00-01:00'` | 推算：`now` 为 `2026-03-29T01:15:00.000Z`，早于 `2026-03-28 23:30` 顺延后的 `2026-03-29T01:30:00.000Z`（`slot > now`）；回退一周到上一周六 `2026-03-21 23:30 (-02:00)`，加 2 小时得 `2026-03-22T01:30:00.000Z` | `'2026-03-22T01:30:00.000Z'`（一致） |
| 7 | [L69](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L69) | `F12/exact-normalized-slot` | `hour: 23, minute: 30`，`now: '2026-03-29T00:30:00-01:00'` | 推算：`now` 为 `2026-03-29T01:30:00.000Z`，恰好等于 `2026-03-28 23:30` 顺延后的 `2026-03-29T01:30:00.000Z`，到点触发 | `'2026-03-29T01:30:00.000Z'`（一致） |
| 8 | [L70](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L70) | `F12/next-week-before-slot` | `hour: 23, minute: 30`，`now: '2026-04-04T23:29:59.999-01:00'` | 推算：下一周周六 `2026-04-04` 的 `23:30 (-01:00)` 为 `2026-04-05T00:30:00.000Z`；`now` 早 1ms，未到点，回退一周到 `2026-03-28 23:30`，顺延后为 `2026-03-29T01:30:00.000Z` | `'2026-03-29T01:30:00.000Z'`（一致） |
| 9 | [L71](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L71) | `F12/next-week-exact-slot` | `hour: 23, minute: 30`，`now: '2026-04-04T23:30:00-01:00'` | 推算：下一周周六 `2026-04-04 23:30 (-01:00)` 恰好到点，加 1 小时得 `2026-04-05T00:30:00.000Z` | `'2026-04-05T00:30:00.000Z'`（一致） |
| 10 | [L72-L73](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L72-L73) | `F12/gap-target-already-ran` | `hour: 23, minute: 30`，`now: '2026-03-29T12:00:00-01:00'`，已存 `demo` 的 `'2026-03-29T01:30:00.000Z'` | 推算：算得槽位 `2026-03-29T01:30:00.000Z` 命中已存记录，去重返回 `null` | `null`（一致） |
| 11 | [L74](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L74) | `F12/2027-sunday-late-query` | `now: '2027-03-28T23:30:00-01:00'`，默认周六 `10:00` | 推算：`2027-03-28` 为周日，此前最近周六为跳过日 `2027-03-27`；当天 `10:00` 偏移为 `-02:00`，加 2 小时得 `2027-03-27T12:00:00.000Z` | `'2027-03-27T12:00:00.000Z'`（一致） |
| 12 | [L76](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L76) | `F12/2027-before-normalized-slot` | `hour: 23, minute: 30`，`now: '2027-03-28T00:15:00-01:00'` | 推算：`2027-03-27 23:30` 顺延后为 `2027-03-28T01:30:00.000Z`（周日 `00:30-01:00`）；在周日 `00:15-01:00`（`01:15Z`）查询尚未到点，回退一周到 `2027-03-20 23:30 (-02:00)`，加 2 小时得 `2027-03-21T01:30:00.000Z` | `'2027-03-21T01:30:00.000Z'`（一致） |

此外，`newYorkCases`（[test_t223_retrospective_due.ts:19-55](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L19-L55)）完整保留了原有的 26 个 `America/New_York` 用例（`F1`～`F11`），其手算期望值已在第一次审查（见 [REVIEW-agy-r1.md:54-87](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/REVIEW-agy-r1.md#L54-L87)）逐条核对无误。

#### (b) 是否经真实 `Retrospectives.due()` 运行
- **是。** [test_t223_retrospective_due.ts:15](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L15) 从 `join(product, 'workbench/src/retrospective.ts')` 动态导入真实的 `Retrospectives` 类，第 [90-92](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L90-L92) 行实例化 `new Retrospectives(db, '/private/tmp/t223-unused-no-files')` 并调用 `retrospectives.saveSchedule(...)`，第 [102](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L102) 行直接调用 `retrospectives.due('demo', now)`。

#### (c) 每组是否在显式 TZ 下运行，TZ 不对是否拒绝
- **是。** [test_t223_retrospective_due.ts:10-12](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L10-L12) 在加载被测模块前强制检查：
  ```ts
  const [productArg, output, zone] = process.argv.slice(2);
  assert(productArg && output && zone, 'usage: node test_t223_retrospective_due.ts PRODUCT OUTPUT.json ZONE');
  assert.equal(process.env.TZ, zone, 'the requested case group must match explicit TZ');
  ```
  并在第 [83](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L83) 行检查 `assert(Object.hasOwn(groups, zone), \`unsupported case group: ${zone}\`);`。若未显式设置 `process.env.TZ`、`process.env.TZ` 与命令行参数 `zone` 不一致，或 `zone` 不在 `groups` 的三个具名时区键内，脚本立即抛错退出。

#### (d) 断言会不会被放宽、跳过或吞掉
- **不会。** [test_t223_retrospective_due.ts:4](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L4) 使用 `node:assert/strict`；循环（[L87-L109](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L87-L109)）无条件遍历 `cases`，第 [103-104](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L103-L104) 行严格断言 `assert.equal(actual, c.expected, c.name)` 与 `assert.equal(now.toISOString(), originalNow, ...)`；任何断言失败或异常在 `catch`（[L106-L108](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L106-L108)）中记为 `pass: false`，并在第 [110-115](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L110-L115) 行由 `const pass = results.every(row => row.pass)` 将 `report.status` 置为 `'INCOMPLETE'`、`process.exitCode` 置为 `1`。

---

### 4. 第一次审查的意见核对

- **主控将非阻塞意见改判为阻塞的依据是否成立**：
  - **完全成立。** 从 [REVIEW-agy-r1-controller-check.md](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/REVIEW-agy-r1-controller-check.md#L11-L20)、[scan_midnight_gaps.mjs](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/scan_midnight_gaps.mjs#L1-L24) 和 [nuuk-probe.ts](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/nuuk-probe.ts#L1-L24) 推理：
    1. [scan_midnight_gaps.mjs:10-23](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/scan_midnight_gaps.mjs#L10-L23) 扫描 `Intl.supportedValuesOf('timeZone')` 在 2026–2027 年的所有向前跳过转换，比较转换前后的本地日序号 `Math.floor(after / DAY) > Math.floor(before / DAY)`（[L19](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/scan_midnight_gaps.mjs#L19)）。在现行时区中，`America/Nuuk` 和 `America/Scoresbysund` 确实在 `2026-03-28` 与 `2027-03-27` 周六 `23:00 (-02)` 直接跳到周日 `00:00 (-01)`，推翻了第一次审查（[REVIEW-agy-r1.md:48](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/REVIEW-agy-r1.md#L48)）“现行时区不在 `23:00 -> 00:00` 跨日跳过”的前提。
    2. [nuuk-probe.ts:8-20](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/nuuk-probe.ts#L8-L20) 在 `TZ=America/Nuuk` 下设置周六 `10:00` 日程，在 `2026-03-29T23:30:00-01:00` 或 `2026-04-02T23:30:00-01:00` 调用 `r.due('demo', new Date(c.now))`：
       - **推算第二轮候选行为**：`slot = new Date(now)` 带着 `23:30` 的墙钟时间执行 `slot.setDate(28)`，因 `2026-03-28 23:30` 在 `America/Nuuk` 下不存在，`UTC(t)` 按 `-02:00` 将其规范为 `2026-03-29T01:30:00.000Z`（即本地周日 `2026-03-29 00:30-01:00`）；紧接着执行 `slot.setHours(10, 0, 0, 0)` 时落在了周日 `2026-03-29 10:00 (-01:00)` = `'2026-03-29T11:00:00.000Z'`，而非正确的周六 `'2026-03-28T12:00:00.000Z'`。
       - **推算基线 `76f969963` 行为**：先在查询日（`03-29` 或 `04-02`）`setHours(10, 0, 0, 0)`，再 `setDate` 回退到 `2026-03-28`，因 `10:00` 在查询日和目标日均正常存在，基线返回正确值 `'2026-03-28T12:00:00.000Z'`。因此这是第二轮候选新引入的回归。
    3. **去重后果**：[retrospective.ts:68](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L68) 按 `run.scheduled_for === slot.toISOString()` 精确比对。即便周六 `10:00` 已按 `'2026-03-28T12:00:00.000Z'` 触发并记录，当周随后几天晚上 `23:00`～`23:59` 里的 `retrospectiveTimer` 每分钟轮询（[daemon.ts:118-120](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/daemon.ts#L118-L120)）仍会算出新 key `'2026-03-29T11:00:00.000Z'`，绕过已存的 `'2026-03-28T12:00:00.000Z'` 导致同一周重复启动一次复盘。
    4. 此外，第一次审查建议的“先 `setHours(12, 0, 0, 0)` 锚定正午”（[REVIEW-agy-r1.md:157](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/REVIEW-agy-r1.md#L157)）仍经过一个多余的中间本地时刻，不如直接按数字日历构造干净（[REVIEW-agy-r1-controller-check.md:19](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/controller/REVIEW-agy-r1-controller-check.md#L19)）。
- **第三轮代码是否解决了它**：
  - **已完全解决。** 第三轮代码（[retrospective.ts:63-66](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L63-L66)）直接用 `new Date(year, month, day, schedule.hour, schedule.minute, 0, 0)`（及回退一周时的 `day - 7`）一步构造目标时刻，彻底消除了携带查询时刻墙钟时间的中间 `Date`，并在 [test_t223_retrospective_due.ts:61-82](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L61-L82) 中用 `America/Nuuk` 与 `America/Scoresbysund` 两组共 24 次运行（12 个 `F12` 用例 × 2 个时区）锁死了该行为。

---

### 5. 设计核对

- 核对 [retrospective.ts:55-70](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L55-L70) 与 [change.diff:1-160](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/change.diff#L1-L160)：改动只在根因处改为按日历数字与日程时分直接构造 `Date`，**没有任何**为兼容或“保险”加的 fallback、重试、双写、平行 API 或吞异常。

---

### 6. 边界核对

- 核对 [test_t223_retrospective_due.ts:1-115](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L1-L115)：
  - 第 [12-13](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L12-L13) 行断言 `process.env.TZ === zone` 与 `process.env.TMPDIR === '/private/tmp'`；
  - 第 [88](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L88) 行使用内存 SQLite `new DatabaseSync(':memory:')` 并在第 [108](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L108) 行 `finally { db.close(); }` 关闭；
  - 第 [93-100](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L93-L100) 行直接向内存表 `retrospective_runs` 插入预设运行记录以验证 `due()` 去重，不调用会写磁盘文件的 `prepare()`；
  - 全程只用内存 SQLite 与本地直接方法调用，不碰用户数据目录（`~/.claude`、`~/.codex`、`~/.gemini`、`~/.config/herdr-core`、`~/.local/state/herdr-core`）、不连接也不启动 Herdr 或 hc、不调用真实模型。

---

## 二、审查意见列表

本次代码、规则与测试审查**无阻塞意见，也无非阻塞意见**（0 条意见）。

---

## 三、[ticket.md](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/ticket.md#L35-L39) 第 35 行验收及“另核对”各项判定（代码与测试角度）

> 注：本次审查范围仅限代码、规则与测试，**运行结果见证据审查**。

| [ticket.md](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/ticket.md#L35-L39) 第 35–39 行验收细项 | 代码与测试角度状态 | 依据（文件与行号） |
| --- | --- | --- |
| [ticket.md:35](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/ticket.md#L35)：`修后同一条件得到 2026-03-02T07:30:00.000Z` | **PASS**（运行结果见证据审查） | [retrospective.ts:63-66](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L63-L66) 先由 `now` 的年月日与星期差算出 `2026-03-02`（`day = 8 - 6 = 2`），再以 `new Date(2026, 2, 2, 2, 30, 0, 0)` 构造 `02:30 EST` = `'2026-03-02T07:30:00.000Z'`；测试用例 `F1/spring-query-for-earlier-Monday`（[test_t223_retrospective_due.ts:20](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L20)）断言该精确期望值；跨午夜跳过时区同类条件由 `F12`（[test_t223_retrospective_due.ts:62-66, 74](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L62-L66)）覆盖。运行结果见证据审查。 |
| [ticket.md:36](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/ticket.md#L36)：`目标日期本身就是跳过日、日程时刻不存在时的取值（例如 America/New_York 的日程设在周日 02:30，查询在 2026-03-08 之后），规则写进代码注释和 README` | **PASS**（运行结果见证据审查） | 规则（按转换前偏移解释、向前顺延跳过的时长）已写进代码注释 [retrospective.ts:58-62](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L58-L62) 与文档 [README.md:1186-1189](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/README.md#L1186-L1189)；测试在 `America/New_York` 下由 `F2`、`F3`、`F4`、`F11/gap-target-does-not-rerun-next-day`（[test_t223_retrospective_due.ts:22-27, 53-54](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L22-L27)）覆盖，在 `America/Nuuk` 与 `America/Scoresbysund` 跨午夜跳过下由 `F12`（[test_t223_retrospective_due.ts:67-73, 76](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L67-L73)）覆盖。运行结果见证据审查。 |
| [ticket.md:37](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/ticket.md#L37)：`秋季回拨日的重复时刻（如 01:30）取哪一次` | **PASS**（运行结果见证据审查） | 规则（取较早的一次）已写进 [retrospective.ts:61-62](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L61-L62) 与 [README.md:1188-1189](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/README.md#L1188-L1189)；测试由 `F5` 四个用例及 `F11/second-overlap-does-not-rerun`（[test_t223_retrospective_due.ts:29-32, 51-52](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L29-L32)）覆盖。运行结果见证据审查。 |
| [ticket.md:38](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/ticket.md#L38)：`普通日、月末、年末不受影响` | **PASS**（运行结果见证据审查） | `MakeDay` 自动处理当月及跨月、跨年日历日期计算（[retrospective.ts:63-66](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/src/retrospective.ts#L63-L66)）；测试由 `F6/ordinary-summer-day`、`F6/ordinary-winter-day`、`F7/month-boundary`、`F8/year-boundary`、`F9`、`F10` 以及 `F12/thursday-late-query`（4 月初跨回 3 月末）、`F12/next-week-before-slot`（[test_t223_retrospective_due.ts:33-42, 63, 70-71](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L33-L42)）覆盖。运行结果见证据审查。 |
| [ticket.md:39](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/ticket.md#L39)：`期望值按日历手工推算，不取实现的输出` | **PASS**（运行结果见证据审查） | `newYorkCases`（26 项，[test_t223_retrospective_due.ts:19-55](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L19-L55)）与 `midnightGapCases`（12 项，[test_t223_retrospective_due.ts:61-77](file:///Users/luckye/Documents/Code/a2a-review/T-223-r2/candidate/workbench/tests/test_t223_retrospective_due.ts#L61-L77)）的所有 `expected` 均为写死在测试源码中的常量，经独立日历手算逐一核对全部相符，未调用被测实现计算期望值。运行结果见证据审查。 |

PASS