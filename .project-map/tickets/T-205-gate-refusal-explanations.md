---
id: T-205
title: 门禁拒绝只显示代码，用户看不懂下一步
type: build
status: closed
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

- [x] 列出要覆盖的拒绝码。
- [x] 修前版本经真实入口：`oracle_not_found`、`stale_turn` 只显示代码；修后显示原因与下一步，代码仍在。
- [x] 主控经 `a2a` 或 MCP 拿到的拒绝回执带同样的说明。

通用：先在真实入口留红态再修根因；不写 ~/.claude、~/.codex 等全局配置；独立审查。

## 不做

改门禁的拒绝条件。

## Resolution

2026-10-27 PASS。覆盖 26 个拒绝码（清单与没收的码见 RESULTS）。根因：门禁拒绝回执只有代码，界面时间线与 worker 回执也只照抄代码。修法：`gates/refusals.ts` 一张码→原因/下一步的表；后台套接字回执加 `explanation`（`a2a`、MCP 原样打印同一份回执），任务页时间线与 worker 回执摘要接同一份文案；`error`、`details` 与拒绝条件不变。真实入口端到端测试（真实 `a2a call dispatch` 得 `oracle_not_found`，真实 Claude Code worker 补交得 `stale_turn`）：修前版本 a3ae46cf2 六项失败，修后九项通过，三个变异体各在对应检查失败。MCP 未单独实测（与 `a2a` 读同一回执，静态核对）。agy 独立审查结论“可合并”，一条 P3 观察。见 [RESULTS](../../evidence/2026-10-27-batch28/T-205/RESULTS.md)、[审查](../../evidence/2026-10-27-batch28/T-205/review-2.md)。
