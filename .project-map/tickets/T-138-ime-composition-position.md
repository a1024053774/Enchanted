---
id: T-138
title: 终端输入法：在行中间插入时提交的文字错位（取到输入框末尾的字）
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：用户 2026-10-23 在本 session 逐字（第 1 条）：“1.修复”

原因（源码依据，尚未复现）：xterm.js 6.0.0 的 `CompositionHelper` 在 compositionstart 记下隐藏输入框 `textarea.value.length`，提交时取 `substring(start)`；该输入框只在回车、Ctrl+C、失焦时清空，会累积已提交文字。插入点不在输入框末尾时，取到的是末尾两个字（用户见到打“dachu”出来“怪了”），候选框也浮在行尾。

1. 先用真实 Electron 加 CDP `Input.imeSetComposition`/`insertText` 复现：在行中间提交两字词，红态。
2. 修：每次提交后清空输入框，使下一次 compositionstart 的起点永远是 0 且光标在末尾。不改 xterm 源码。
3. 若复现不成立，报告真正原因再停下，不凭猜测修。

## Acceptance

- [x] 真实 Electron 红态：修前在行中间提交“打出”，发给 PTY 的是末尾两字；修后是“打出”。
- [x] 已知坏实现（还原修复）被该测试抓住。
- [x] 连续多次中间插入、回车后再插入都正确。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-23 关闭，PASS。

- 复现（执行主控沙箱外 `outside-01-20261023-131559-9292`，起点 b99f4869b）：错位只在读屏模式出现——隐藏输入框留着上次的文字，光标跟到行中间，中间插入“打出”时 PTY 收到“怪了”（输入框末尾两字）；读屏模式关闭（T-143 起的默认）时正确。
- 修复：`eb4f6bad1`（`renderer.tsx`：每次提交后等 xterm 读完本次提交再清空隐藏输入框，组字进行中不清；不改 xterm 源码、不关读屏模式），测试 `test_t138_ime_e2e.py`（`b3b6d520b`、`102db97ea`：第 2 轮测试驱动 ASCII 只发 char 不发 keydown，改为完整按键序列），合并 `57ce6e939`；README `7436f6014`。
- 验收（第 3 轮 `outside-03-20261023-134525-51971`）：两种读屏模式下，三次中间插入、回车后再插入、ASCII 输入全部正确；起点红态与还原修复的变异都在读屏模式四处中间插入失败（期望“打出”，实际“怪了”）；T-139/T-143 通过，T-091 与起点同样失败（已知过时）。测试用 CDP `Input.imeSetComposition`/`insertText` 驱动，Chromium 的 compositionend 不是 trusted 事件，测试如实记录；没有用真实系统输入法。截图归档在外置盘 `a2a-evidence/2026-10-23-batch23/T-138/`。
- 独立审查：agy gemini-3.8-flash-high，PASS。三条 P3：读屏模式下原生输入框没有可朗读的未回车字符（终端内容仍由无障碍树朗读）；非标准输入法用 Esc 取消时若留下字符，要等下一次输入才清空；README 过期已更新。
- 合并后回归 07（7436f6014）：32 项全部通过。

