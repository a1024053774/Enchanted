---
id: T-017
title: 工作台的技术底座
type: compare
status: closed
blocked_by: []
claimed_by:
supersedes:
---

## Question

工作台用什么技术底座，fork 出来的引擎怎么跟进上游？

## Resolution

2026-10-06 grilling 确认（[ledger](../../.grilling/a2a-gui-client.md) 的 D2、D8、D14、C14）。

选定：Herdr 0.9.3（`c4653a4`，Apache-2.0）引擎的硬分叉，加上 GPUI 界面。fork 中不自动拉取 Herdr 的在线检测清单；检测清单与上游修复以后单独同步。

被否决：
- 基于 Zed 二次开发：NO_GO，原因是 GPL、需要完整 Xcode、249 个 crate、线程模型与 Herdr 冲突，见[评估记录](../../findings/gui-client-assessment-2026-10-06.zh-CN.md)；
- fork muxel：GPL，依赖 tmux，约 10 个预设，没有给 agent 用的控制接口；
- 从头新建：基本等于重写 Herdr；
- 跟随上游 rebase：改名和结构调整会让冲突持续增加。
