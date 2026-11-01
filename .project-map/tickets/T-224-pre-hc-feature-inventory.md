---
id: T-224
title: 换运行时之前计划过的功能，逐项看 hc 能否做得更好
type: research
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## Question

用户 2026-10-31：“最好能把 Core 移植过来之后，能把我们原先想设计的功能，就是之前没换运行时时候想做的东西更好的实现”。地图的 hc 运行时待切项要求切片前先盘点。

要回答：

1. 换到 hc（T-209）之前，计划过但没做、做了一半、或者做了但受 node-pty 运行时限制而做得不好的功能有哪些。来源包括：地图的 *Not yet specified*、未关闭和 `ready: no` 的票、`findings/` 里两次真实使用和 lcu 实测的报告、`intent.md`、各规格的 Out of scope 与后续切片、README 路线图里旧 Enchanted 的未来 feature。每项写出处（文件与行号或票号）。
2. 每项在 hc 上能否做得更好：靠 hc 的哪项能力（attach/detach、多 viewer、OSC 7501、父子通知、label、后台重启接回等），这项能力是否已被 T-211 实测证实；没证实的写成待证事实，并给出最小探针。
3. 每项建议放进哪个待切切片（受管窗格走 hc；后台重启接回原 attempt；状态统一取 hc 事件；worker 卡住推给主控；跨项目“等你”分组与问题界面），还是需要新切片，或者 hc 帮不上忙、维持原计划。
4. 哪些项会改变已关闭的决定或规格，需要用户裁定。

只给依据和选项，不实现，不改已关闭的决定。

## Resolution

（未开始）
