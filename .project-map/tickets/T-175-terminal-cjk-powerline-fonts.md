---
id: T-175
title: L02：终端中文字间距与对齐、powerline 字形
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

来源：findings/2026-10-25-lcu-real-use.md；用户 2026-10-24 逐字：“然后你再用 lcu 测试一下软件看看能不能发现其他问题”。

现象见报告 L02（中文字间多空隙、中文表格边框不齐、p10k 分隔符成方块）。目标：终端字形与宽度与用户常用终端（Terminal/Herdr）一致：CJK 按双宽且无额外间隙，表格竖线对齐；powerline/Nerd 字形有可用回退；终端字体在设置里可改（逗号分隔的回退列表）。先读 xterm.js 6 文档与现有依赖（unicode11/unicode-graphemes addon、customGlyphs、字体回退），不自造。

通用：先在真实 Electron 隔离实例复现并留红态，再修根因；真实 Claude 用 claude-haiku-5-5；不加重试掩盖未知；不用正则判断意图；agy 独立审查。

## Acceptance

- [ ] 真实 Electron：同一段中文与中文表格在修前错位、修后对齐（截图对照）；p10k 提示符显示正常。
- [ ] 设置里改终端字体立即生效且重启保留。

## 不做

范围外的问题经问题上报，不顺手改。
