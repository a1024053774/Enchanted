---
id: T-128
title: 后台第二次重启后，被打断的 worker、reviewer 与 monitor 仍要登记或恢复
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

来源：T-123 端到端开发运行（2026-10-22）。执行主控在 T-124 已批准范围内自建的缺陷级 ticket。

事实：T-124 的恢复逻辑只处理“被这一次重启打断”的记录（`pane_recovered.daemon` 等于当前后台）。后台连续重启两次时，第一次重启已经给 worker 写过 `pane_recovered`，第二次就跳过了：worker 既不登记为已停止，门禁也找不到它的窗格，`verify`、`reclaim` 和 run 续跑都返回 `unknown_pane`；monitor 在第二次重启后也不会恢复。T-123 开发运行 `dev3` 的事件序列：`pane_recovered`、`pane_gone_confirmed` 只出现在第一次重启（seq 111、117），第二次重启（seq 125）之后没有。

要做的：曾经被恢复过、尚未归档的 worker、reviewer 与 monitor 记录，每次后台启动都按 T-124 的规则处理：worker、reviewer 确认进程已退出后登记为已停止，monitor 按原启动记录恢复。

## Acceptance

- [x] 后台连续重启两次后，交付过的任务仍能 `verify`、审查、集成（T-123 端到端的迁移场景）。
- [x] 去掉修复（只认这一次重启）的变异在同一场景失败于 `unknown_pane`。
- [x] T-124 的 restart-working、restart-verified 变体仍通过。

## Resolution

2026-10-22 PASS，随 T-123 一起交付（候选 1 f0188d772，最终候选 a04c60a50）。`workbench/src/panes.ts` 的恢复循环现在处理每一个曾被恢复过、尚未归档的 worker、reviewer 与 monitor，不再只处理被这一次重启打断的。证据：T-123 端到端 `migrated_attempt_reclaimed`、`migrated_task_continues_to_integration` 绿态；变异 `gone-only-first-restart` 失败于 `unknown_pane`；T-124 的 restart-working、restart-verified 变体通过。见 [T-123 候选 2 RESULTS](../../evidence/2026-10-22-batch20/T-123/candidate-2/RESULTS.md)。
