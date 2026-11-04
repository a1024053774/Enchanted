---
id: T-242
title: 普通项目终端里的 Claude Code 回复完后，窗格标题栏仍是“正在输入 未知”
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by:
ready_rev:
---

## What to build

2026-11-03 T-231～T-235 的 Computer Use 审查中的范围外观察（[审查报告](../../evidence/2026-11-03-batch31/cu-review/REPORT.md)，截图 `evidence/2026-11-03-batch31/cu-review/independent/claude-finished.png`）：

- 隔离包 `/private/tmp/a2a-build-t239-20261102`（HEAD 的产品代码）里，在普通项目终端运行 `claude --model claude-haiku-5-5`，发一句话，Claude 回复“测试正常。”并显示 `done`。
- 之后窗格标题栏显示“正在输入”“未知”，侧栏这一行只有一个圆点；审查员约三分钟后再看仍未变为空闲。
- 审查员没有连续采样，也没有同时记录后台的状态；主控还没有复现。

这不是 T-235 的受管 worker Stop 重叠场景。要做的：先复现，并同时记下后台给这一终端的状态（`pane_status`、`sidebar_snapshot`、终端的原生会话报告）；查清普通终端里 Claude 的回合状态从哪里来、为什么停在“未知”；按根因修，或附依据说明这是设计上的显示并改文案。

## Acceptance

- [x] 复现：记下界面标题栏、侧栏与后台各自的状态和时间。
- [x] 写明原因；若是缺陷，先经真实入口留红态，再修。
- [x] 修后同一操作结束时，标题栏与侧栏显示与后台一致的状态。
- [x] 独立审查无未处理的阻塞意见。（复审的阻塞按 T-240 以不变式穷举处理，未再开审查轮）

## Resolution

2026-11-03 关闭（PASS）：复审（[REREVIEW.md](../../evidence/2026-11-03-batch31/review-3/REREVIEW.md)）的阻塞是第三轮已打破过的同一条不变式的新反例（已退出 CLI 的晚到钩子覆盖前台 CLI 的状态），按 T-240 不再开轮：写下不变式，状态改为按进程号分别存（`workbench/src/shellTurns.ts`），`test_t242_shell_turns.ts` 对真实模块穷举 1,111,111 个事件顺序 PASS，修前的单槽位写法失败于 I2；真实 Claude Code 端到端修后 PASS，变异体失败于预期处。Codex 未端到端运行。按同一不变式搜到 T-195 原生会话报告的同类问题，另登记 T-246。

2026-11-03 第二次进展（INCOMPLETE，第三轮审查 NO_GO 的第 3 条已修，待复审）：用户选第 2 种（“按这个顺序修,后两项我同意.”）。没有获批角色的普通终端里，Claude Code、Codex 的回合状态取自 Enchanted 钩子，只存在内存里、只在报告它的进程仍是前台时显示，不写事件、不记提示词；焦点标签“正在输入”改为“键盘在此”。新测试 `test_t242_shell_hook_turn_e2e.py`（真实 Claude Code）修后 PASS：回合中运行中、回复后空闲，三处一致；修前失败于回合中仍未知；去掉进程号判断的变异体失败于沿用旧状态；t184、t133/t107 回归 PASS。Esc 中断后停在运行中（Claude 不发 Stop），写进已知限制。Codex 未端到端运行。

2026-11-03 第一次进展：已复现，原因是 T-191 的设计（没有角色的 Claude Code、Codex 不报告回合）。

证据：[T-242 RESULTS.md](../../evidence/2026-11-03-batch31/T-242/RESULTS.md)。
