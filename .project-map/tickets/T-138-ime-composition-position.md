---
id: T-138
title: 终端输入法：在行中间插入时提交的文字错位（取到输入框末尾的字）
type: build
status: open
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

- [ ] 真实 Electron 红态：修前在行中间提交“打出”，发给 PTY 的是末尾两字；修后是“打出”。
- [ ] 已知坏实现（还原修复）被该测试抓住。
- [ ] 连续多次中间插入、回车后再插入都正确。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

