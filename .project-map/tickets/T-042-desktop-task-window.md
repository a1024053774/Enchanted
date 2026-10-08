---
id: T-042
title: 合并任务窗口并在隔离桌面版中复验
type: build
status: open
blocked_by: [T-038, T-039]
claimed_by:
supersedes:
---

## What to build

T-039 交接后，主控把 fork 分支 `a2a-t038`（`ad13b72`）合并进 `a2a`（合并 T-037/T-039 的同一文件分段改动）。然后让隔离数据目录中的 Electron 桌面版能到达任务窗口：查明 T-038 记录的现象（导入弹窗点 Not now 不关闭；直达 `/a2a` 时 WebSocket 帧头异常与连接被拒绝；基线同样空白），区分环境、启动方式与上游缺陷。见 [T-038 交付记录](../../evidence/2026-10-07-synara-batch2/T-038/RESULTS.md) 与 round6。

## Acceptance

- [ ] 合并后的 `a2a` 上，typecheck、lint 通过；T-036/T-037 的 35 项与 T-038 的 membership 场景重跑通过。
- [ ] 隔离桌面版截图或录屏：一个项目下至少两个任务，其中一个任务含 worker 与 reviewer 两个会话，并显示门禁状态。
- [ ] 真实（非夹具）observer 状态与人工介入标记在界面上显示：受管 worker thread 中由人输入一条消息后，任务窗口出现对应标记。
- [ ] 外观由用户判断。

## Resolution
