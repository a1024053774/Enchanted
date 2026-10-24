---
id: T-165
title: F01 残余：排队输入那一轮的 Stop 早于转录登记，worker 停在“运行中”
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

来源：执行主控在 T-157 合并后（main efcad2e70，与 T-157 候选 1ca1f3e08 的 workbench 代码完全相同）复跑 `workbench/tests/test_t157_stop_input_e2e.py`，2/2 失败于“worker 及门禁反馈回到空闲”；T-161 候选上的同一回归 1/1 失败。T-157 的 outside-05 中同一场景 2/2 通过，所以这是时序相关的缺陷，不是 T-161 引入的。属于 T-157（F01 blocker）已批准范围内的缺陷级残余，执行主控按 T-004 自建。

现场（`/private/tmp/t157-stop-input-63d2qaht`，state.sqlite3 的 orchestration_events）：原 Stop 交付通过（relay_processed ok）；用户输入后 `claude_prompt_queued`、`pane_waiting_native_queue`；随后 CLI 处理排队输入那一轮的 Stop 在 seq 120 到达，seq 121 记 `stop_not_matched`；seq 123～125 才凭原生转录登记该轮（`turn_submitted`、`turn_start_signal` origin native-transcript）。之后再无 Stop，worker 一直是“运行中/未知”。

目标：排队输入那一轮的 Stop 与转录登记的先后不应决定结果。Stop 先到时，要能在登记该轮后与之匹配（或在处理 Stop 时先读转录完成登记），worker 回到空闲；不放松门禁对 turn/attempt/版本的核对，不把无关 Stop 误配，不加重试循环或超时兜底来掩盖。

## Acceptance

- [ ] 红态：在当前 main 上用确定的时序（例如夹具让排队那一轮的 Stop 在转录写入前送达）稳定复现 `stop_not_matched` 且停在运行中。
- [ ] 绿态：同一时序下 worker 回到空闲，T-157 的正例、基线与坏实现、T-159/T-160/T-133 回归通过；`test_t157_stop_input_e2e.py` 连续多次通过。
- [ ] 反例：与该轮无关的 Stop 仍不匹配。

## 不做

范围外的问题经问题上报，不顺手改。
