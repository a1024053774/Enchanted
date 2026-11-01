# T-221 结果（主控记录，2026-10-31）

结论：**PASS**。四处按天扫描 Codex 记录的循环改用同一段按本地日历计算的范围，夏令时回拨当天不再漏掉次日。T-136、T-137 的复盘测试时钟改用具名本地时区，跨切换仍按墙钟推算日程时刻。普查中另查到 `Retrospectives.due()` 在春季跳过时刻晚一小时，不在本票范围，登记为 T-223。

## 候选与提交

- 基线 `d72a7746b`，分支 `t221-dst-day-scan`，worktree 提交 `b18af793f`，cherry-pick 到 main 为 `b54b691f7`。
- 提交的树对象 `124367b9` 与 worker 第二轮交的冻结候选 `r2-candidate.patch` 应用到基线后的树相同。从基线到合入前的 main，本票改动的 10 个文件没有其他提交。
- 产品改动：新增 `workbench/src/codexScanDays.ts`，`nativeLink.ts`、`panes.ts`、`trajectoryArchive.ts`（两处）改用它。测试改动：新增 `tests/local_calendar.py`、`test_t221_codex_scan_days.ts`、`test_t221_calendar_clocks.py`；`test_t136`、`test_t137` 改用 `local_now`；`workbench/README.md` 补一段说明。

## 验收条目

| 条目 | 状态 | 依据 |
| --- | --- | --- |
| 修前红态：`TZ=America/New_York`、回拨日晚间启动，扫描范围不含次日 | PASS | worker 把原循环原样抽成函数，四处产品代码调用它，在 T-219 的实际启动时刻下 196 项检查失败 38 项，`fall-T219-exact-launch/range/0` 只得到 `2026/10/31`（REPORT.md“红态、绿态与变异”） |
| 修后含次日；春季跳过、秋季回拨、月末、年末都核对起止日期 | PASS | 8 组用例的期望日期是写死的字符串，主控按日历逐组推算核对；主控复跑 196 项全过（`controller/runs.log` 的 scan-days） |
| 四处共用同一段计算，不再有“本地日历步长配固定 24 小时终点” | PASS | 四个漏改变异各只在对应消费者失败（5、5、8、8 项），去掉“前一天”的变异失败 16 项；worker 全仓扫描无旧写法 |
| `test_t195_native_link_e2e.py` 当前日期通过；T-219 第 6 项改判已修复 | PASS | worker 在回拨前夜（纽约 2026-10-31 22:51，`regression-t195.command.json`）运行 T-195，16 项全过，含 `managed_codex_unsearchable_day_grey`；T-219 第 6 项据此改判为已修复，见 T-221 票的 Resolution |
| `test_t136` 跨夏令时仍按墙钟推算：修前失败、修后通过；同类写法普查逐处判定 | PASS | 修前 `schedule_fires_once_at_its_time` 失败（诊断：测试按固定 `-04:00` 算出 14:00Z，后台按 10:00 EST 即 15:00Z 触发）；主控复跑 T-136 13 项、T-137 10 项全过；主控的固定偏移变异在四个跨切换用例失败、月末年末通过；普查 48 个命中逐行判定见 [r2-audit-decisions.md](r2-audit-decisions.md) |
| agy 只读审查无未处理的阻塞意见 | PASS | agy 无阻塞、无非阻塞意见；主控核对出几处引用与原始输出对不上，不影响结论（[controller/REVIEW-agy-r1-controller-check.md](controller/REVIEW-agy-r1-controller-check.md)） |

## 主控复核

主控在 T-221 worktree 上独立复跑了五个入口，脚本 [controller/run-ctl.sh](controller/run-ctl.sh)，汇总 [controller/runs.log](controller/runs.log)：

- 日期扫描单测（`TZ=America/New_York`）：196 项全过；
- 固定日历的时钟检查：6 组全过；
- 时钟改回无参数 `astimezone()` 的变异（[controller/mutant-fixed-offset.diff](controller/mutant-fixed-offset.diff)）：`FAILED (failures=4)`，失败的是 spring-two-days、fall-two-days、spring-week、fall-week；
- T-136 完整 E2E：13 项全过；
- T-137 完整 E2E：10 项全过。

六组时钟用例的期望值，主控按纽约时区的切换日期（2026-03-08、2026-11-01）逐组推算过，与测试一致。

## 普查发现的另一处缺陷

`workbench/src/retrospective.ts` 的 `due()` 先在查询当天 `setHours`，再回退到计划星期。查询日若是春季跳过日，02:30 先被归一成 03:30，回退到周一后也是 03:30。worker 用真实 `Retrospectives.due()` 复现：周一 02:30 的日程，在 2026-03-08 12:00 EDT 查询，应得 `2026-03-02T07:30:00.000Z`，实际 `08:30`。本票任务书规定不改定时产品的行为，主控另开 [T-223](../../../.project-map/tickets/T-223-retrospective-due-spring-gap.md)。

## 证据归档（T-088）

整份 worker 证据目录、主控复跑目录和 25 个测试现场，已归档到 `/Volumes/WD-Elements/a2a-evidence/2026-10-31-batch29/T-221/`：

| 清单 | 内容 | 文件数 | 字节 |
| --- | --- | --- | --- |
| [archive/worker-evidence.archive.json](archive/worker-evidence.archive.json) | `a2a-worktrees/T-221-evidence` | 119 | 1302645 |
| [archive/controller.archive.json](archive/controller.archive.json) | `a2a-worktrees/T-221-controller` | 13 | 107815 |
| [archive/fixtures.archive.json](archive/fixtures.archive.json) | 25 个 `/private/tmp` 现场（T-135、T-136、T-137、T-195 回归，日期单测与变异） | 9704 | 2570783299 |

每个条目的源与副本文件数、字节数一致，没有 socket 等特殊文件。副本由 T-219 归档用的同一脚本 [archive_evidence.py](../T-219/archive/archive_evidence.py) 生成。核对一致后，删除了 25 个 `/private/tmp` 原件。

仓库里只留 worker 报告 [REPORT.md](REPORT.md)、普查判定 [r2-audit-decisions.md](r2-audit-decisions.md)、两轮命令 [COMMANDS.md](COMMANDS.md)、[r2-COMMANDS.md](r2-COMMANDS.md) 和主控文件。报告里指向日志和 JSON 的相对链接，对应归档的 `worker-evidence/` 下同名文件。报告中“需要主控决定”各项已处理：agy 审查已做；T-136 时钟在第二轮修好；`due()` 缺陷登记为 T-223。
