---
id: T-020
title: 构建缓存、开源许可与代码复用
type: decide
status: closed
blocked_by: []
claimed_by:
supersedes:
---

## Question

构建缓存放在哪里，开源许可和代码复用怎么定？

## Resolution

2026-10-06 grilling 确认（[ledger](../../.grilling/a2a-gui-client.md) 的 D3、C9、D4、D11、C13）。

- a2a 与 Enchanted 的构建缓存默认放在外置盘 `/Volumes/WD-Elements`；外置盘未挂载时构建直接报错，不回退到内置盘。具体配置见 T-026。
- 永不闭源，自用并开源；允许直接复用 GPL 代码。并入 GPL 代码后整体以 GPL-3.0 发布。
- 能复用就复用，但不因此改变方向；多 CLI 支持优先参考 Herdr、Synara、muxel 的设计。
