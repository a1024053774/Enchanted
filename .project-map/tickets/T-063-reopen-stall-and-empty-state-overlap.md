---
id: T-063
title: 修复重开已有 profile 停在启动 logo、会话空态文字与 logo 重叠
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

T-062 的 worker 发现两处范围外的界面问题，用户要求都做（逐字："两条范围外的界面问题都做"）：

1. 隔离 dev UI 用已有 profile 重开后停在启动 logo，约 11 秒无内容、无报错（`evidence/2026-10-09-batch11/T-062/` 的 `resume01.json`、`resume01-5.png`；上报 `20261009T223641Z-worker:s11-t062-issue-001`）。查明是真实启动缺陷还是隔离 dev 环境才有，是真实缺陷就修。
2. 会话空态里 "Import your Claude Code and Codex projects" 的文字与 Synara logo 重叠，全宽与窄窗口都可见（`green03-initial.png`、`green03-narrow.png`；上报 `20261009T223804Z-worker:s11-t062-issue-001`）。

## Acceptance

- [ ] 问题 1：复现并查明来源（产品还是 dev 环境），保存证据与重放命令。是产品缺陷就先红后绿：同一 profile 重开后在合理时限内出现主界面；是环境问题就说明依据，并让重开路径在验收环境里能走通。都不能把"诊断命令退出 0"当作重开通过。
- [ ] 问题 2：先红后绿的界面用例；1600×1050 与 1280×900 两种视口下文字与 logo 不重叠，截图作证，外观由用户判断。
- [ ] 既有套件、typecheck、lint 通过；对上游文件的改动列清单。
- [ ] 不碰正式工作台数据目录 `~/Library/Application Support/a2a-workbench`；只用隔离 profile。

## 说明

- 失败方式清单（处理方式写进 RESULTS）：重开时旧 profile 的已看标记或缓存状态损坏；服务端未就绪时前端无重试；窗口尺寸在启动后改变；空态文案换成其他语言后变长。
- 与 [T-062](T-062-panel-overlay-remnant.md) 可能同改 `Sidebar.tsx` 附近的界面，同一文件同一时间只能有一个写入者，由执行主控串行安排。
- 授权来源：用户 2026-10-09 说"两条范围外的界面问题都做"；`ready_by: ideation`，`ready_rev: 1`。

## Resolution
