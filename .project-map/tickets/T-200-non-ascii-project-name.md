---
id: T-200
title: 中文等非 ASCII 目录名的项目在界面上显示为 project
type: build
status: open
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

- [ ] 修前版本经真实入口：打开名为中文的 Git 目录，界面显示 `project`；修后显示目录名。
- [ ] 两个中文名目录同时打开时，界面能区分；项目号与门禁记录不变。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

改项目号的生成规则；已有项目的迁移。

## Resolution
