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

- [x] 合并后的 `a2a` 上，typecheck、lint 通过；T-036/T-037 的 35 项与 T-038 的 membership 场景重跑通过。
- [x] 隔离桌面版截图或录屏：一个项目下至少两个任务，其中一个任务含 worker 与 reviewer 两个会话，并显示门禁状态。
- [ ] 真实（非夹具）observer 状态与人工介入标记在界面上显示：受管 worker thread 中由人输入一条消息后，任务窗口出现对应标记。
- [ ] 外观由用户判断。

## Resolution

进行中（主控记录，2026-10-08）：第 2 项 PASS，用户在 Codex GUI（Computer Use）中完成，证据 [T-042/desktop](../../evidence/2026-10-07-synara-batch2/T-042/desktop/RESULTS.md)，提交 `73def97`；截图 `04-task-window.jpg` 显示一个项目下两个任务、"分页交付"内并列 worker 与 reviewer 会话及门禁状态 `ready`，主控已查看。经正常 UI 关闭导入公告后点击"任务窗口"链接到达；Electron 使用 hash history，正确地址为 `/#/a2a`，T-038 round6 直接打开的 `/a2a` 不是有效入口，其 WebSocket 帧头异常的根因仍未确定。第 1、3、4 项待 T-039 交接后合并再做。

主控记录（2026-10-08）：合并提交 `3566ef4`，见 [合并记录](../../evidence/2026-10-07-synara-batch2/T-042/merge/MERGE.md)。第 1 项 PASS：[复验](../../evidence/2026-10-07-synara-batch2/T-042/verify/recovery-01/RESULTS.md) 中 lint、typecheck 8/8、标准桌面构建、18 项与 17 项、membership HTTP 场景（含跨项目与 OPTIONS）全部通过。首轮复验时执行 agent 为绕开旧 server bundle，把 `apps/server/dist` 换成指向外置盘的链接并在其中放了指回 node_modules 的链接，tsdown 清理输出时沿链接删除了 6,186 个受控文件和依赖；agent 已按删除清单 `git restore`、按锁文件重装依赖，主控核对 fork HEAD 仍为 `3566ef4`、仅原有 `.grok/` 未跟踪、`synara-t038` 未受影响。事故记录见 [首轮报告](../../evidence/2026-10-07-synara-batch2/T-042/verify/initial-RESULTS.md)。第 3 项 INCOMPLETE：真实 Electron 显示 observer `healthy`，但隔离环境 provider 关闭，受管 worker 中的人工消息被拦为草稿，未产生 human_intervention 事件；需要用户决定是否在隔离环境启用 provider 并允许一次真实模型调用。

