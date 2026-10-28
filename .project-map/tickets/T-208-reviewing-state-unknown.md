---
id: T-208
title: 任务页底部在审查中、返工中显示“门禁 未知”
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

来源：真实用户式试用第 3 轮 3b（[RESULTS](../../evidence/2026-10-27-batch28/UAT-03/RESULTS.md) 发现 3）。审查员在跑时，任务标签和门禁记录都是 `reviewing`，任务页底部却写“门禁 未知”，用户以为门禁出了问题。

根因：界面的状态名表 `gateStateNames`（`workbench/src/gateReceipts.ts`）缺门禁实际会写的 `reviewing` 与 `rework` 两个任务状态，底部（`renderer.tsx` 的 `gate-label`）查不到就显示“未知”，门禁记录标题则直接显示英文代码。

## Acceptance

- [x] 修前版本经真实入口：任务进入审查后，底部显示“未知”。
- [x] 修后审查中、返工中都显示中文状态名；门禁会写入的每个任务状态在表里都有名字（由测试从门禁代码里列出状态逐个核对，不手抄）。

通用：先在真实入口留红态再修根因；独立审查。

## 不做

改门禁状态本身。

## Resolution

2026-10-28 PASS。`gateStateNames` 补 `reviewing: '审查中'`、`rework: '返工中'`。真实入口测试 `workbench/tests/test_t208_gate_state_names_e2e.py`：修前底部显示“未知”（`red-1.json`），修后“审查中”；从门禁源码提取的 15 个任务状态都有名字；两个变异体各在缺名的状态上失败。agy 审查“可合并”，P2 已改。证据见 [RESULTS](../../evidence/2026-10-27-batch28/T-208/RESULTS.md)。
