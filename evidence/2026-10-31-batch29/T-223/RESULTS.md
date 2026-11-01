# T-223 结果（主控记录，2026-11-01）

结论：**PASS**。`Retrospectives.due()` 改为从查询时刻只取本地年月日与星期，用 `new Date(年, 月, 日, 时, 分)` 一步构造目标时刻，回退一周也重新构造。春季跳过日查询不再晚一小时，跳过段延到本地午夜的时区也不会落到次日。

## 候选与提交

- 基线 `76f969963`，分支 `t223-due-spring-gap`，worktree 提交 `3841c635d`，cherry-pick 到 main 为 `ed5ad223b`。
- worktree 的差异与 worker 第三轮冻结的 `candidate-round3.patch`、审查目录的 `change.diff` 相同（去掉 `index` 行后比较），提交只含这三份文件：`workbench/src/retrospective.ts`、`workbench/README.md`、新增 `workbench/tests/test_t223_retrospective_due.ts`。
- 从基线到合入前的 main，`workbench/README.md` 有 T-212 的改动（`8006f37ea`），段落不重叠，cherry-pick 没有冲突。合入后在 main 上按三个时区重跑新测试：纽约 26 项、Nuuk 12 项、Scoresbysund 12 项全过。

## 三轮经过

- 第一轮：worker 先在 `FAILURE-MODES.md` 列出 F1–F12，再修改。
- 第二轮：改成“先 `setDate` 再 `setHours`”，纽约 26 项全过。agy 第一次审查把“查询时刻的墙钟在目标日期不存在”判为非阻塞，理由是现行时区不会从 23:00 跳到次日 00:00。主控扫描全部时区，发现 America/Nuuk、America/Scoresbysund 在 2026-03-28、2027-03-27 正是这样跳；又经真实 `due()` 复现：第二轮候选在 Nuuk 返回周日 `2026-03-29T11:00:00.000Z`，正确值是周六 `2026-03-28T12:00:00.000Z`，同一周会重复触发。主控据此改判为阻塞，退回（[controller/REVIEW-agy-r1-controller-check.md](controller/REVIEW-agy-r1-controller-check.md)）。
- 第三轮：直接按数字日期构造时刻，新增 Nuuk、Scoresbysund 两组，各 12 项。

## 验收条目

| 条目 | 状态 | 依据 |
| --- | --- | --- |
| 修前经真实 `Retrospectives.due()` 留下红态，春季条件下晚一小时 | PASS | 基线纽约组 `F1/spring-query-for-earlier-Monday` 得 `2026-03-02T08:30:00.000Z`，期望 `2026-03-02T07:30:00.000Z`；另有两个 F4、三个 F11 失败。worker `r3-baseline` 与主控 `controller/r3/base-red-*` 一致 |
| 修后同一条件得 `2026-03-02T07:30:00.000Z`；跳过日、重复时刻、普通日与月末年末另核对；期望值按日历手算 | PASS | worker 与主控绿态三组共 50 项全过；规则写进 `retrospective.ts` 注释和 README（不存在的时刻按转换前偏移顺延，重复时刻取较早一次）；期望值写死在测试里，agy r3a 逐项手算、主控用 node 复算一致 |
| `test_t136`、`test_t137` 在当前日期仍通过 | PASS | worker 与主控各跑一次，T-136 13 项、T-137 10 项全过，四份 summary 都是 PASS |
| 独立审查（agy 只读）无未处理的阻塞意见 | PASS | 第三次审查拆成 r3a（代码、规则、测试）与 r3b（运行证据），都是 PASS，没有阻塞意见；主控逐条核对了引用（[controller/REVIEW-agy-r3-controller-check.md](controller/REVIEW-agy-r3-controller-check.md)）。第二次审查的引用大量编造，已作废（[controller/REVIEW-agy-r2-controller-check.md](controller/REVIEW-agy-r2-controller-check.md)） |

## 红态与变异

