---
id: T-177
title: L04：侧栏堆积与启动默认选中已结束终端
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

现象见报告 L04。目标：已结束/已作废 attempt 的会话默认折叠为“历史 N 个”，可展开、可一键清理（只从列表隐藏或归档，不删证据，不改门禁记录）；已集成任务名下仍空闲的 worker 给出“回收”入口（走门禁 reclaim，不自动关）；应用启动时默认选中最近活跃的会话或空项目页，不选已结束终端。

通用：先在真实 Electron 隔离实例复现并留红态，再修根因；真实 Claude 用 claude-haiku-5-5；不加重试掩盖未知；不用正则判断意图；agy 独立审查。

## Acceptance

- [ ] 真实 Electron：2 张票多次重派后侧栏只显示当前 attempt 与“历史 N”；清理后重启仍保持；回收入口经门禁。
- [ ] 启动默认选中合理。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-25，PASS。记录见 [RESULTS.md](../../evidence/2026-10-25-batch25/T-177/RESULTS.md)。侧栏把已结束的会话和被新 attempt 取代的会话折进每个任务下的“历史 N 个”，默认收起；“清理”把已结束的会话从列表拿掉（追加 `sidebar_hidden` 事件，记录与门禁事件不删，运行中的会话拒绝清理）；已集成任务仍空闲的当前 worker 显示“回收”，经门禁 `reclaim`；没有指定启动目标时，打开最近活跃、未结束的会话，不再选中已退出的家目录终端。真实 Electron 红态 13 项失败，修后两次 PASS 18/18，两个变异被拒，三项回归 PASS；agy 审查 PASS（一项 P3 观察：纯终端只打字不更新 `active_at`，已记录）。
