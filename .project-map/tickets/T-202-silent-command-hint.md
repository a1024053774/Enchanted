---
id: T-202
title: 安静的命令也被提示“可能在等 macOS 权限弹窗”
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by:
ready_rev:
---

## What to build

来源：真实用户式试用第 1 轮（[RESULTS](../../evidence/2026-10-27-batch28/UAT-01/RESULTS.md) 发现 4）。项目终端里跑 `sleep 300`，几秒后出现“sleep 启动后还没有任何输出。它可能在等 macOS 的权限弹窗……请移开其他窗口找一找”。

同一提示在 Claude 真被“文稿”授权弹窗挡住时说对了（发现 1 的归因），所以不删提示；改文案或触发条件，让本来就不输出的命令不被说成可能卡在权限上。具体怎么改先定再做。

## Acceptance

- [ ] 修前版本经真实入口：`sleep` 安静数秒后出现权限弹窗提示；修后不再把它说成可能在等权限，或文案明确“如果它应当有输出”。
- [ ] CLI 真被系统授权弹窗挡住时（可用新打包的 Enchanted Test 复现），提示仍出现。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

检测系统弹窗本身。

## Resolution