各次运行的失败项与失败值由 agy r3b 逐行列出，主控用脚本对照各 JSON 复核，82 行全部一致（[controller/REVIEW-agy-r3b.md](controller/REVIEW-agy-r3b.md)）。

| 运行 | 纽约 | Nuuk | Scoresbysund |
| --- | --- | --- | --- |
| 基线 `76f969963` | 6 项失败 | 2 项失败（`F12/before-normalized-slot`、`F12/2027-before-normalized-slot`） | 同 Nuuk |
| 第二轮候选（已知坏实现） | 全过 | 7 项失败，首项 `F12/sunday-late-query` 得 `2026-03-29T11:00:00.000Z` | 同 Nuuk |
| 第三轮候选 | 全过 | 全过 | 全过 |
| worker 变异 `hours-before-date` | 4 项失败 | 3 项 | 3 项 |
| worker 变异 `date-only-rollback` | 2 项失败 | 2 项 | 2 项 |
| worker 变异 `query-clock-round2` | 全过 | 7 项失败 | 7 项 |
| 主控变异 `mutant-slot-rollback`（[diff](controller/r3/mutant-slot-rollback.diff)） | 全过 | 2 项失败 | 2 项 |

主控的 Nuuk 探针在第三轮候选上四个场景都返回 `2026-03-28T12:00:00.000Z`（[controller/r3/nuuk-probe-candidate.log](controller/r3/nuuk-probe-candidate.log)）。主控复跑脚本 [controller/run-ctl-r3.sh](controller/run-ctl-r3.sh)，汇总 [controller/r3/runs.log](controller/r3/runs.log)。

## 审查记录

| 次 | 对象 | 结果 |
| --- | --- | --- |
| 第一次（r1） | 第二轮候选 | 引用核对通过；一条非阻塞意见被主控改判为阻塞，退回 |
| 第二次（r2） | 第三轮候选，一份报告看全部材料 | 结论 PASS，但检查项名、用例名与失败值大量编造；会话中途压缩过上下文。作废 |
| 第三次（r3a、r3b） | 第三轮候选，拆成两份 | 都是 PASS，r3a 无意见，r3b 一条非阻塞；引用全部对上，两份会话都没有压缩上下文 |

r3b 的非阻塞意见：worker 的 T-136 运行在 13 项全部通过后，第一次清理 fixture 时报 `OSError [Errno 66] Directory not empty: home`，第二次清理删净。worker 保留了 93 个残留文件；主控独立重跑的 T-136 清理正常，第二轮那次也正常。目前只出现过一次，不另开票，再出现时按同类问题开票。

## 证据归档（T-088）

| 清单 | 内容 | 文件数 | 字节 |
| --- | --- | --- | --- |
| [archive/worker-evidence.archive.json](archive/worker-evidence.archive.json) | `a2a-worktrees/T-223-evidence` | 233 | 5818952 |
| [archive/controller.archive.json](archive/controller.archive.json) | `a2a-worktrees/T-223-controller` | 58 | 384336 |
| [archive/review.archive.json](archive/review.archive.json) | 两个审查目录 `a2a-review/T-223-r1`、`T-223-r2` | 312 | 4332469 |
| [archive/fixtures.archive.json](archive/fixtures.archive.json) | 17 个 `/private/tmp` 现场（13 个 `t223-*` 源码副本，主控的 T-136、T-137 各两个） | 3718 | 230644259 |

归档在 `/Volumes/WD-Elements/a2a-evidence/2026-10-31-batch29/T-223/`。每个条目的源与副本文件数、字节数一致，没有特殊文件。核对后删除了原件。

仓库里只留 worker 报告 [REPORT.md](REPORT.md)、失败方式清单 [FAILURE-MODES.md](FAILURE-MODES.md)、第三轮失败值 [r3-failure-values.md](r3-failure-values.md) 和主控文件。报告里指向日志和 JSON 的相对链接，对应归档的 `worker-evidence/` 下同名文件。
