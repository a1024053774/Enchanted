STATUS: **FAIL**

SUMMARY: **需修复**。发现 1 项 P2 停止流程缺陷、1 项 P3 证据表述问题；未发现已复现的跨 attempt 身份误绑定。P3 涉及的底层行为是既有行为，本次新增的是不准确的说明。

TARGET: `dbde5eeb444faa95e173ba06b3ee33b56d57e75f`

EVIDENCE:

- 按 `git diff faf1b0d7a dbde5eeb4` 和固定 SHA 的文件内容审查。开始、结束时工作区均干净，提交未移动；`git diff cd69040d1 dbde5eeb4 -- workbench` 为空。`acceptance/**`、`REVIEW.md` 没有变化。
- 除静态检查外，用 `node --input-type=module -e` 从固定 SHA 抽取原方法，运行纯内存时序探针。数据库使用内存 SQLite，运行时、锁及进程生命周期由探针控制；没有启动真实后台、CLI 或运行会写仓库的测试。
- 核对了候选保存的红态、绿态、变异和回归摘要。project-map 开始、结束检查均为 Problems 0、Stale living docs 0。

FINDINGS:

1. **[P2] 在途绑定没有纳入停止流程，关库后错误记录再次抛错，形成未处理的 Promise 拒绝。**

   位置：[daemon.ts:92](/Users/luckye/Documents/Code/a2a/.claude/worktrees/dreamy-ptolemy-d0f2f0/workbench/src/daemon.ts:92)、[daemon.ts:284](/Users/luckye/Documents/Code/a2a/.claude/worktrees/dreamy-ptolemy-d0f2f0/workbench/src/daemon.ts:284)、[core.ts:837](/Users/luckye/Documents/Code/a2a/.claude/worktrees/dreamy-ptolemy-d0f2f0/workbench/src/gates/core.ts:837)。

   **已复现的时序**：

   - `nativeSessionLearned` 读完窗格，拿任务锁得到 `operation_busy`，进入 100ms 等待。
   - 原门禁操作完成、锁释放；在绑定重试前收到停止请求。
   - `beginShutdown()` 设置停止标志。`shutdown()` 等待请求和 resumed runs，但没有等待这个绑定 Promise；在窗格停止和连接关闭很快完成的情况下，先执行 `gates.close(); store.close()`。
   - 绑定醒来，抛出 `daemon_stopping`；其 `.catch` 再调用 `store.event(...)`，向已经关闭的数据库写事件。

   使用候选的绑定方法、回调、shutdown 和事件写入代码，在内存 SQLite 中观察到：

   ```text
   ERR_INVALID_STATE: database is not open
   ```

   加监听器时捕获到 `unhandledRejection`；取消监听器、使用当前 Node v26.5.0 默认行为时，进程退出码为 **1**。这条路径既没有留下 `native_session_bind_failed`，也没有正常完成异步错误处理。

   另一个内存探针显示：若停止发生在 `await readThread()` 期间，该方法返回后没有再次检查 `shuttingDown`，仍可继续写 `runtime_bound`。

   **最小修正方向**：登记在途绑定，在关闭数据库前等待其收尾；让错误记录本身失败时也有明确接收者，并在 `readThread` 返回后重新检查停止状态。需要覆盖“等锁期间停止”和“读窗格期间停止”两个时序，无须扩大重试范围。

2. **[P3] RESULTS 对重启后 `run` 补绑的说明过宽。**

   位置：[RESULTS.md:93](/Users/luckye/Documents/Code/a2a/.claude/worktrees/dreamy-ptolemy-d0f2f0/evidence/2026-11-08-batch34/T-253/RESULTS.md:93)。

   “经 run 跟随的 attempt 仍由 observeRun 补绑”放在后台重启限制之下，容易被理解为这两种恢复情况可由 `run` 补救。但 [core.ts:3059](/Users/luckye/Documents/Code/a2a/.claude/worktrees/dreamy-ptolemy-d0f2f0/workbench/src/gates/core.ts:3059) 会在补绑之前拒绝 `live.stopped && task.state === "claimed"`。

   对固定 SHA 的 `observeRun` 运行内存探针，输入为：任务仍为 `claimed`、attempt 的原生会话为空、恢复记录中的窗格已停止且带有原生会话号。结果为：

   ```text
   result: run_external_unknown
   attempt.native_session: null
   runtime_bound 写入次数: 0
   ```

   **修正方向**：把说明限定为仍能通过观察前置检查的运行中窗格；已停止的恢复窗格不应被描述为可以靠 `observeRun` 补绑。这不是要求本票扩展恢复方案。

COUNTEREXAMPLE:

- 独立内存探针中，别的 launch、thread、shell、已绑定领导进程均被拒为 `identity_conflict`，没有写入；attempt 编号、fence、规格版本不匹配均被拒为 `stale_attempt`。等锁期间替换 attempt 也没有写入新 attempt。
- 首次绑定写一条事件，重复调用不再写；连续扫描五次只触发一次回调。reviewer、辅助 rollout、已知原生会话的窗格没有触发 worker 绑定。
- 候选保存的端到端绿态确实记录了：
  `dispatched(native=null)` → `pane_native_session` → `runtime_bound(by=native_session_learned)`，会话号一致，之后回收及再派成功。去掉回调的 `t253-no-bind` 变异则在业务断言上失败：回收 `identity_conflict`、再派 `already_claimed`。它能够区分本次修复前后。
- 单元夹具包含本问题需要的派发后身份字段，且补齐了让 reclaim 到达身份检查所需的登记；它不是完整派发记录。缺少方法的单元红态本身只证明接口不存在，真正的业务红态由上述端到端结果提供。

LIMITATIONS:

- 新绑定临界区内没有 `await`。同一后台中的 `observeRun`、dispatch、submit、reclaim 不会与它交错持锁；回调也没有被 dispatch 等待，未发现循环等待。100ms 重试有实际锁竞争依据，不属于无证据重试。但锁若一直不释放，循环没有期限；目前停止收尾存在第 1 项缺陷。
- T-170 的 `neverStarted` 条件和 reclaim 身份要求没有改动；候选保存的 failed、fast、hang 回归分别支持“启动失败可回收”和“原生会话为空、CLI 仍运行时拒绝”。本次未重新启动这些端到端测试。
- 恢复路径不会重新触发 B，不能据此宣称恢复场景已修好。RESULTS 已披露这个缺口，也披露了“没交付就结束回合”未单独运行、错误记录路径没有端到端证据；这些未知不计作通过。
- 未证实正常运行期间存在回调重复触发、跨 attempt 误绑定或与 `observeRun` 撞锁导致失败。纯内存探针不能替代真实后台停止、重启的端到端验证。

**结论：需修复第 1 项停止流程缺陷，并收窄第 2 项证据说明；当前候选不建议合并。**