---
id: T-176
title: L03：会话状态显示不一致（主控空闲仍转圈等）
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

来源：findings/2026-10-25-lcu-real-use.md；用户 2026-10-24 逐字：“然后你再用 lcu 测试一下软件看看能不能发现其他问题”。

现象见报告 L03。目标：同一会话在侧栏、窗格头、窗格底栏、项目行显示同一状态、同一来源（与 T-146 同原则）：回合结束即空闲；“等待用户回答/等待主控回答”指向真正在等的一方；时间列写清是“启动于”还是“结束于”，刚结束的会话不显示“1 天”。

通用：先在真实 Electron 隔离实例复现并留红态，再修根因；真实 Claude 用 claude-haiku-5-5；不加重试掩盖未知；不用正则判断意图；agy 独立审查。

## Acceptance

- [x] 真实 Electron：主控回合结束后各处同时显示空闲；worker 窗格头与底栏一致；主控等用户时项目行写等你回答。
- [x] 红态截图对照。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-25，PASS。记录见 [RESULTS.md](../../evidence/2026-10-25-batch25/T-176/RESULTS.md)。窗格头改为显示侧栏同一行的状态，删掉底栏的“执行：…”；已结束的行显示“结束 N 分”；没有主控在回合中、却有 worker 等主控答复时，项目行显示“等你处理”。真实 Electron 端到端：修前本票四项检查全红、修后 18 项 PASS，第一轮候选上复现了审查指出的两个缺陷；T-157 回归 PASS。agy 第一轮 INCOMPLETE（P1 家目录终端窗格头“未知”等三条，均已修），第二轮 PASS。未解：实测那一轮主控终端的钩子事件一条都没送到后台，各种组合都没能复现，已上报构思主控。
