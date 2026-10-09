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

## Acceptance

- [ ] 门禁 create 新建的项目在侧栏显示有意义的名称；已有项目不受影响。
- [ ] 工作台重启后新记录为新格式，删除兼容分支后 `acceptance/workbench_identity_oracle.py` 中新格式与拒绝用例仍通过（旧格式用例相应调整并说明）。

## Resolution
