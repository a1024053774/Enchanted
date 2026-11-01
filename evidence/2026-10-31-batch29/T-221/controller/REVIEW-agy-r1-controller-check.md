# T-221 agy 审查：主控逐条核对（2026-10-31）

对照冻结的审查副本 `/Users/luckye/Documents/Code/a2a-review/T-221-r1` 和主控复跑的原始输出核对。agy 的结论只在代码或原始输出对得上时采用。

## 结论

agy 判定无阻塞意见、无非阻塞意见，六条验收条目全部 PASS。主控采用“无阻塞意见”这一结论：它列出的根因、四处调用点、测试期望值和变异区分度，与代码和原始输出一致。各条验收条目的状态以主控自己的复跑（`runs.log`）和 worker 原始输出为准，不以 agy 的数值为据。

## 核对属实的部分

- 四处调用点的行号与写法：`nativeLink.ts:140`、`panes.ts:1245` 为 `codexScanDays(since)`，`trajectoryArchive.ts:83`、`:101` 为 `codexScanDays(since, Date.now(), -1)`。
- 测试时钟：`test_t136_retrospective_e2e.py` 第 30 行导入 `local_now`，第 289 行改用 `local_now(fixture.env)`；`test_t137_reflect_e2e.py` 第 163 行为 `when.isoformat()`，第 179、265 行改用 `local_now(fixture.env)`。
- `test_t221_codex_scan_days.ts` 的 8 组用例：期望值是写死的日期字符串，主控按日历逐组推算，`days`、`archive`、`before`、`after` 都对。
- 红态与变异的失败数，按日志里第一段 JSON 逐项统计：

  | 日志 | 失败 / 总数 | 失败所在检查 |
  | --- | --- | --- |
  | `red-extracted.log` | 38 / 196 | range 12、nativeLink 5、panes 5、archive-controller 8、archive-retro-at-start 8 |
  | `mutant-original-helper.log` | 38 / 196 | 同上 |
  | `mutant-miss-native.log` | 5 / 196 | 只有 nativeLink |
  | `mutant-miss-panes.log` | 5 / 196 | 只有 panes |
  | `mutant-miss-archive-cwd.log` | 8 / 196 | 只有 archive-retro-at-start |
  | `mutant-miss-archive-id.log` | 8 / 196 | 只有 archive-controller |
  | `mutant-drop-previous.log` | 16 / 196 | archive-controller 8、archive-retro-at-start 8 |

- `red-extracted.log` 里 `fall-T219-exact-launch/range/0` 实际为 `["2026/10/31"]`，期望 `["2026/10/31", "2026/11/01"]`。
- 主控固定偏移变异 `controller/mutant-fixed-offset.log`：`FAILED (failures=4)`，失败的正是 spring-two-days、fall-two-days、spring-week、fall-week 四个跨切换的用例，month-end、year-end 通过。
- 普查里 `Retrospectives.due()` 的问题已另开 T-223，本票不修，与任务书一致。

## 逐字对不上的引用（不采用）

- 验收条目 4 写 `test_t195_native_link_e2e.py` “15 项检查全部通过”：`evidence/regression-t195.json` 的 `checks` 实为 16 项，`status` 为 PASS，其中包括 `managed_codex_unsearchable_day_grey`。结论不变，数字不对。同一条写运行时刻为 `2026-11-01T02:32:51Z`（纽约 22:32:51）：`regression-t195.command.json` 记的开始时刻是 `2026-10-31T22:51:39-04:00`。（这一处在归档后补记，归档副本里没有。）
- 验收条目 5 引 `evidence/diagnostic-t136.log` 写“`fired: ["2026-11-02T15:00:00.000Z"]`”：该文件没有 `fired` 字段，内容是 `existing_test_slot` 为 `2026-11-02T10:00:00-04:00`、`calendar_new_york_slot` 为 `2026-11-02T10:00:00-05:00`。修前红态 `evidence/regression-t136.json` 里的 `fired` 是空列表 `[]`。agy 说的机理（测试用固定 `-04:00` 算出 14:00Z，后台按 10:00 EST 即 15:00Z 触发）与诊断记录一致，引文是编的。
- 主控固定偏移变异的四个失败，agy 写在第 12、24、36、48 行；实际 `FAIL:` 标题在第 8、22、36、50 行。

## 处理

无未处理的阻塞意见。上面几处引用错误不影响结论，不需要 worker 改动。
