---
id: T-045
title: 工作台"用量与限额"显示失败
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
---

## What to build

用户在正式工作台（`~/Library/Application Support/a2a-workbench`）的 Settings → Usage & limits 看到 Codex、Claude、Cursor 均为"Unavailable / Could not reach the … usage endpoint"，而聊天正常。主控核对：本机直接访问 `chatgpt.com/backend-api/wham/usage` 2 秒内返回（401，网络可达）；错误来自 `apps/server/src/providerUsage/providers/codex.ts` 的异常分支，但工作台 `server.log` 没有该警告的细节。查明根因并修复，使 Codex 与 Claude 用量正常显示。

## Acceptance

- [ ] 根因有证据（日志、复现命令或源码路径），区分工作台启动环境、凭据读取、网络与上游缺陷。
- [ ] 修复后工作台中 Codex、Claude 的用量显示正常（截图），或说明某个 provider 因条款或认证方式本就不提供用量。
- [ ] 诊断与验证期间不兑换 refresh token、不改写用户 `~/.codex`、`~/.claude` 凭据；修改上游文件时列清单。

## Resolution
