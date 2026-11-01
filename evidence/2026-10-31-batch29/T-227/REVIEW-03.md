STATUS: FAIL

FINDINGS:

- [P2] [panes.ts:1149](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1149) — **trace 与事件库同时不可写时，仍会逐帧报告失败。** 静态反例：Codex 已有未扫描的 rollout，PTY trace 写失败后仍进入 `scan`；1455 行的 `store.event("native_record")` 写库失败，1150 行将其记为 `native_read_failed`，1267–1271 行再次触发 `event_write_failed`。扫描偏移尚未推进，下一帧重复同一路径，重新造成逐帧报警与日志增长。现有 [测试第78行](/Users/luckye/Documents/Code/a2a/workbench/tests/test_pane_trace_failure.ts:78) 只在事件库可写时创建 rollout，因此第87行“观察者只调用一次”没有覆盖这个组合。

- [P2] [panes.ts:1306](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1306) — **继续调用协议处理并不能继续应答，且会制造重复失败事件。** trace 失败后收到 `ESC[6n` 等查询，`terminalProtocol` 经 `serializeWrite` 应答，但 [1523行](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1523) 因 `pane.failed` 拒绝；1309行随后记录 `terminal_protocol_failed`，覆盖原 trace 错误。每个查询都会重复此过程。第三轮取消提前返回后，这条路径在 trace 持续不可写时也能到达；[REPORT.md:80](/Users/luckye/Documents/Code/a2a-worktrees/T-227-evidence/REPORT.md:80)“终端协议照常应答”的结论不成立。当前测试没有发送协议查询。

EVIDENCE:

- 已读票面、REVIEW-01、REVIEW-02、REPORT、完整候选及相关调用链。候选与工作区三个文件相对 `03ba1cf54`、HEAD 的 diff 逐字一致；审查结束时未变化。
- 前两轮原意见的直接修改均已落地：native trace 经统一入口（`panes.ts:1456`）；恢复可写后的停写检查（测试第75–81行）；关闭错误消息包含两个原因（`panes.ts:342`）；受管回调不再因 trace 失败提前返回（1148–1153行）。
- 关闭按 launch 找对应 pane（592–597行），再按该终端地址调用 kill（`hc.ts:159`）；成功后重新抛原错误，关闭失败合并两个错误。未发现新增关错终端路径。
- 第三轮日志与结果文件一致：`r3-red-managed/results.json` 的 trace 场景为 `0 !== 2`；绿态三场景均 `failure=null`；变异为 `75 !== 0`。
- `r3-green-resize/run.json`：失败事件1条、trace保持982字节、tick为2→40；`r3-green-initial/run.json`：终端列表为空、shell已退出、关闭事件检查通过。对应日志一致。`r3-t104.json.status`、`r3-t107.json.status` 均为 PASS。
- 窗格 PTY/native trace、paint及登录脱敏写入均检查停写开关；未发现新增 fallback、兼容分支或平行 API。上述问题来自停写之后继续执行的失败路径。

LIMITATIONS:

- 两条新意见来自静态调用链与内存推演；未运行测试、启动服务或连接 hc／供应商。
- 未执行项目地图 status；未注入关闭失败、登录 trace 失败或 OSC 7501 专门场景。
- 历史运行缺少完整候选版本绑定；T104/T107 的 `revision=null`。REPORT 第92行的运行顺序声明无法由运行记录独立验证。