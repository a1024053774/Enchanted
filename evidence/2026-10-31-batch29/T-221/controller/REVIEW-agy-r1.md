# T-221 agy 独立审查原文

- 来源：agy，模型 Gemini 4 Argon (High)，`--mode auto`，审查目录 `/Users/luckye/Documents/Code/a2a-review/T-221-r1`（只读）。
- 取自 agy 会话库 `fe70beb0-ea87-4a3b-a2bb-7745f6699fc2.db` 第 101 步；终端画面只显示了尾部。账号邮箱只出现在终端抬头，不在本文。
- 文中链接指向冻结的审查副本。主控逐条核对见 `REVIEW-agy-r1-controller-check.md`。

---

# T-221 独立只读审查报告

---

## 一、审查意见（阻塞 / 非阻塞）

本次审查未发现**阻塞**意见，也未发现需要修改候选代码的**非阻塞**问题：

- **阻塞意见**：无（0 条）。
- **非阻塞意见**：无（0 条）。

---

## 二、逐项核对详情

### 1. 根因与改动

1. **[`codexScanDays`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/codexScanDays.ts#L2-L12) 的本地日历边界与步长**：
   - 在 [codexScanDays.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/codexScanDays.ts#L1-L12)（对应 [change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/change.diff#L164-L175)）中：
     - 第 3–5 行：`const start = new Date(since), tomorrow = new Date(now);`、`start.setHours(0, 0, 0, 0);`、`start.setDate(start.getDate() + startDayOffset);`，将起点归零到本地日历午夜 `00:00:00.000` 并按本地日历偏移 `startDayOffset` 天；
     - 第 6–7 行：`tomorrow.setHours(0, 0, 0, 0);`、`tomorrow.setDate(tomorrow.getDate() + 1);`，将终点设为 `now` 所在本地日历日期的次日（“本地明天”）午夜 `00:00:00.000`；
     - 第 9–11 行：`for (const day = start; day.getTime() <= tomorrow.getTime(); day.setDate(day.getDate() + 1))` 每次 `yield new Date(day)`，使用 `<=` 比较本地午夜时间戳，并以 `day.setDate(day.getDate() + 1)` 按本地日历逐日递增，起点与终点（本地“明天”）两端均包含。
   - **四类日历边界推算核对**（`TZ=America/New_York`，2026 年夏令时 3 月 8 日 02:00 开始、11 月 1 日 02:00 结束）：
     - **秋季回拨前夜**：`2026-10-31T22:34:14-04:00` 到 `2026-10-31T22:35:14-04:00`（[test_t221_codex_scan_days.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t221_codex_scan_days.ts#L23-L25)），原写法终点 `Date.now() + 86_400_000` 为 `2026-11-01T21:35:14-05:00`，而 `day` 加一天后为 `2026-11-01T22:34:14-05:00`（相距 25 小时 = `90_000_000` ms），导致漏掉 `2026/11/01`（见 [context/T-219-evidence/dst-america-02.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/context/T-219-evidence/dst-america-02.log#L1-L12)）。新写法比较本地午夜 `2026-10-31T00:00:00-04:00` 与 `2026-11-01T00:00:00-04:00`，完整产出 `["2026/10/31", "2026/11/01"]`（`startDayOffset = -1` 时产出 `["2026/10/30", "2026/10/31", "2026/11/01"]`）。
     - **春季跳过**：`2026-03-06T23:55:00-05:00` 到 `2026-03-08T00:05:00-05:00`（[test_t221_codex_scan_days.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t221_codex_scan_days.ts#L26-L28)），跨越 2026-03-08（23 小时日），`setDate(getDate() + 1)` 逐日保持本地 `00:00:00`，产出 `["2026/03/06", "2026/03/07", "2026/03/08", "2026/03/09"]`（`startDayOffset = -1` 含 `"2026/03/05"`）；另在 `2026-03-09T00:15:00-04:00`（[test_t221_codex_scan_days.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t221_codex_scan_days.ts#L38-L40)）下，旧写法 `new Date(since - 86_400_000)` 落在 `2026-03-07T23:15:00-05:00` 会多扫 `"2026/03/07"`，新写法先 `setHours(0, 0, 0, 0)` 再 `setDate(getDate() - 1)` 准确从 `"2026/03/08"` 开始。
     - **秋季回拨当日**：`2026-11-01T00:15:00-04:00` 到 `2026-11-01T22:35:00-05:00`（[test_t221_codex_scan_days.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t221_codex_scan_days.ts#L29-L31)）产出 `["2026/11/01", "2026/11/02"]`；且在 `2026-11-01T23:30:00-05:00`（[test_t221_codex_scan_days.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t221_codex_scan_days.ts#L41-L43)）下，旧写法 `new Date(since - 86_400_000)` 落在 `2026-11-01T00:30:00-04:00` 会漏掉前一天 `"2026/10/31"`，新写法 `startDayOffset = -1` 准确包含 `"2026/10/31"`。
     - **月末与年末**：4 月 30 日进位到 5 月 1 日（[test_t221_codex_scan_days.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t221_codex_scan_days.ts#L32-L34)：`["2026/04/29", "2026/04/30", "2026/05/01"]`）与 12 月 31 日进位到次年 1 月 1 日（[test_t221_codex_scan_days.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t221_codex_scan_days.ts#L35-L37)：`["2026/12/30", "2026/12/31", "2027/01/01"]`）均由 `Date.prototype.setDate` 正确进位。

2. **四处调用点核对**：
   - [`codexRootThreads`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/nativeLink.ts#L136-L162)：在 [nativeLink.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/nativeLink.ts#L6) 导入 [`codexScanDays`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/codexScanDays.ts#L2)，第 140 行改为 `for (const day of codexScanDays(since))`（[change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/change.diff#L33-L34)）。
   - [`Panes.scan`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/panes.ts#L1243-L1246)：在 [panes.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/panes.ts#L46) 导入 [`codexScanDays`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/codexScanDays.ts#L2)，第 1245 行改为 `for (const day of codexScanDays(since))`（[change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/change.diff#L54-L55)）。
   - [`TrajectoryArchive.codexRolloutIn`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/trajectoryArchive.ts#L80-L97)：在 [trajectoryArchive.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/trajectoryArchive.ts#L5) 导入 [`codexScanDays`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/codexScanDays.ts#L2)，第 83 行改为 `for (const day of codexScanDays(since, Date.now(), -1))`（[change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/change.diff#L75-L76)），起点保持为启动前一天（`startDayOffset = -1`）。
   - [`TrajectoryArchive.codexRollout`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/trajectoryArchive.ts#L100-L108)：第 101 行改为 `for (const day of codexScanDays(since, Date.now(), -1))`（[change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/change.diff#L84-L85)），起点同样保持为启动前一天（`startDayOffset = -1`）。

3. **代码库中是否残留“本地日历步长配固定 24 小时终点”**：
   - 核对 [evidence/final-scan.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/final-scan.log#L1-L11) 与 [evidence/r2-audit.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/r2-audit.log#L1-L403)，`workbench/src` 下已无任何 `86_400_000` 或 `setDate(getDate() + 1)` 配固定毫秒终点的写法。

---

### 2. 测试的区分度

1. **[test_t221_codex_scan_days.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t221_codex_scan_days.ts#L1-L118)**：
   - **红态是否在原逻辑上取得、被测对象是否为产品同一段计算**：
     - 先将原逻辑原封不动抽出为 [evidence/extracted-codexScanDays.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/extracted-codexScanDays.ts#L1-L6)（`const start = new Date(since + startDayOffset * 86_400_000), end = now + 86_400_000; for (const day = start; day.getTime() <= end; day.setDate(day.getDate() + 1))`）并由四处产品代码调用（[evidence/extraction.patch](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/extraction.patch#L1-L72)）。
     - 测试直接从产品目录加载 [`codexScanDays`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/codexScanDays.ts#L2)、[`nativeLink`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/nativeLink.ts#L19)、[`TrajectoryArchive`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/trajectoryArchive.ts#L14)、[`Panes`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/panes.ts#L1242)（[test_t221_codex_scan_days.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t221_codex_scan_days.ts#L13-L18)）。
     - 红态输出见 [evidence/red-extracted.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/red-extracted.log#L1-L399)：共 196 项检查，38 项失败。其中 `fall-T219-exact-launch/range/0` 实测 `["2026/10/31"]`、期望 `["2026/10/31", "2026/11/01"]`（第 68–78 行），四处真实消费者在 `2026/11/01` 全部失败（第 94–124 行）。
   - **期望值是否为手工写死的日历事实**：
     - [test_t221_codex_scan_days.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t221_codex_scan_days.ts#L19-L44) 的 8 组 `cases`（`fall-T219-evening`、`fall-T219-exact-launch`、`spring`、`fall-day-evening`、`month-end`、`year-end`、`spring-previous-local-day`、`fall-previous-local-day`）全部是硬编码的 `'YYYY/MM/DD'` 字符串数组，且逐组带有越界对照日 `before` 与 `after`（第 65 行 `for (const date of [c.before, ...c.archive, c.after])`）。经独立按日历推算核对，8 组的 `days`、`archive`、`before`、`after` 全部准确无误。
   - **变异测试（`evidence/mutant-*`）是否都失败在对应检查**：
     - 变异脚本见 [evidence/mutate.py](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/mutate.py#L1-L56)：
       1. `original-helper`（[evidence/mutant-original-helper.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/mutant-original-helper.log#L1-L400)）：回退 [`codexScanDays`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/codexScanDays.ts#L2) 为固定 `86_400_000`，38 项失败（覆盖 `range` 与四个消费者）。
       2. `miss-native`（[evidence/mutant-miss-native.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/mutant-miss-native.log#L1-L42)）：只回退 [`nativeLink.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/nativeLink.ts#L140) 一处循环，5 项失败，全部落在 `*/nativeLink/*`（第 6、13、20、27、34 行）。
       3. `miss-panes`（[evidence/mutant-miss-panes.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/mutant-miss-panes.log#L1-L42)）：只回退 [`panes.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/panes.ts#L1245) 一处循环，5 项失败，全部落在 `*/panes/*`（第 6、13、20、27、34 行）。
       4. `miss-archive-cwd`（[evidence/mutant-miss-archive-cwd.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/mutant-miss-archive-cwd.log#L1-L79)）：只回退 [`trajectoryArchive.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/trajectoryArchive.ts#L83) 的 `codexRolloutIn`，8 项失败，全部落在 `*/archive-retro-at-start/*`（第 6、15、23、32、41、50、59、69 行）。
       5. `miss-archive-id`（[evidence/mutant-miss-archive-id.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/mutant-miss-archive-id.log#L1-L79)）：只回退 [`trajectoryArchive.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/trajectoryArchive.ts#L101) 的 `codexRollout`，8 项失败，全部落在 `*/archive-controller/*`（第 6、15、23、32、41、50、59、69 行）。
       6. `drop-previous`（[evidence/mutant-drop-previous.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/mutant-drop-previous.log#L1-L151)）：把 [`trajectoryArchive.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/trajectoryArchive.ts#L83-L101) 的 `-1` 改为 `0`，16 项失败，全部是 8 组用例各自的“启动前一天”在 `archive-controller` 和 `archive-retro-at-start` 上返回 `[]`。

2. **[test_t221_calendar_clocks.py](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t221_calendar_clocks.py#L1-L39) 与 [local_calendar.py](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/local_calendar.py#L1-L10)**：
   - **六组期望值独立按日历推算核对**（`TZ=America/New_York`）：
     1. `spring-two-days`（第 14 行）：UTC `2026-03-07T03:34:00+00:00` 对应纽约标准时（EST，`-05:00`）`2026-03-06T22:34:00-05:00`；加 2 天并取 10:00 墙钟，跨过 2026-03-08 02:00 夏令时起点，进入 EDT（`-04:00`），应为 `2026-03-08T10:00:00-04:00`。与测试一致。
     2. `fall-two-days`（第 15 行）：UTC `2026-11-01T02:34:00+00:00` 对应纽约夏令时（EDT，`-04:00`）`2026-10-31T22:34:00-04:00`；加 2 天并取 10:00 墙钟，跨过 2026-11-01 02:00 回拨点，进入 EST（`-05:00`），应为 `2026-11-02T10:00:00-05:00`。与测试一致。
     3. `spring-week`（第 16 行）：UTC `2026-03-02T14:00:00+00:00` 对应纽约 EST `2026-03-02T09:00:00-05:00`（周一）；加 7 天并取 09:00 墙钟，跨过 2026-03-08 夏令时起点，应为 `2026-03-09T09:00:00-04:00`。与测试一致。
     4. `fall-week`（第 17 行）：UTC `2026-10-26T13:00:00+00:00` 对应纽约 EDT `2026-10-26T09:00:00-04:00`（周一）；加 7 天并取 09:00 墙钟，跨过 2026-11-01 回拨点，应为 `2026-11-02T09:00:00-05:00`。与测试一致。
     5. `month-end`（第 18 行）：UTC `2026-05-01T03:34:00+00:00` 对应纽约 EDT `2026-04-30T23:34:00-04:00`；加 2 天并取 10:00 墙钟，未跨夏令时切换，应为 `2026-05-02T10:00:00-04:00`。与测试一致。
     6. `year-end`（第 19 行）：UTC `2026-12-31T03:34:00+00:00` 对应纽约 EST `2026-12-30T22:34:00-05:00`；加 2 天并取 10:00 墙钟，未跨夏令时切换，应为 `2027-01-01T10:00:00-05:00`。与测试一致。
   - **主控的固定偏移变异（[controller/mutant-fixed-offset.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/controller/mutant-fixed-offset.log#L1-L66)）**：
     - 变异差异见 [controller/mutant-fixed-offset.diff](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/controller/mutant-fixed-offset.diff#L1-L8)（将 `return datetime.now(ZoneInfo(name))` 改为 `return datetime.now().astimezone()`）。
     - 运行结果见 [controller/mutant-fixed-offset.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/controller/mutant-fixed-offset.log#L1-L66)（以及 worker 的 [evidence/r2-mutant-fixed-offset.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/r2-mutant-fixed-offset.log#L1-L57)）：`FAILED (failures=4)`，恰好只在 `spring-two-days`（第 12 行）、`fall-two-days`（第 24 行）、`spring-week`（第 36 行）、`fall-week`（第 48 行）四个跨夏令时切换的 subTest 失败，而在不跨夏令时的 `month-end` 与 `year-end` 上通过。

3. **T-136、T-137 的测试时钟改动**：
   - [test_t136_retrospective_e2e.py](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t136_retrospective_e2e.py#L30)（[change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/change.diff#L97-L106)）：仅在第 30 行导入 [`local_now`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/local_calendar.py#L7)，并将第 289 行 `datetime.now().astimezone() + timedelta(days=2)` 改为 `local_now(fixture.env) + timedelta(days=2)`；第 299–307 行的 `schedule_fires_once_at_its_time` 与 `schedule_off_does_not_fire` 断言一字未改。
   - [test_t137_reflect_e2e.py](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t137_reflect_e2e.py#L37)（[change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/change.diff#L118-L155)）：导入 [`local_now`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/local_calendar.py#L7)，将第 179 行和第 265 行的 `datetime.now().astimezone()` 替换为 `local_now(fixture.env)`，并将第 163 行 `when.astimezone().isoformat()` 改为 `when.isoformat()`（因 `when` 已带具名时区 `ZoneInfo`）；所有 `check(...)` 断言完全未变、未放宽。

---

### 3. 第二轮普查清单核对

对照 [evidence/REPORT.md](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/REPORT.md#L140-L169)、[evidence/r2-audit.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/r2-audit.log#L1-L403)、[evidence/r2-audit-wide.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/r2-audit-wide.log#L1-L2065)、[evidence/r2-audit-decisions.md](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/r2-audit-decisions.md#L1-L60) 及直接阅读 `candidate/` 源码，逐项核查如下：

1. **已在本票修复的条目（6 处）**：
   - [nativeLink.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/nativeLink.ts#L140)、[panes.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/panes.ts#L1245)、[trajectoryArchive.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/trajectoryArchive.ts#L83) 与 [trajectoryArchive.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/trajectoryArchive.ts#L101)：四处产品代码均改用 [`codexScanDays`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/codexScanDays.ts#L2)，判定成立。
   - [test_t136_retrospective_e2e.py](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t136_retrospective_e2e.py#L289) 与 [test_t137_reflect_e2e.py](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t137_reflect_e2e.py#L157-L180)（及第 265 行）：两处 E2E 测试跨日时钟均改用 [`local_now`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/local_calendar.py#L7)，判定成立（T-137 修前红态证据见 [evidence/r2-red-t137.json](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/r2-red-t137.json#L204-L209)，修后绿态见 [evidence/r2-green-t137.json](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/r2-green-t137.json#L1-L21) 与 [controller/t137.json](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/controller/t137.json#L1-L21)）。

2. **产品代码另行登记、不在本票修改的条目（1 处）**：
   - [`Retrospectives.due`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/retrospective.ts#L55-L65)：`slot.setHours(schedule.hour, schedule.minute, 0, 0);` 在秋季回拨日 `01:00–01:59` 折叠小时或春季跳过日 `02:00–02:59` 不存在小时有单独问题（复现证据见 [evidence/r2-product-due-audit.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/r2-product-due-audit.log#L1-L42)）。符合任务书 [brief.md](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/brief.md#L66-L69)“不改定时产品的行为……产品问题只报告不修”，主控已另开 T-223，不在本票范围。

3. **判为“不会出错 / 不改”的条目，理由是否成立**：
   - [MetricsPage.tsx](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/app/MetricsPage.tsx#L20-L25)（及测试 [test_t162_role_records_metrics_e2e.py](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t162_role_records_metrics_e2e.py#L174-L181)）：`new Date(value + 'T00:00:00')` 再 `date.setDate(date.getDate() + 1)`（以及 `new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1)`），构造和递增都在本地日历午夜（`00:00:00`）上进行，不混用固定毫秒或固定偏移，无论当日 23、24 还是 25 小时，都准确得到次日本地 `00:00:00` 的 `toISOString()`。理由成立。
   - [renderer.tsx](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/app/renderer.tsx#L90-L97)：`since(iso, now)` 用 `(now - Date.parse(iso)) / 1000` 与 `86400` 比较，计算的是两个绝对时刻之间经过的相对时长（秒数），不是日历日期边界或墙钟日程。理由成立。
   - [scripts/inbox](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/scripts/inbox#L14)（及第 30–38、403 行）：`COPY_REMINDER_PERIOD = dt.timedelta(days=7)`，其时间戳经 [`timestamp`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/scripts/inbox#L30-L38) 转为 `dt.timezone.utc`，`now` 也是 `dt.datetime.now(dt.timezone.utc)`（第 403 行），全链路在 UTC 下比较绝对时长，无本地夏令时。理由成立。
   - [test_t195_native_link_e2e.py](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t195_native_link_e2e.py#L391-L392)：`tomorrow = datetime.now() + timedelta(days=1)` 后接 `tomorrow.strftime('%Y/%m/%d')`。Python 的 naive `datetime.now()` 取本地墙钟年月日时分秒，加 `timedelta(days=1)` 是纯公历日期加 1 天，不经过固定 UTC 偏移换算，因此 `strftime('%Y/%m/%d')` 永远得到本地日历“明天”的年月日。理由成立。
   - [test_t124_controller_e2e.py](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t124_controller_e2e.py#L384-L386) 与 [test_t167_codex_start_e2e.py](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t167_codex_start_e2e.py#L77)：`reset + 86400` 和 `int(time.time()) + 86400` 均为模拟配额重置的未来 Unix 秒时间戳，不涉及本地日历目录或墙钟日程。理由成立。
   - [test_t107_daemon_readonly.mjs](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t107_daemon_readonly.mjs#L40)、[controlled_quality_pty.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/controlled_quality_pty.ts#L34-L35)、[docs/assets/demo.js](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/docs/assets/demo.js#L713-L714)：只格式化当前 `new Date()`，无跨日推算。理由成立。

4. **是否漏掉同类写法**：
   - 核查 [evidence/r2-audit.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/r2-audit.log#L1-L403) 与 [evidence/r2-audit-wide.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/r2-audit-wide.log#L1-L2065) 全仓搜索结果（涵盖 `86_400_000`、`86400`、`setDate`、`getDate`、`setHours`、`timedelta`、`astimezone`、`ZoneInfo`、`TZ`），未发现任何遗漏的“本地日历步长配固定 24 小时终点”或“固定偏移跨日推算墙钟”写法。

---

### 4. 设计与任务边界

- **无冗余或防御性分支**：[change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/change.diff#L1-L360) 仅含 [workbench/README.md](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/README.md#L1166-L1169)、[codexScanDays.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/codexScanDays.ts#L1-L12)、四处调用文件（[nativeLink.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/nativeLink.ts#L140)、[panes.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/panes.ts#L1245)、[trajectoryArchive.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/trajectoryArchive.ts#L83-L101)）、测试时钟模块 [local_calendar.py](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/local_calendar.py#L1-L10)、两处 E2E 测试（[test_t136_retrospective_e2e.py](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t136_retrospective_e2e.py#L289)、[test_t137_reflect_e2e.py](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t137_reflect_e2e.py#L163-L265)）及两个新回归测试（[test_t221_codex_scan_days.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t221_codex_scan_days.ts#L1-L118)、[test_t221_calendar_clocks.py](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t221_calendar_clocks.py#L1-L39)）。
- **无 fallback、无重试、无兼容分支、无平行路径、无吞异常**：旧的 `86_400_000` 循环已被直接替换删除（[change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/change.diff#L33-L85)）。
- **未越出任务书边界**：
  - 未改 Codex 记录目录的 `sessions/YYYY/MM/DD` 命名约定（[nativeLink.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/nativeLink.ts#L141)、[panes.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/panes.ts#L1246)、[trajectoryArchive.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/trajectoryArchive.ts#L84)）；
  - 未改 [`nativeLink`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/nativeLink.ts#L49-L55) 的置灰规则；
  - 未改 [retrospective.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/retrospective.ts#L55-L65) 复盘定时产品的行为。

---

### 5. 文档核对

- [candidate/workbench/README.md](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/README.md#L1166-L1169)（对应 [change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/change.diff#L9-L13)）新增段落：
  - 描述 [`src/codexScanDays.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/codexScanDays.ts#L1-L12) 按本地日历计算日期范围：原生链接与窗格扫描从启动当天开始（`startDayOffset = 0`），终端主控与复盘的轨迹归档查找从启动前一天开始（`startDayOffset = -1`），均扫描到本地明天，包含两端，覆盖夏令时切换、月末与年末；
  - 描述 T-136、T-137 的复盘验收时钟通过 [`tests/local_calendar.py`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/local_calendar.py#L1-L10) 使用与后台 Node 相同的具名本地时区，以及回归检查 [`tests/test_t221_codex_scan_days.ts`](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t221_codex_scan_days.ts#L1-L118) 和 `python3 tests/test_t221_calendar_clocks.py`（[test_t221_calendar_clocks.py](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t221_calendar_clocks.py#L1-L39)）。
  - 与候选代码及测试行为完全一致。

---

## 三、验收条目逐条状态与依据

对照 [ticket.md](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/ticket.md#L30-L37) 的 6 条验收条件：

1. **修前经真实入口留下红态：在 `TZ=America/New_York`、启动时刻取回拨日晚间的条件下，扫描范围不含次日（可用注入的时刻调用产品里的同一段日期计算，不另写一份）。**
   - **状态**：`PASS`
   - **依据**：
     - 原逻辑抽取件 [evidence/extracted-codexScanDays.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/extracted-codexScanDays.ts#L1-L6) 与四处调用补丁 [evidence/extraction.patch](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/extraction.patch#L1-L72)；
     - 红态日志 [evidence/red-extracted.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/red-extracted.log#L1-L399)：在 `TZ=America/New_York` 下，`fall-T219-exact-launch/range/0`（`since: '2026-10-31T22:34:14-04:00'`, `now: '2026-10-31T22:35:14-04:00'`）实测输出 `["2026/10/31"]`，缺少次日 `"2026/11/01"`（第 68–78 行），四个真实消费者在 `"2026/11/01"` 上的检查全部失败（第 94–124 行）；
     - 另有 T-219 初始真实运行红态 [context/T-219-evidence/baseline-06c.json](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/context/T-219-evidence/baseline-06c.json#L120-L133) 与诊断 [context/T-219-evidence/dst-america-02.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/context/T-219-evidence/dst-america-02.log#L1-L12)。

2. **修后同一条件下扫描范围含次日；春季跳过、秋季回拨、月末、年末四种边界都核对起止日期，期望值按日历推算，不取实现的输出。**
   - **状态**：`PASS`
   - **依据**：
     - 候选实现 [codexScanDays.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/codexScanDays.ts#L1-L12)（[change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/change.diff#L164-L175)）；
     - 专项测试 [test_t221_codex_scan_days.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/tests/test_t221_codex_scan_days.ts#L19-L44) 硬编码 8 组日历期望值（涵盖秋季回拨、春季跳过、月末、年末及 `startDayOffset = -1` 边界）；
     - Worker 绿态输出 [evidence/green-days.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/green-days.log#L1-L5)（`status: "PASS"`, `total: 196`, `failed: []`）；
     - 主控独立重跑输出 [controller/runs.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/controller/runs.log#L2)、[controller/scan-days.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/controller/scan-days.log#L1-L5) 与 [controller/scan-days.json](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/controller/scan-days.json#L1-L60)。

3. **四处循环都改用同一段日期计算，代码里不再有“本地日历步长配固定 24 小时终点”的写法。**
   - **状态**：`PASS`
   - **依据**：
     - 四处改动：[nativeLink.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/nativeLink.ts#L140)（[change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/change.diff#L33-L34)）、[panes.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/panes.ts#L1245)（[change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/change.diff#L54-L55)）、[trajectoryArchive.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/trajectoryArchive.ts#L83) 与 [trajectoryArchive.ts](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/candidate/workbench/src/trajectoryArchive.ts#L101)（[change.diff](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/change.diff#L75-L85)）；
     - 变异区分度证据：[evidence/mutant-miss-native.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/mutant-miss-native.log#L1-L42)、[evidence/mutant-miss-panes.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/mutant-miss-panes.log#L1-L42)、[evidence/mutant-miss-archive-cwd.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/mutant-miss-archive-cwd.log#L1-L79)、[evidence/mutant-miss-archive-id.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/mutant-miss-archive-id.log#L1-L79)、[evidence/mutant-drop-previous.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/mutant-drop-previous.log#L1-L151)；
     - 全仓扫描证据：[evidence/final-scan.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/final-scan.log#L1-L11) 与 [evidence/r2-audit.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/r2-audit.log#L17-L402)。

4. **`test_t195_native_link_e2e.py` 在当前日期正常运行通过；T-219 的第 6 项改判为已修复并附证据。**
   - **状态**：`PASS`
   - **依据**：
     - [evidence/regression-t195.json](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/regression-t195.json#L1-L26)（及第 157–186 行）：在 `2026-10-31` 回拨前夜窗口内（时间戳 `2026-11-01T02:32:51Z`，即纽约时间 `2026-10-31 22:32:51 EDT`）运行 `test_t195_native_link_e2e.py`，`status: "PASS"`，包含 `managed_codex_unsearchable_day_grey` 在内的 15 项检查全部通过（`during.link.available: false`，原因为 `读不了 Codex 的记录 .../sessions/2026/11/01（EACCES: permission denied, scandir '.../sessions/2026/11/01'），分不出现在是哪个线程`）。

5. **`test_t136` 的定时检查跨夏令时仍按本地墙钟推算日程时刻：修前在跨回拨的条件下失败，修后通过；同类写法的普查结果逐处列出判定。**
   - **状态**：`PASS`
   - **依据**：
     - 修前红态：[evidence/regression-t136.json](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/regression-t136.json#L1-L18)（及第 134–144 行）、[evidence/regression-t136-baseline.json](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/regression-t136-baseline.json#L1-L18)、[evidence/diagnostic-t136.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/diagnostic-t136.log#L1-L12)（`fired: ["2026-11-02T15:00:00.000Z"]` 对应 `10:00 EST`，而固定 `-04:00` 偏移算出的 `slot` 为 `14:00Z`，导致 `schedule_fires_once_at_its_time` 失败）；以及 T-137 同类红态 [evidence/r2-red-t137.json](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/r2-red-t137.json#L204-L209)；
     - 修后绿态：Worker 运行结果 [evidence/r2-green-t136.json](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/r2-green-t136.json#L1-L21)（及第 134–147 行：`schedule_fires_once_at_its_time`、`schedule_off_does_not_fire`、`start_failure_recorded_on_run`、`retry_after_failed_start_keeps_range` 全部通过）、[evidence/r2-green-t137.json](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/r2-green-t137.json#L1-L21)；主控重跑结果 [controller/runs.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/controller/runs.log#L8-L11)、[controller/t136.json](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/controller/t136.json#L1-L21)（及第 134–147 行）、[controller/t137.json](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/controller/t137.json#L1-L21)；
     - 全年固定日历基准测试与变异：[controller/calendar-clocks.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/controller/calendar-clocks.log#L1-L6)（绿态 `OK`）与 [controller/mutant-fixed-offset.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/controller/mutant-fixed-offset.log#L1-L66)（固定偏移变异 `FAILED (failures=4)`）；
     - 普查记录与逐处判定：[evidence/r2-audit.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/r2-audit.log#L1-L403)、[evidence/r2-audit-wide.log](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/r2-audit-wide.log#L1-L2065)、[evidence/r2-audit-decisions.md](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/r2-audit-decisions.md#L1-L60)、[evidence/REPORT.md](file:///Users/luckye/Documents/Code/a2a-review/T-221-r1/evidence/REPORT.md#L140-L169)。

6. **独立审查（agy 只读）无未处理的阻塞意见。**
   - **状态**：`PASS`
   - **依据**：本审查报告（只读独立核查全部代码差异、测试期望推算、变异证据、主控重跑记录与全仓普查结果，无阻塞意见）。

---

PASS