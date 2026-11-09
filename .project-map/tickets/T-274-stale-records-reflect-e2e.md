---
id: T-274
title: 修复 T-133/T-137/T-162 三条过期的端到端测试
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## 来由

T-273 复验时发现（执行主控自建缺陷票）：`test_t137_reflect_e2e.py`、`test_t133_t134_records_metrics_e2e.py` 在 HEAD `3b12f3432` 上就报 `plan: StopIteration`（脚本模型的计划先于产品的模型请求用尽）；`test_t162_role_records_metrics_e2e.py` 在 HEAD 上报“超时：记录页读取结束”，疑为 T-262 给记录页加了常驻 `role="status"` 计数，测试仍等它消失。证据：`evidence/2026-11-09-batch35/T-273/stale-tests.json`。

## 要做的

查清各自的失败原因，按当前需求改测试（不改产品行为去迁就测试），让三条测试重新能作为记录页、指标页、Reflect 页的回归证据。

## Acceptance

- [ ] 三条测试在当前 HEAD 上通过；各自的变异仍判红。
- [ ] 用它们复验 T-273 的“不回归”一条。
