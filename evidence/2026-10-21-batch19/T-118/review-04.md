codex
结论：**NO_GO**。审查对象为 `t118-04.diff`；结束时 13 个受审文件仍与候选一致。全程未修改文件、未提交。

1. **P2：关闭超过 10 秒才完成时，崩溃重载仍留下失效窗格。**  
   [main.ts:616](/Users/luckye/Documents/Code/a2a/workbench/app/main.ts:616) 等待超时后直接重载，此时 selection 仍包含正在关闭的 key。随后关闭完成，在 [main.ts:398](/Users/luckye/Documents/Code/a2a/workbench/app/main.ts:398) 删除 key；关闭回执属于旧 renderer，新界面的[定时刷新:471](/Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx:471) 只更新侧栏，不能同步窗格集合。  
   实际关闭与恢复 handler 的内存时序探针确认：**关闭耗时 5 秒时重载集合为 `[]`；耗时 12 秒时，第 10 秒重载集合为 `["P"]`，关闭完成后实际集合为 `[]`。** 该场景可达：后台请求期限为 [120 秒](/Users/luckye/Documents/Code/a2a/workbench/src/transport.ts:28)。  
   应保留 10 秒上限，并让超时后完成的关闭同步到新 renderer。真实入口回归应覆盖“关闭延迟超过 10 秒期间崩溃”。

第三轮两条核对：

- **首次绑定 launch 重新隐藏：代码已修。** [renderer.tsx:234](/Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx:234) 在绑定前设置恢复状态。实际读取循环与生产 writer 的局部探针中，51 个写入片段全部处于隐藏状态；移除该行后，51 个全部处于显示状态。此探针模拟终端边界，不证明真实绘制时序。
- **崩溃重载等待 closing：部分解决。** 10 秒内完成的关闭已正确等待；超时分支仍有上述 P2。

未发现其他可确认的 P1/P2 缺陷。

已核对测试版 `ui-test-09` 包含本轮两处修复；[GUI 证据](/Users/luckye/Documents/Code/a2a/evidence/2026-10-21-batch19/T-118/ui-restore-green-09.json)支持约 2 MB 恢复、最终画面及单次 `Page.crash` 自恢复。但以下边界仍**只有代码检查或局部探针**：无 launch 后绑定、小积压重连、空 trace、读取错误、切换／创建／关闭期间崩溃、关闭超时、关窗抑制、10 秒内再次崩溃、外部 SIGTERM、恢复版本的 GUI 展示及正常登录最终审计。本轮未重跑会写入文件的端到端测试。
