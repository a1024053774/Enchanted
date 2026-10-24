---
id: T-168
title: N02：只读审查窗格文字重叠
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

来源：T-164 新发现 N02（一般）：切到 C 的 Haiku reviewer 只读查看时，出现重复、覆盖的文字和黑块（`evidence/2026-10-23-batch24/T-164/screenshots/17-reviewer-readonly-no-focus-error.png`）；没有键入字符。F02 的错误横幅已消失，但渲染不正常。T-164 要求新缺陷由执行主控建缺陷级票。

目标：先在真实 Electron 里用审查员会话回放复现，再查渲染时序（回放、切换、尺寸变化）的根因并修最小层。

## Acceptance

- [ ] 红态：真实 Electron 复现只读审查窗格文字重叠，保留截图。
- [ ] 绿态：同一序列下文字不重叠；T-161 只读焦点与 T-139/T-143 视图回归通过。

## 不做

范围外的问题经问题上报，不顺手改。
