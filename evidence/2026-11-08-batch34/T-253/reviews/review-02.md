STATUS: **PASS**

SUMMARY: **未发现本轮范围内必须修复的缺陷。审查 01 的 P2 已修复，P3 的说明已收窄。**

TARGET: `8fad54c0dfcd9f1358dbb98799e0d8c187be7bf3`，比较基线 `dbde5eeb4`。本结论仅覆盖这两项修复及其引入的风险。

EVIDENCE:

1. **停止期间不再写绑定，关库前会等待绑定收尾。**  
   [core.ts:837](/Users/luckye/Documents/Code/a2a/.claude/worktrees/dreamy-ptolemy-d0f2f0/workbench/src/gates/core.ts:837) 在 `readThread` 返回后检查停止状态，检查到拿锁、核对和写入之间没有 `await`。从固定 SHA 抽取原方法运行纯内存探针，结果为：
   - 读窗格期间停止：拒 `daemon_stopping`，绑定写入次数为 0。
   - 等锁期间停止、锁继续保持占用：下一轮读完后拒绝，没有继续等锁。
   - 绑定尚未完成时进入 shutdown：数据库保持打开；释放读取后，先记录拒绝，再关库。
   
   同一“读期间停止”输入在 `dbde5eeb4` 上写入 1 次，在候选上写入 0 次，能区分修前与修后。

2. **未发现 Promise 登记、清理或漏等问题。**  
   [daemon.ts:93](/Users/luckye/Documents/Code/a2a/.claude/worktrees/dreamy-ptolemy-d0f2f0/workbench/src/daemon.ts:93) 登记的是包含 `.catch`、`.finally` 的最终 Promise。即使原调用立即完成或拒绝，清理回调也在微任务中运行，发生在 `bindings.add(binding)` 之后；没有提前访问未初始化变量的问题。独立探针验证了多个 Promise 各自完成后 Set 清空。  
   [daemon.ts:299](/Users/luckye/Documents/Code/a2a/.claude/worktrees/dreamy-ptolemy-d0f2f0/workbench/src/daemon.ts:299) 先完成窗格 shutdown，再关闭两个服务，之后才取 Set 快照。生产路径中，worker 已停止，`scan` 会跳过停止窗格；shell 不触发这种绑定；请求、恢复和 resumed runs 也已先收尾。**未找到快照之后仍能新登记绑定的可达时序。**

3. **读取异常和记录失败都有接收者。**  
   非 Refusal 的 `readThread` 错误会进入后台 `.catch`，以错误文字记为 `native_session_bind_failed`，不重试。记录写失败则报告 `event_write_failed`，调用 `panes.onEventWriteFailed`。独立探针验证了 stderr 报告、observer 进入 `failed`、Promise 正常收尾。  
   该接收者最终调用 [core.ts:428](/Users/luckye/Documents/Code/a2a/.claude/worktrees/dreamy-ptolemy-d0f2f0/workbench/src/gates/core.ts:428)，只更新内存状态，不再写数据库；处理方式与 [panes.ts:1357](/Users/luckye/Documents/Code/a2a/.claude/worktrees/dreamy-ptolemy-d0f2f0/workbench/src/panes.ts:1357) 的事件写失败约定一致。普通绑定拒绝不会标坏 observer，只有拒绝记录本身写失败才会触发，未发现处理过重或过轻的证据。

4. **停止后多读一次窗格有成本，但未发现有害副作用。**  
   [panes.ts:2626](/Users/luckye/Documents/Code/a2a/.claude/worktrees/dreamy-ptolemy-d0f2f0/workbench/src/panes.ts:2626) 对已停止窗格直接返回保存的事实；抽取该原方法的探针确认进程查询次数为 0。尚未停止时会执行进程查询，并可能更新观察事实、扫描 rollout、记录事件；它不是纯读取，但不会在这里派发新输入。查询子进程配置了 5 秒超时。  
   与 `observeRun` 相比，这里少了读取前的停止检查，保留了读取后的检查，因此可能多做一次查询；候选没有因此取得停止后的绑定写权限。

