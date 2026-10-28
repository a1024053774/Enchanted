---
id: T-205
title: 门禁拒绝只显示代码，用户看不懂下一步
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

来源：真实用户式试用第 2 轮（[RESULTS](../../evidence/2026-10-27-batch28/UAT-02/RESULTS.md) 发现 2、3）。时间线与回执只写 `门禁拒绝 未通过 dispatch：oracle_not_found`、`交付：门禁没有受理（stale_turn）`。`stale_turn` 在这里的意思是已交付的 attempt 只能在“交付被打回”的修复流程里再交，要补改就改卡、回收、重派；用户和主控都没看出来，主控还建议了不管用的做法。

为常见拒绝码给出一句人话原因和下一步（界面与 `a2a` 回执同一份文案），代码照旧保留。先列出要覆盖的码。

## Acceptance

- [ ] 列出要覆盖的拒绝码。
- [ ] 修前版本经真实入口：`oracle_not_found`、`stale_turn` 只显示代码；修后显示原因与下一步，代码仍在。
- [ ] 主控经 `a2a` 或 MCP 拿到的拒绝回执带同样的说明。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

改门禁的拒绝条件。

## Resolution
