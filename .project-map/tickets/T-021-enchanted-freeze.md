---
id: T-021
title: Enchanted 的搁置与并入
type: decide
status: closed
blocked_by: []
claimed_by:
supersedes:
---

## Question

Enchanted 怎么处理？

## Resolution

2026-10-06 grilling 确认（[ledger](../../.grilling/a2a-gui-client.md) 的 C8、D5）。Enchanted 搁置，功能在 M1 之后并入工作台。

执行记录（2026-10-06）：在 Enchanted 目录执行 `git init -b main` 并提交快照 `3e2ad91`。6 个上游克隆（tokei、agent-trail、codeburn、status-trio、tokscale、toknotch）都没有未提交改动或未推送提交，以 submodule 固定在当前提交。122 MB 的 `plans/enchanted-r5/evidence/a1-launch-attempt-v1.mov` 超过 GitHub 的单文件上限，留在磁盘但不入库。随后提交 `b0094c4`，在 Enchanted 的 AGENTS.md 中标明冻结。
