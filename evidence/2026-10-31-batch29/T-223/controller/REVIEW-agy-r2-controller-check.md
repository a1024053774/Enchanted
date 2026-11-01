# T-223 agy 第二次审查：主控核对记录

2026-11-01，执行主控。审查报告原文见 [REVIEW-agy-r2.md](REVIEW-agy-r2.md)，对象是第三轮候选，审查目录 `a2a-review/T-223-r2`。会话库 `~/.gemini/antigravity-cli/conversations/b86dd148-86aa-4fb8-b4f1-fb84203cc752.db`，报告取自第 85 步。

## 结论：报告不采纳，作废重审

报告结论是 PASS、无阻塞、无非阻塞意见。但引用核对不过，这份报告不能当独立审查证据。

报告里 169 个文件链接都指向真实存在的文件，行号也在文件范围内。可是链接旁边写的名字和数值，大量在审查目录里找不到：

- **T-136、T-137 的检查项名全是编的。** 报告列了 T-136 的 14 个、T-137 的 10 个检查项名，例如 `schedule_triggered_once`、`retrospective_row_persisted`、`trigger_to_report_under_60s`。审查目录里任何文件都没有这些字串。真实名单在 `evidence/r3-t136-summary.json` 的 `checks`（13 项，例如 `schedule_fires_once_at_its_time`）和 `evidence/r3-t137-summary.json` 的 `checks`（10 项，例如 `schedule_off_by_default`）。
- **红态的用例名和失败值是编的。** 报告说纽约基线失败在 `F1/spring-forward-monday-after-sunday-gap`，actual `2026-03-09T07:30:00.000Z`、expected `2026-03-09T06:30:00.000Z`。真实的 `evidence/r3-baseline/America--New_York.json` 和 `controller/r3/base-red-New_York.json` 里，失败的是 `F1/spring-query-for-earlier-Monday`，actual `2026-03-02T08:30:00.000Z`、expected `2026-03-02T07:30:00.000Z`；另外五项是 `F4/gap-query-before-normalized-slot`、`F4/one-ms-before-normalized-slot`、`F11/already-ran-same-project`、`F11/other-project-does-not-block`、`F11/manual-run-does-not-block`。报告里的 `F4/gap-target-before-normalized-slot`、`F11/already-ran-canonical-slot` 等名字都不存在。
- Nuuk 一组的变异、第二轮红态里的若干名字与数值，同样找不到原文。

可能的原因：会话第 82 步出现了 agy 自己写的上下文摘要（`<summary> ## 1. Task Overview`），说明审查中途压缩过上下文；第 85 步的报告像是凭摘要和记忆写的，没有回到文件里取原文。这是模型行为记录，不改变本票候选本身的结论。

## 候选本身

主控自己的第三轮复跑（`controller/r3/`）各组结果都和 worker 证据一致，见第一次核对记录和 `r3/runs.log`。但票面要求 agy 独立审查无未处理的阻塞意见，这一条现在没有有效证据，记 INCOMPLETE。

## 处理

重审拆成两份更小的审查，各自只读一部分材料，减少上下文压缩：

- r3a：代码、规则与测试（原第 1、2、3、7、8 项，以及第 6 项里的改判依据）；
- r3b：证据（原第 4、5、6 项）。

提示词另加两条：名称与数值只能从文件原文复制；写最终报告前，把要写进报告的每个名称和数值重新打开文件核对一遍。
