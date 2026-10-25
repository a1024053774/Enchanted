---
id: T-174
title: L01：CLI 卡在系统授权弹窗时窗格空白无提示
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

现象见报告 L01。目标：终端里前台 CLI 启动后若干秒没有任何输出时，窗格显示可操作的提示（例如“CLI 还没有输出，可能在等 macOS 的权限弹窗，弹窗可能在其他窗口后面”），有输出后自动消失；只依据“无输出时长”这一机械事实，不猜原因、不替用户点。若能可靠得知应用自身的隐私授权状态，可补一条指向系统设置的说明（不自动改设置）。

通用：先在真实 Electron 隔离实例复现并留红态，再修根因；真实 Claude 用 claude-haiku-5-5；不加重试掩盖未知；不用正则判断意图；agy 独立审查。

## Acceptance

- [x] 复现：让 CLI 阻塞在无输出状态（可用不输出的替身），修前窗格空白无提示，修后出现提示；有输出后提示消失。
- [x] 正常启动的 CLI 不出现提示。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-25，PASS。记录见 [RESULTS.md](../../evidence/2026-10-25-batch25/T-174/RESULTS.md)。项目终端的前台程序在最后一次输出之后启动、且 6 秒没有输出时，窗格顶部提示它可能在等 macOS 权限弹窗；有输出即消失。真实 Electron 端到端：修前红、修后 6/6、变异被拒；agy 审查 PASS。没用真实 Claude 复现隐私弹窗（需要撤销系统授权）。
