---
id: T-178
title: L05：流程页显示别的项目的任务、标题重复
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

来源：findings/2026-10-25-lcu-real-use.md；用户 2026-10-24 逐字：“然后你再用 lcu 测试一下软件看看能不能发现其他问题”。

现象见报告 L05。目标：项目视图下的流程页只显示该项目的任务（或当前项目置顶并展开，其他项目明确分组折叠）；任务标题不重复显示“T-1 · T-1”。

通用：先在真实 Electron 隔离实例复现并留红态，再修根因；真实 Claude 用 claude-haiku-5-5；不加重试掩盖未知；不用正则判断意图；agy 独立审查。

## Acceptance

- [ ] 真实 Electron：在 demo 项目下打开流程页，置顶是本项目任务；标题不重复。

## 不做

范围外的问题经问题上报，不顺手改。
