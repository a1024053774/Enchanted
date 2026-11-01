STATUS: FAIL

FINDINGS:

- [P2] [workbench/src/panes.ts:1149](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1149) — 停写开关同时永久停止后续帧的状态观察。反例：agy/opencode 的 trace 首次写失败，恢复可写后再发送 OSC 7501 blocked/done；`appendTrace` 因 `traceFailed` 返回 false，回调直接退出，1152 行的 `reportedTurns` 不再执行，导致 `cliTurn`、`native_turn_report`、`native_wait_reported` 丢失。基线在文件恢复可写后会继续处理这些报告。应把停止 trace 写入与继续消费状态信号分开，同时保留失败窗格的派发限制。

EVIDENCE:

- 候选 patch 与工作区三个文件相对 `03ba1cf54` 的 diff 逐字一致；审查结束时未变化。
- REVIEW-01 三条原意见均已修正：`panes.ts:1456` 将 native trace 接入统一规则；`test_pane_trace_failure.ts:70` 和 `test_t212_trace_failure_e2e.py:148` 检查恢复可写后仍停写；`panes.ts:342` 的错误消息包含原错误及关闭错误，能经过 `daemon.ts:1022` 返回。
- 关闭按 launch 查找对应 pane（`panes.ts:592`），使用该终端地址关闭（`hc.ts:159`）；成功后重新抛原错误（`panes.ts:343`）。关闭、进程核对失败会向上传播，未发现新增吞异常、fallback、重试或兼容路径。
- 新发现的调用链：`panes.ts:1260` → `1149` 提前返回 → 跳过 `1152`；实际状态记录位于 `2185–2215`。项目终端在 `381–395` 先解析 OSC 再处理 trace，没有同样的问题。
- native 测试在 `test_pane_trace_failure.ts:53–63` 反复查询同一批记录，并显式调用 `launchInfo` 触发扫描；没有检查停写后新到达的状态信号，因此未覆盖上述退化。
- REPORT 的关键结果与所链 JSON、日志一致：第二轮 native 红态 `6 !== 2`；隔离变异 `75 !== 0`；resize 变异 `trace_after_restore` 为 1107→1814 字节，停写检查为 false；绿态为 982→982 字节、tick 1→40。initial 绿态终端列表为空、shell 已退出、关闭事件检查通过；第二轮 T104/T107 的 `status` 均为 PASS。

LIMITATIONS:

- 未重跑测试、启动后台或连接 hc／供应商；上述新问题来自静态调用链与内存推演。
- 登录 trace、关闭失败没有专门运行证据。
- 历史运行未完整绑定当前候选版本；第二轮 T104/T107 的 `revision` 为 null，无法独立确认运行时源码与本候选完全一致。