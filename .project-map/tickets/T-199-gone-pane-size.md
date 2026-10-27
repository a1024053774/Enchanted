---
id: T-199
title: 后台重启后已消失的 worker 窗格报整数错误、内容空白
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

来源：T-192 装机时，a1024053774.github.io 的 T-1 的 agy worker 窗格显示 “Error: This API only accepts integers”（`evidence/2026-10-27-batch28/T-192/ui/16-installed-github-io-T-1-pane-error.jpg`）。用户 2026-10-27：“修复新发现的问题”。

后台重启后，进程已确认消失的 worker/reviewer 窗格由 `registerGone` 登记为没有终端的替身，`pane_status` 却返回 `size: {}`，界面据此调用 xterm resize 报错。让这类窗格的状态如实表示“没有终端尺寸”，界面不再报错。

## Acceptance

- [x] 修前版本经真实入口：重启后已消失的 worker 的 `pane_status` 为 `size: {}`；修后为 `null`，活窗格仍返回整数尺寸。
- [x] 界面打开这类窗格不再出现整数错误。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

worker 进程在后台退出后不退出、导致记为 pane_gone_unconfirmed 的情况（只记录观察）。

## Resolution

2026-10-27，状态 PASS，在开发版本上验证；用户 /Applications 里的 Enchanted 还没装上这个修复。证据见 [evidence/2026-10-27-batch28/T-199/RESULTS.md](../../evidence/2026-10-27-batch28/T-199/RESULTS.md)。

- 根因：`registerGone` 登记的替身没有终端，`status()` 却返回 `size: {}`。
- 修法：替身标记 `gone`，`status()` 对它返回 `size: null`。
- 端到端：T-124 的 restart-working 场景新增两项检查。工作树 PASS；修前版本 606a5e193 与变异 `gone-size-empty` 都在新检查上失败。
- 界面：修前出现报错；最终构建不再报错，窗格只读显示原输出。
- 独立审查 2 轮，末轮“可合并”。
- 顺带观察：被测 worker 在后台退出后仍不退出，导致重启记为 `pane_gone_unconfirmed`。没有查原因，不在本票范围。

