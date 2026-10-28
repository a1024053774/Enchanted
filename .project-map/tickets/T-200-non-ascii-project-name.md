---
id: T-200
title: 中文等非 ASCII 目录名的项目在界面上显示为 project
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

来源：真实用户式试用第 1 轮（[RESULTS](../../evidence/2026-10-27-batch28/UAT-01/RESULTS.md) 发现 2）。打开 `/private/tmp/uat/repos/我的 项目` 后，侧栏和标题都显示 `project`。

项目号只允许 `[A-Za-z0-9_.-]`（`daemon.ts` 的 `project_open`），目录名去掉其余字符后为空就用 `project`，第二个这样的目录是 `project-2`。项目号本身不改；界面上项目的名字改用目录名，项目号只在需要时作为辅助信息。

## Acceptance

- [x] 修前版本经真实入口：打开名为中文的 Git 目录，界面显示 `project`；修后显示目录名。
- [x] 两个中文名目录同时打开时，界面能区分；项目号与门禁记录不变。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

改项目号的生成规则；已有项目的迁移。

## Resolution

2026-10-27 PASS。根因：项目号只留 `[A-Za-z0-9_.-]`，中文目录的项目号成了 `project`，界面直接拿项目号当名字。修法：项目号与门禁记录不变，界面改用目录名（`renderer.tsx` 的 `projectName`），已打开项目同名时带上项目号区分；用在侧栏、标题、任务眉标、角色申请横幅、开终端按钮、移除对话框、通知卡片、流程页。真实 Electron 入口的端到端测试：修前版本 a3ae46cf2 在侧栏、同名区分、横幅、标题四项失败，修后 7 项通过；变异体“同名不带项目号”只在同名区分失败。agy 独立审查结论“可合并”，一条 P3（送审 diff 混有 T-202、T-204 的 renderer 改动）。主进程系统通知与 `a2a` 回执仍用项目号，未改。见 [RESULTS](../../evidence/2026-10-27-batch28/T-200/RESULTS.md)、[审查](../../evidence/2026-10-27-batch28/T-200/review-1.md)。
