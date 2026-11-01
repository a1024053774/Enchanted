STATUS: FAIL

FINDINGS:

- [P2] [workbench/src/panes.ts:1454](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1454) — `native.jsonl` 仍直接调用 `appendFileSync`，绕过 `traceFailed`。`launchInfo()`（938）、`processInfo()`（1354）及退出回调（1162）仍可到达这里，因此 PTY trace 失败后仍可能写另一份 trace；若是 `native.jsonl` 自身写失败，也不会触发停写，后续扫描会重复记录 `native_record`、重试同一行。统一规则尚未覆盖所有写入点。

- [P2] [workbench/tests/test_pane_trace_failure.ts:41](/Users/luckye/Documents/Code/a2a/workbench/tests/test_pane_trace_failure.ts:41)、[test_t212_trace_failure_e2e.py:159](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t212_trace_failure_e2e.py:159) — 当前只证明失败事件去重，不能证明停写。反例：每帧继续尝试 append，但仅首次调用 `recordFailure`，现有断言仍可通过，因为文件始终不可写。应补充恢复可写后继续输出、核对 trace 不增长的检查，并用这个反例验证。

- [P2] [workbench/src/panes.ts:342](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:342) — 关闭失败的原因在请求边界丢失。`AggregateError.errors` 包含两个错误，但消息只包含原始打开错误；[daemon.ts:1022](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:1022) 只序列化 `String(error)`。调用者只能知道“没有关掉”，无法知道关闭为何失败，妨碍处理残留终端。应把 `closeError` 一并放入可返回的消息或诊断字段。

EVIDENCE:

- 已读票面第 18–43 行、候选完整 diff、相关调用链、两份测试及变异 diff；候选与工作区相对 `03ba1cf54` 的 diff 逐字一致，审查结束时未变化。
- 关闭路径按 launch 查找 pane（592–597），再使用其 `HcTerminal.address` 杀终端（`hc.ts:159`）；未发现会选中其他终端的新路径。成功关闭后重新抛出原错误（343）。
- `REPORT.md:31–40` 的结果与证据一致：红态 resize 为 43 条、initial 为 5 条且终端存活；两份绿态均为 1 条；保留终端变异的三项关闭检查均失败。对应日志与 run.json 一致。
- `red-managed/results.json` 两项均为 `5 !== 1`；绿态两项 `failure=null`。`t104.json.status`、`t107.json.status` 均为 `PASS`。
- 项目终端在停写后仍处理 OSC（381–395）。受管回调提前返回延续了原先 append 失败时的处理顺序；未据此认定新增协议应答退化。未发现新增 fallback、重试或兼容分支；平行写入规则见第一条。

LIMITATIONS:

- 未重跑测试、启动后台或连接 hc／供应商；以上运行结论来自现存证据。
- 登录 trace、关闭失败、停写后的 OSC／协议／扫描没有专门运行证据。
- run.json 未记录完整候选代码版本，无法独立确认历史运行与当前候选的绑定。
- 项目地图 status 报告 `workbench/README.md` stale；只读审查未处理。