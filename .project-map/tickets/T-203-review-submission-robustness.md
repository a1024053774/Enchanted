---
id: T-203
title: 审查员手写嵌套 JSON 回包易错，审查卡死要人工重开
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

来源：真实用户式试用第 2 轮（[RESULTS](../../evidence/2026-10-27-batch28/UAT-02/RESULTS.md) 发现 1）。同一次交付的两次审查，审查员（Claude Code `claude-sonnet-5-5`）最后一条回复都是深层嵌套的 JSON，末尾都少一个 `}`，门禁按 `review_json` 拒收，任务暂停；问题页两张卡都显示“问题 1”。重派后的第三次审查才通过。

门禁拒收格式不对的回包是对的，不放宽。要定的是审查员怎么交回包才不靠模型数括号：例如经 `a2a` 命令或 T-194 的 MCP 工具按字段提交，由工具拼成协议对象；或其他做法。先定方案再做；同时查清两张卡为何同号。

## Acceptance

- [ ] 方案定下并写进本票。
- [ ] 修前版本经真实入口：审查员的回包少一个括号时审查卡死；修后同样的审查意见能被门禁收下，格式真不对时仍拒收并说明。
- [ ] 同一 attempt 的多张问题卡编号不重复。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

放宽门禁对回包内容的检查；改审查判断本身。

## Resolution
