---
id: T-192
title: 任务页显示门禁全程，已结束的票不再是空页
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by:
ready_rev:
---

## What to build

来源：[findings/2026-10-27-two-real-uses.md](../../findings/2026-10-27-two-real-uses.md)（U07、U08）。决定见 [T-189](T-189-real-use-fixes-decisions.md)。

- 点进任务时，不论有没有存活窗格，都显示：任务卡（目标、路径、完成条件）、每个 attempt 的时间线（认领、交付、检查、审查、集成、回收及原因）、审查报告、打分、集成提交与尾注。有存活窗格时窗格在上，记录在下。
- 门禁增加任务关闭状态（主控经门禁关闭），关闭的票不再显示“待认领”。
- 对照产品页第 1 节第 3 步的说法，做不到的改产品页。

## Acceptance

- [x] 已回收的票（如 a2a+T-138）点进去能看到上述内容，不是空页。
- [x] 关闭后的票在任务格显示“已关闭”。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

范围外问题经问题上报。

## Resolution

2026-10-27 实现；同日装进 /Applications 后在用户真实状态里点开 a2a+T-138，整页显示任务卡与时间线，两条验收已勾。实现与证据见 [evidence/2026-10-27-batch28/T-192/RESULTS.md](../../evidence/2026-10-27-batch28/T-192/RESULTS.md)。

- 根因：没有保存过布局的任务，界面放一个跟随当前 attempt 的默认窗格；attempt 回收后这个窗格是空的，盖住整页。门禁也没有关闭状态。
- 改动：
  - 门禁新增只读 `task_history`（`workbench/src/gates/taskHistory.ts`）和 `close`。
  - 没有打开的窗格时整页显示 `TaskRecord`；当前有 worker 时给出“打开 worker 会话”按钮。有窗格时记录收在底部。
  - 产品页第 3 步与工作台 README 同步。
- 证据：
  - 隔离后台经真实入口取得红态、绿态。
  - 一条真实 Claude Code worker 走完交付、verify 打回、上报、撤销、回收，之后从任务格点进是整页记录（ui/11～13）。
  - `history_check.ts` 有 1 个绿态，`mutants.sh` 的 11 个已知坏实现全部 FAIL。
  - 独立审查 6 轮，最后一轮结论“可合并”。
- 两条验收都已勾：
  - a2a+T-138 在安装版里的记录页见 ui/14、ui/15。它没走到审查与集成，所以页面没有那三段。
  - 有审查、打分、集成的票，页面内容是用真实事件夹具验证的；真实回收的那次没有经过审查与集成。
- 其他没有验证：N3 忙碌时禁用按钮，没有在界面里复验；close 在并发与崩溃恢复下的行为。
- 行为变化：停在记录页时派发新 worker，页面不会自动切过去，需要点按钮。

