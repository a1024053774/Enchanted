---
id: T-159
title: F03：“向右分屏”换成新普通终端，原 worker 不并排
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：用户 2026-10-23 逐字：“全部 7 条 + 3 条模型行为对策”（选项：切全部修复票）；报告 findings/2026-10-23-real-user-dogfood.md，执行主控 needs-decision 20261023T222913Z。

报告 F03（严重）：在任务视图 worker 菜单点“向右分屏”，主区只剩项目根目录的新普通终端，原 worker 消失，标题仍是该任务。
目标：分屏保留当前窗格并增加右侧窗格；任务 agent 与普通终端若不能同屏，操作前说明。与 T-139 的视图模型一致，不另做一套。

通用要求：先在真实 Electron（隔离实例）复现并留红态证据，再修最小根因层；不加自动重试掩盖未知；使用 `CONTEXT.md` 术语；修改界面文案前读 `frontend-less-ai-tone`。

## Acceptance

- [x] 真实 Electron：任务视图点向右分屏后，原 worker 与新窗格并排，窗格数、类型、目录与菜单所述一致。
- [x] 红态：修前只有一个新终端。
- [x] 新窗格是普通终端（用户 2026-10-24：“任务视图里也可以分屏吧,比如说我想对这个任务有疑问,想开一个分屏侧边聊天来讨论这个任务”，经构思主控 answer 20261024T024128Z-001 转述）：不计入 worker、不占任务路径、不算人工介入；侧栏/窗格头标“普通终端”；默认目录为任务仓库根（不是 worker worktree）。T-139“普通终端只在项目层”的说明与测试同步改为允许任务视图并排普通终端。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-24 关闭，PASS。修前红态（outside-01）：任务视图点向右分屏后原 worker 被新普通终端替换。首个候选走“任务视图禁用分屏并说明”分支，审查 01 判 INCOMPLETE（验收写并排），经 needs-decision 用户改定：任务视图允许并排普通终端。修复：`workbench/app/main.ts`、`renderer.tsx` 让任务视图分屏保留 worker 并在旁边新开普通终端（角色 shell，目录为任务仓库根），不计入 worker、不占任务路径、不记人工介入，窗格头标“普通终端”；撤回禁用分支；`test_t139_*` 与 README 同步此规则。outside-04：两个变异（替换 worker、普通终端输入被记为 worker 人工介入）在预期断言上被拒，T-139/T-143 回归通过；green 因测试正向对照取错基线报错（测试缺陷）。outside-05 修后 green 46 项 PASS（含真实正向对照）。审查 02 agy PASS；P3：T-139 ticket 正文旧规则未同步，已在 T-139 末尾加注。合并 fd00ec8f8。证据 `evidence/2026-10-23-batch24/T-159/RESULTS.md`。
