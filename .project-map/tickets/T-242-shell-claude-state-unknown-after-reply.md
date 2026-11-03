---
id: T-242
title: 普通项目终端里的 Claude Code 回复完后，窗格标题栏仍是“正在输入 未知”
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

2026-11-03 T-231～T-235 的 Computer Use 审查中的范围外观察（[审查报告](../../evidence/2026-11-03-batch31/cu-review/REPORT.md)，截图 `evidence/2026-11-03-batch31/cu-review/independent/claude-finished.png`）：

- 隔离包 `/private/tmp/a2a-build-t239-20261102`（HEAD 的产品代码）里，在普通项目终端运行 `claude --model claude-haiku-5-5`，发一句话，Claude 回复“测试正常。”并显示 `done`。
- 之后窗格标题栏显示“正在输入”“未知”，侧栏这一行只有一个圆点；审查员约三分钟后再看仍未变为空闲。
- 审查员没有连续采样，也没有同时记录后台的状态；主控还没有复现。

这不是 T-235 的受管 worker Stop 重叠场景。要做的：先复现，并同时记下后台给这一终端的状态（`pane_status`、`sidebar_snapshot`、终端的原生会话报告）；查清普通终端里 Claude 的回合状态从哪里来、为什么停在“未知”；按根因修，或附依据说明这是设计上的显示并改文案。

## Acceptance

- [ ] 复现：记下界面标题栏、侧栏与后台各自的状态和时间。
- [ ] 写明原因；若是缺陷，先经真实入口留红态，再修。
- [ ] 修后同一操作结束时，标题栏与侧栏显示与后台一致的状态。
- [ ] 独立审查无未处理的阻塞意见。

## Resolution

（未开始）
