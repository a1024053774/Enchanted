---
id: T-133
title: 界面显示用户输入记录与人工介入
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

来源：用户 2026-10-22 逐字：“107 吧多 worker 做出来，早期的调研票关掉，然后还缺的都做”。 切换条件里的“用户输入记录”：门禁的 `user_inputs` 表已记下用户在窗格里亲手打的字、面板答复等（T-050 语义），受管 worker 窗格里的输入记为人工介入；界面只有一个标签，看不到记录。

- 按项目、任务、会话列出用户输入：时间、形态（键入、面板答复、审批等，按库里已有的字段）、目标会话与角色、文本；落在受管 worker 窗格里的标“人工介入”。
- 只读，不改库；派发与注入的文字不出现在这里（记录器已跳过已登记的注入）。

## Acceptance

- [ ] 真实 Electron：夹具里用户在主控终端和受管 worker 窗格各打一段字、在面板答复一条；视图列出三条，worker 那条标人工介入，内容与库读回一致；后台注入的派发文字不出现。修前没有这个视图。
- [ ] 截图与复现命令入证据。

## 不做

不做含义标注与抽取（MAP“Not yet specified”）；不改记录器。
