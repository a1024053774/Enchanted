---
id: T-176
title: L03：会话状态显示不一致（主控空闲仍转圈等）
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

现象见报告 L03。目标：同一会话在侧栏、窗格头、窗格底栏、项目行显示同一状态、同一来源（与 T-146 同原则）：回合结束即空闲；“等待用户回答/等待主控回答”指向真正在等的一方；时间列写清是“启动于”还是“结束于”，刚结束的会话不显示“1 天”。

通用：先在真实 Electron 隔离实例复现并留红态，再修根因；真实 Claude 用 claude-haiku-5-5；不加重试掩盖未知；不用正则判断意图；agy 独立审查。

## Acceptance

- [ ] 真实 Electron：主控回合结束后各处同时显示空闲；worker 窗格头与底栏一致；主控等用户时项目行写等你回答。
- [ ] 红态截图对照。

## 不做

范围外的问题经问题上报，不顺手改。