5. **新增测试能拒绝相应错误实现。**  
   后台夹具使用真实 `serve()`、门禁与数据库，替换的是窗格和读取边界。[t253_shutdown_host.ts:47](/Users/luckye/Documents/Code/a2a/.claude/worktrees/dreamy-ptolemy-d0f2f0/workbench/tests/t253_shutdown_host.ts:47) 中“等关库或最多 2 秒”刻意制造了区分：
   - 不等待绑定的实现先关库，读取随即返回，拒绝记录落不进库。
   - 正确实现保持库打开，读取在 2 秒后返回，拒绝记录成功，然后关库。
   
   保存的红态、绿态和变异结果与此一致。三个修复点分别有 `stop-not-rechecked`、`shutdown-skips-bindings`、`bind-record-unguarded` 覆盖；期望来自停止契约和审查 01，不依赖实现生成答案。  
   `stop_while_binding` 的失败诊断落在 `daemon_stopped` 之后，**本轮可接受**：它仍在关库前完成，没有绑定或验收成功写入。当前代码没有把 `daemon_stopped` 当作事件表的终止屏障；既有停止测试要求的是在途请求结果先于它完成。

6. **P3、证据保存和项目约束符合本轮要求。**  
   [RESULTS.md:125](/Users/luckye/Documents/Code/a2a/.claude/worktrees/dreamy-ptolemy-d0f2f0/evidence/2026-11-08-batch34/T-253/RESULTS.md:125) 明确限定：只有仍在运行、能通过前置检查的窗格可由 `observeRun` 补绑；已停止的 claimed 恢复窗格会先拒 `run_external_unknown`。原 P3 表述问题已修正。  
   `test_startup_shutdown_e2e.py` 的宿主确实没有创建操作者凭据，当前 `serve()` 会在启动时拒绝；该要求和宿主代码均早于本票。将这四项记为未跑通、不计 PASS 有依据。旧顶层绿态、变异及回归摘要与移入 `r2/` 的对应内容直接比较一致。`acceptance/**`、`REVIEW.md` 未改；未发现新增门禁旁路、持锁等待或无依据的 fallback、重试。

FINDINGS:

- **无已证实的新增缺陷；无必须修复项。**

COUNTEREXAMPLE:

- `stop-not-rechecked`：两个停止检查失败。
- `shutdown-skips-bindings`：缺少应持久化的绑定拒绝记录，即使退出码为 0 仍判失败。
- `bind-record-unguarded`：记录写失败导致后台退出 1。
- 本轮独立探针也确认旧版在读期间停止后仍写入，候选拒绝写入。

LIMITATIONS:

- 本轮只运行了纯内存探针和只读检查；真实后台、CLI 及回归结果来自候选保存的证据，没有重新启动落盘测试。真实 CLI 下“绑定恰好与停止重叠”的端到端证据仍未提供，RESULTS 已披露。
- `Promise.all` 自身没有超时。**若 `readThread` 永远不兑现，shutdown 就会一直等**；目前未证实生产读取能进入这种状态。2 秒夹具证明收尾顺序，不能证明真实停止耗时，也不能把“100ms 重试”理解为整个停止流程的耗时上限。
- 后台测试断言了 stderr 和进程存活，没有直接断言 observer 为 `failed`；本轮独立内存探针补查了这一行为。
- T-127 首次失败的保留摘要只显示后台启动失败，没有保存能核对 TLS 重置原因的 stderr。因此“TLS 连接被重置”的具体归因标为**未证实**；随后按 `b01096b84` 重跑通过的摘要存在，首次失败也没有被算作 PASS。
- 未运行全量测试。开始、结束时固定提交均未移动，工作区均干净；project-map 两次均为 Problems 0、Stale living docs 0。全程未修改文件、未提交。

**结论：可合并 `8fad54c0d`。本轮 P2、P3 修复通过复核；上述证据边界不构成已证实的合并阻断项。**