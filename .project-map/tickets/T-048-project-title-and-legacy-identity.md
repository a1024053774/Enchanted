---
id: T-048
title: 门禁自动建项目的标题与启动器旧记录兼容代码
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
---

## What to build

`apps/server/src/a2a/service.ts:101` 在门禁自动建项目时把标题写死为 "a2a pagination"，侧栏出现多个同名项目。改为使用 create 请求中的项目信息（例如 project id 或新增的项目标题字段）。另：T-046 为识别旧格式工作台进程记录加了遍历 locale 的兼容分支（`a2a/scripts/workbench_runtime.py`）；正式工作台以 T-046 之后的代码重启并写入新格式记录后删除该分支，保留对其他进程记录的拒绝。

主控补充（2026-10-09）：工作台以 T-046 代码重启后，记录仍是中文格式——写记录的是 `a2a/scripts/launch-workbench.mjs:28`，它用继承的 locale 调 `ps`，T-046 只改了读取一侧（T-046 的 oracle 只覆盖读取路径）。本 ticket 一并修写入侧：写入与读取用同一 locale 无关的格式。兼容分支的删除顺序由主控在合并时处理：先用旧代码停止正式工作台，再合并，再启动写出新格式记录。

## Acceptance

- [ ] 门禁 create 新建的项目在侧栏显示有意义的名称；已有项目不受影响。
- [ ] `launch-workbench.mjs` 写入的身份在任何调用者 locale 下与 `workbench_runtime.py` 读取的格式一致（用临时数据目录与受控子进程验证，不启动正式工作台）；工作台重启后新记录为新格式，删除兼容分支后 `acceptance/workbench_identity_oracle.py` 中新格式与拒绝用例仍通过（旧格式用例相应调整并说明）。

## Resolution

**PASS（worker 实现与隔离验收）；待主控关闭。** fork 提交 `42376b018616d56a2f0774913bf85c7a9cf82940`：新项目标题直接取 create 请求中的 project id，已有项目不改名；身份写入与读取统一 `LC_ALL=C`，删除 locale 遍历兼容分支。项目标题取得父版本红态并通过真实门禁/原生 SQLite 侧栏快照复验；相关服务测试 11/11，实际 launcher 写入与 status 读取 oracle 红态 50/61、绿态 61/61。

报告、原始输出、精确命令、完整测试夹具归档与 oracle 快照/patch 见 [T-048 RESULTS](../../evidence/2026-10-09-batch7/T-048/RESULTS.md)。按任务书提交范围，`acceptance/workbench_identity_oracle.py` 的已验证源文件改动留给主控单独收录。正式工作台未停止或重启；主控仍须用旧代码停止、更新后启动并核对新记录，取得正式验收/集成证据后关闭 ticket。验收框保持未勾选，避免把 worker 隔离结果写成正式迁移完成。
