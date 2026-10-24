---
id: T-168
title: N02：只读审查窗格文字重叠
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

来源：T-164 新发现 N02（一般）：切到 C 的 Haiku reviewer 只读查看时，出现重复、覆盖的文字和黑块（`evidence/2026-10-23-batch24/T-164/screenshots/17-reviewer-readonly-no-focus-error.png`）；没有键入字符。F02 的错误横幅已消失，但渲染不正常。T-164 要求新缺陷由执行主控建缺陷级票。

目标：先在真实 Electron 里用审查员会话回放复现，再查渲染时序（回放、切换、尺寸变化）的根因并修最小层。

## Acceptance

- [x] 红态：真实 Electron 复现只读审查窗格文字重叠，保留截图。
- [x] 绿态：同一序列下文字不重叠；T-161 只读焦点与 T-139/T-143 视图回归通过。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-24 关闭，PASS。写入者为执行主控本人（构思主控 answer 20261024T070244Z-ideation-answer-001 转述用户决定）。根因：只读窗格的 xterm 被拉伸到容器大小，PTY 却停在 160×45（只读窗格无输入凭据，不调 PTY）；CLI 按 PTY 列数做的相对重绘在另一宽度下擦错行、留残行，回放与实时都一样。修复：在线窗格状态带上 PTY 实际尺寸；只读窗格按该尺寸显示、可滚动、打开时停在最新的行；可写窗格不变，不改被查看程序的终端尺寸。
证据（受控 PTY，0 个模型请求，真实 Electron/后台/门禁）：修前红态 2/2（视图 154 列、PTY 160 列，残行）；绿态 3/3；两个坏实现（只读仍按容器适配、只读改 PTY 尺寸）均失败；T-161、T-139/T-143、T-091 等回归 PASS。独立审查 agy PASS（三条 P3 观察，无需改动；历史窗格尺寸未持久化为后续建议，结果中已列未覆盖）。合并 75f0a91dc；合并后 build、T-168、T-161、T-166 主机级与端到端、T-091 6/6 PASS。证据 `evidence/2026-10-23-batch24/T-168/RESULTS.md`。
