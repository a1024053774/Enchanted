---
id: T-165
title: F01 残余：排队输入那一轮的 Stop 早于转录登记，worker 停在“运行中”
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

来源：执行主控在 T-157 合并后（main efcad2e70，与 T-157 候选 1ca1f3e08 的 workbench 代码完全相同）复跑 `workbench/tests/test_t157_stop_input_e2e.py`，2/2 失败于“worker 及门禁反馈回到空闲”；T-161 候选上的同一回归 1/1 失败。T-157 的 outside-05 中同一场景 2/2 通过，所以这是时序相关的缺陷，不是 T-161 引入的。属于 T-157（F01 blocker）已批准范围内的缺陷级残余，执行主控按 T-004 自建。

现场（`/private/tmp/t157-stop-input-63d2qaht`，state.sqlite3 的 orchestration_events）：原 Stop 交付通过（relay_processed ok）；用户输入后 `claude_prompt_queued`、`pane_waiting_native_queue`；随后 CLI 处理排队输入那一轮的 Stop 在 seq 120 到达，seq 121 记 `stop_not_matched`；seq 123～125 才凭原生转录登记该轮（`turn_submitted`、`turn_start_signal` origin native-transcript）。之后再无 Stop，worker 一直是“运行中/未知”。

目标：排队输入那一轮的 Stop 与转录登记的先后不应决定结果。Stop 先到时，要能在登记该轮后与之匹配（或在处理 Stop 时先读转录完成登记），worker 回到空闲；不放松门禁对 turn/attempt/版本的核对，不把无关 Stop 误配，不加重试循环或超时兜底来掩盖。

## Acceptance

- [x] 红态：在当前 main 上用确定的时序（例如夹具让排队那一轮的 Stop 在转录写入前送达）稳定复现 `stop_not_matched` 且停在运行中。
- [x] 绿态：同一时序下 worker 回到空闲，T-157 的正例、基线与坏实现、T-159/T-160/T-133 回归通过；`test_t157_stop_input_e2e.py` 连续多次通过。
- [x] 反例：与该轮无关的 Stop 仍不匹配。

## 不做

范围外的问题经问题上报，不顺手改。

## Resolution

2026-10-24 关闭，PASS。根因：排队输入那一轮的 Stop 早于后台凭原生转录登记该轮到达时，`claudeStop` 直接记 `stop_not_matched` 丢弃，登记后再无 Stop。修复在 `workbench/src/panes.ts`：只暂存同一转录、晚于排队输入、非子代理、`stop_hook_active=false`、prompt_id 未用过且无 active 的根 Stop；登记该轮后按同一 `claudeStop` 核对（信任、转交、after_transfer 比对）完成，失败经 `recordFailure` 记录；promptId 不符的暂存 Stop 记不匹配；`current` 判定另加 `!stopped && !nativeEnded`。门禁核对未放松。README 同步（5c2e0df20）。
沙箱外（0 个真实模型回合）：outside-02 在修前 main 确定时序红态 2/2；outside-03 同一时序绿态 3/3、T-157 stop-input 3/3、无关 Stop 反例 PASS；修前基线与丢弃早到 Stop 的坏实现只败在三项空闲/完成断言；T-157 基线、坏调用方与三个变异只在预期断言失败；stale recover/expired 与 T-159/T-160/T-133 回归 PASS。03 汇总脚本崩溃（两种 checks 格式），由只读汇总 SUMMARIZE-03 补出 RESULT，未重跑。独立审查 agy PASS（两条 P3 观察，无需改动）。合并 25ff4ff19。整批回归 46/46 见 `evidence/2026-10-23-batch24/merge-wave/README.md`。证据 `evidence/2026-10-23-batch24/T-165/RESULTS.md`。
