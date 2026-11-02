---
id: T-237
title: 复盘进程已退出、后台重启后，复盘列表里那一行仍显示“进行中”
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

2026-11-02 Computer Use 实测（`evidence/2026-11-02-batch30/cu-bugsweep/BUGS-r2.md`，截图 `shots/r2-reflect-status.png`）：第一轮 06:02 启动的手动复盘，在目录信任框里选了退出，CLI 随后结束；第一轮结束时隔离后台也被停掉。第二轮用同一状态目录 `/private/tmp/a2a-cu/state` 重新启动，Reflect 页里这一行仍是“进行中”，报告为“—”。库里只有 `retrospective_started`，没有任何结束事件。

期望：复盘的 CLI 退出、或后台重启后找不到它的终端时，这一行显示已结束（没有产出就写没有报告）或“未知”，不能一直显示“进行中”。要查清复盘的结束是怎么判定的、后台重启时为什么没有核对。

## Acceptance

- [ ] 先写下可能出错的方式。
- [ ] 修前红态：启动复盘、让 CLI 退出且不写报告、重启后台，列表仍显示“进行中”。
- [ ] 修后：同一场景显示已结束或未知；正常写出报告的复盘照旧导入。
- [ ] 独立审查（GPT 只读，新开干净会话）无未处理的阻塞意见。

## Resolution

（未开始）
