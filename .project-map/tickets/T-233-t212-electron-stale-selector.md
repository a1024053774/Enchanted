---
id: T-233
title: T-212 Electron 测试点侧栏行的选择器已过时，只因只有一个窗格才碰巧通过
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

T-230 写 UI 测试时发现，范围外（[结果记录](../../evidence/2026-10-31-batch29/T-230/RESULTS.md)）：`workbench/tests/test_t212_shell_hc_e2e.py` 的 Electron 场景用 `[data-terminal-launch=…]` 找侧栏行，界面上的属性是 `data-agent-launch`。这一下点击什么也没点到；测试找窗格用的是 `.pane[data-launch-id=…]`，不会核对错窗格。它现在能通过，是因为界面上只有一个窗格，不用点就显示出来了。多开一个窗格时，指定窗格可能不显示，测试会超时。

要做的：改用 `data-agent-launch`，在两个窗格时也能点开指定的那个。

## Acceptance

- [x] 修前留红态：多开一个窗格后，旧选择器点不开指定窗格，测试超时。
- [x] 修后两个窗格时，`--electron-screen` 与 `--electron-screen --mismatched-screen` 都通过。
- [x] 独立审查（GPT 只读，新开干净会话）无未处理的阻塞意见。

## Resolution

2026-11-03 关闭，**PASS**（[结果](../../evidence/2026-11-03-batch31/T-233/RESULTS.md)）。测试改用 `data-agent-launch`，并在打开窗口前多开一个终端窗格；旧选择器在两个窗格时超时（红态），新选择器两种模式都通过。GPT `gpt-6.1-terra` 审查（含 Computer Use：真实界面两个窗格逐个点开都对）与复审对本票均无阻塞（[审查](../../evidence/2026-11-03-batch31/cu-review/REPORT.md)、[复审](../../evidence/2026-11-03-batch31/cu-review/REREVIEW.md)）。
