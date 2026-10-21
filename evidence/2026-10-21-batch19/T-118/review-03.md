codex
结论：**NO_GO**。审查对象为 `t118-03.diff`，结束时 13 个受审文件仍与该候选一致。全程未修改文件、未提交。

发现按严重程度排列：

1. **P2：无 launch 的占位窗格稍后绑定 launch，仍会显示补读过程。**  
   [renderer.tsx:245](/Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx:245) 在无 launch 时解除隐藏；随后 [renderer.tsx:233](/Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx:233) 首次绑定 launch，却没有重新隐藏。  
   场景：打开尚无执行者的任务窗格，后台稍后启动执行者并积累输出。同一个 `read()` 循环会直接显示历史重绘。使用实际读取循环、生产 writer 和实际 xterm 解析器的只读探针，**3,846 字节产生了 179 个未隐藏的中间画面**。应在首次绑定 launch 时重新进入恢复状态。

2. **P2：关闭窗格期间 renderer 崩溃，重载仍可能取得随后失效的 pane key。**  
   [main.ts:614](/Users/luckye/Documents/Code/a2a/workbench/app/main.ts:614) 等待 switching、creating，但没有等待 [main.ts:384](/Users/luckye/Documents/Code/a2a/workbench/app/main.ts:384) 开始的异步窗格关闭。  
   场景：关闭操作正在等待输入队列或后台回执，此时 renderer 崩溃。新界面先读取包含该窗格的 selection；关闭完成后，后台在 [main.ts:398](/Users/luckye/Documents/Code/a2a/workbench/app/main.ts:398) 删除 key。旧 renderer 的关闭回执已丢失，而新界面的定时刷新只更新侧栏，因此留下失效窗格。实际关闭 handler 与恢复 handler 的内存时序探针确认：**重载取得 `["P"]`，关闭完成后实际集合为 `[]`**。应等待关闭完成再取得最终窗格集合。

第二轮 5 条逐项核对：

| 第二轮问题 | 第三轮核对结果 |
|---|---|
| 1. snapshot 显示历史版本 | **代码已修**。[daemon.ts:423](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:423) 优先取运行时版本；局部探针返回 `9.9.9`，历史仍为 `2.1.304`。真实恢复→snapshot→GUI 证据 **INCOMPLETE**。 |
| 2. ≤64 KiB 重连积压仍可见 | **原反例已消除**：同一 3,846 字节探针现在隐藏期间解析，未隐藏中间帧为 0。但无 launch→绑定 launch 尚有发现 1。 |
| 3. 崩溃重载未等待 creating | **代码已修**：局部时序探针确认 switching、creating 都完成后才重载。真实 GUI 并发场景 **INCOMPLETE**；另有发现 2。 |
| 4. 审计断言仍比较裸版本 | **代码已修**。[run_t108_real.py:105](/Users/luckye/Documents/Code/a2a/workbench/tests/run_t108_real.py:105) 改为比较独立 `--version` 输出，并单独核对 configured/internal_state_version。未提供本候选最终审计落盘的真实运行及对应反事实证据。 |
| 5. GUI 复现文件、构建身份及覆盖不足 | **部分解决**：`register.mts` 已补齐；构建身份与命令已提供。我核对了打包源码及 main/renderer 相关逻辑，包含本轮修复。覆盖不足仍未解决。 |

真实入口证据目前支持：约 2 MB 首次恢复、最终画面、单次 `Page.crash`，以及旧版同脚本失败对照。见 [ui-restore-green-08.json](/Users/luckye/Documents/Code/a2a/evidence/2026-10-21-batch19/T-118/ui-restore-green-08.json)。

以下边界**只有代码检查或局部探针，没有当前候选的真实入口证据**：小积压重连、无 launch 后绑定、空 trace、snapshot/output 错误、切换／创建／关闭期间崩溃、关窗抑制、10 秒内再次崩溃、外部 SIGTERM，以及恢复版本的 GUI 展示和正常登录最终审计。本次没有重跑会写入夹具或证据的端到端测试。
