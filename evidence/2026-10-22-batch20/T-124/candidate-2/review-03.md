作为独立审查者，已完成对提交 `374a7c924`（父提交 `28a0550cc`，T-124 候选 2）及对应代码差异、需求契约 [`.project-map/tickets/T-124-terminal-controller-answers-attach-run.md`](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-124-terminal-controller-answers-attach-run.md) 与验收结果 [`evidence/2026-10-22-batch20/T-124/candidate-2/RESULTS.md`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-124/candidate-2/RESULTS.md) 的逐项审查。审查过程遵循只读原则，未执行任何命令或修改任何文件。

---

### 一、重点审查项分析

#### 1. 后台重启续跑（[`core.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L623-L670) 的 `resumeRuns` / `resumeRun` 与 [`daemon.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L240-L254) 的调用顺序与关停等待）
- **不会重复派发**：
  在 [`core.ts#L646`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L646) 中，`lost` 的判定严格限定为 `task.current_attempt?.attempt_id === run.attempt_id && ["claimed", "reviewing", "paused"].includes(task.state)`。已处于 `submitted`、`verified`、`integrating`、`accepted` 等成果已交付状态的任务，`lost` 为 `false`，绝不触发重新派发，直接进入 `follow()` 继续推进验收或集成。每个任务的续跑在进入时均获取任务级独占锁 [`DatabaseSync("${run.task_id}.run.sqlite3")`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L642)，排除了并发或重复续跑的可能。
- **不会接管别的 attempt**：
  在 `resumeRun` 中核对 `task.current_attempt?.attempt_id === run.attempt_id`；若当前 attempt 已不再是 run 最初绑定的 attempt，`lost` 为 `false`；随后的 [`follow()`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L410) 显式调用 `this.current(initial, run.attempt_id!)`，一旦 attempt 不匹配立即抛出 `stale_attempt`，在 [`runFailed()`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L559) 中将 run 的 outcome 置为 `superseded` 并停止推进，绝不接管任何外部 attempt。
- **操作锁、fence、attempt 绑定不被绕过**：
  所有外部动作（`reclaim`、`dispatch`、`verify`、`integrate`）均经由统一入口 `this.request()`，严格执行 SQLite 事务排他操作锁 [`operationLock`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L3431)；在重新派发时，由门禁内部生成新 attempt 并同步更新 `run.attempt_id` 和 `run.thread_id`，自增 `task.fence` 与 `attempt.fence`。
- **截止时间不被绕过**：
  在 [`core.ts#L665`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L665) 中，`remaining` 计算公式为 `Date.parse(run.started) + run.wait_seconds * 1000 - Date.now()`，严格锚定在 run 首次启动的物理时刻，重启不会重置或延长等待期限；超时直接抛出 `run_deadline` 并标记为 `deadline`。
- **回收再派发的条件正确**：
  被打断的 attempt 仅在任务处于工作未完成阶段（`claimed`、`reviewing`、`paused`）时触发重新派发，且必须先通过门禁 `reclaim`（此时上一代已通过 `registerGone` 确认旧进程退出），完全符合 T-096 裁定 B 与 T-124 裁定 4；若 run 未持久化记录初始派发参数（`run.dispatch` 为空），则安全停止并置为 `paused`，不盲目补发。
- **启动顺序与关停等待可靠**：
  - **启动顺序**：[`daemon.ts#L249-L253`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L249-L253) 中先执行 `gates.recoverReviews()` 与 `panes.recover(daemon)`，待所有上一代窗格恢复或通过 `registerGone` 确认退出并置为 `stopped` 之后，`recovery.then(...)` 才触发 `gates.resumeRuns()`，消除了回收与进程存活的竞态。
  - **关停等待**：[`daemon.ts#L240`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L240) 中显式执行 `await gates.resumedRunsSettled()`，等待 `resuming` 集合中的所有续跑 Promise 在感知到 `shuttingDown` 后落盘 `outcome: "paused", error: "daemon_stopping"`，随后才关闭 PTY 和数据库，避免了写入半途被强行中断。

#### 2. 窗格恢复（[`panes.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L449-L506) 的 `restore`、`registerGone`、`requireMonitorRestore`）
- **非 monitor 记录与正常登录会话隔离**：
  [`requireMonitorRestore`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L48-L53) 严格核对 `record.role === "monitor"`、`record.sandbox === "read-only"`、`typeof record.parent_launch === "string"`，且通过 `requireNotNormalLogin` 排除未经过代理/mock 的正常个人登录环境；受管 worker/reviewer 的启动记录因具有 `attempt` 字段，会在 [`check(record.attempt === null)`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L471) 被拦截并拒绝恢复；此外，shell 启动参数必须严格以 `MANAGED_SHELL_TAIL` 结尾，彻底杜绝了将普通会话冒充为 monitor 恢复的可能。
- **确认进程退出的判断可靠性**：
  [`registerGone`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L819-L845) 不仅检查 PTY shell 的 PID，还比对由 `pane_leader_observed` 事件持久化的 CLI leader PID。调用底层的 `/usr/bin/python3 processSnapshot.py`（内核 `libproc`）进行进程轮询，给予最多 10 秒等待进程自然退出。如果 10 秒后目标进程依然存活，抛出 `previous_process_alive`，记入 `pane_gone_unconfirmed`，且**不**将该窗格置为 `stopped`，从而在安全侧阻止了后续门禁对存活进程的工作区执行 `reclaim`。

#### 3. 进程快照放宽（[`processSnapshot.py`](file:///Users/luckye/Documents/Code/a2a/workbench/src/processSnapshot.py#L127-L134) 的 `settled_snapshot`）
- **绝不掩盖根进程被替换**：
  在 `settled_snapshot` 中，可重试的异常限定为 `TRANSIENT = ('process_identity_changed_during_query', 'process_parent_changed_during_query')`，并且增加防护条件：
  ```python
  if error.operation not in TRANSIENT or error.pid == root_pid or attempt == SNAPSHOT_ATTEMPTS:
      raise
  ```
  一旦根进程的身份在读取期间发生变更（`error.pid == root_pid`），代码立即抛出异常，绝不进行重试；若根进程退出，`snapshot` 直接返回 `[]`；其他任何权限拒绝、循环或超限错误同样立即失败。
- **绝不会拼出不一致的树**：
  `settled_snapshot` 接收 `make_reader` 工厂函数（`lambda: ProcReader(library)`）。在每一次捕获非根短暂变更重试时，都会创建**全新、无缓存的 ProcReader**，从根节点重新启动一次自顶向下的完整广度遍历与二次一致性核对；重试不是对旧树局部数据的修补，整棵树要么在同一次尝试中全部原子一致通过，要么在 3 次尝试失败后整体报错。

#### 4. Codex 额度读取（[`controllerQuota.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/controllerQuota.ts#L104-L118)）
- **窗口选择**：
  在 [`codexWindows`](file:///Users/luckye/Documents/Code/a2a/workbench/src/controllerQuota.ts#L104-L107) 中，仅提取 `limit_id === "codex"` 的 `token_count` 限制窗口（含 `primary` 和 `secondary`）；在 [`codexQuota`](file:///Users/luckye/Documents/Code/a2a/workbench/src/controllerQuota.ts#L110-L118) 中，过滤出 `used_percent >= 100` 且 `resets_at > 0` 的窗口，按 `resets_at` 降序排列取最大值（最晚重置者），并换算为 ISO 字符串；若无满额窗口，安全回落为 `null`。
- **恢复判断**：
  当日志中出现无 `error` 的 `task_complete` 事件时，判定事实为 `"restored"`；在主循环中，仅当系统当前处于 `reading.exhausted` 状态且检测到 `"restored"` 时才发出 `controller_quota_restored` 事件并清除额度耗尽标记，状态转换准确无误。
- **时间戳与坏行过滤**：
  代码在解析每条 JSON 记录时严格过滤 `Date.parse(record?.timestamp) >= approvedAt`，历史遗留的旧额度报错被完全屏蔽；在 [`read`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L70-L77) 循环中，空行直接通过 `!line.trim()` 跳过，非 JSON 撕裂行通过独立 `try ... catch` 捕获并记录一次 `unreadable`，随后使用 `continue` 继续处理后续完整的有效行，日志流不再被永久阻塞。

#### 5. 上一轮四条发现修复核查
1. **发现 1（P1 - monitor 工作目录路径写死导致无法回收）**：
   已修复。在 [`core.ts#L3590-L3622`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L3590-L3622) 中，工作目录已统一使用 `workspace = attachment.workspace ?? task.repo`；测试已追加 `monitor_reclaimed` 验证，变异体 `reclaim-monitor-repo` 精准在 `identity_conflict` 检查点红态中断。
2. **发现 2（P2 - 空行与坏行导致额度监听永久中断）**：
   已修复。在 [`controllerQuota.ts#L70-L77`](file:///Users/luckye/Documents/Code/a2a/workbench/src/controllerQuota.ts#L70-L77) 中增加了空行跳过与坏行 `continue` 机制；测试已注入噪音数据并由变异体 `quota-stops-at-bad-line` 证明。
3. **发现 3（P3 - `--fast` 参数错误提示显示为 blocking）**：
   已修复。在 [`cli.ts#L266`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/cli.ts#L266) 中已改为 `throw new Error(\`boolean required: \${key}\`)`。
4. **发现 4（P3 - 变异体注释顺序颠倒）**：
   已修复。[`test_t124_controller_e2e.py#L1169-L1174`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t124_controller_e2e.py#L1169-L1174) 中关于 `codex-monitor-unbound` 与 `snapshot-denies-privileged` 的注释已调整对齐。

#### 6. 测试独立性与 RESULTS.md 客观性
- **测试独立性**：
  - 测试套件并未依赖被测实现的自我汇报：run 集成通过独立的 `git ls-tree` 命令检查目标文件；monitor 只读性通过真实的只读执行与磁盘写尝试检查；原生提问禁止通过拦截脚本化模型接口中的 `tools` 列表进行断言；工作台额度通知通过真实的 Electron 窗口渲染及 DOM 检查进行验证。
  - 18 个变异体覆盖了从主控回答、未评分集成、monitor 回收、坏行容错到重启续跑各阶段，均能使测试准确失败在预设判定点。
- **RESULTS.md 客观性**：
  - 报告客观详实，未虚标断言项；如实记录了测试执行中遭遇的磁盘不足、Codex 本地依赖缺失、变异体语法错误等异常运行现场，并标明“不作数的运行”；
  - 对“非主控窗格仍出现的原生提问记 `native_question_ignored`”明确标注为“无直接证据（仅代码逻辑）”，未强行记为通过。

---

### 二、审查发现列表

本次代码审查**未发现**阻碍交付的 P0、P1、P2 或 P3 级缺陷。所有重点安全边界、门禁契约、状态机流转及并发锁逻辑均严密合规。

---

### 三、总体审查结论

**结论**：**PASS**

**依据**：
1. 候选 1 审查报告中的全部四条发现（包括 P1 级 monitor 回收缺陷）均已彻底修复并经过独立变异测试验证；
2. 针对用户 2026-10-22 的四条裁定（1.a 原生提问改经 issue 且会话禁用提问工具、2 进程快照非根瞬时变化放宽重试、3 Claude 与 Codex 主控额度监控并在真实窗口核对、4 后台重启后 run 续跑与 monitor 恢复）的实现完备严密，未破坏门禁操作锁、fence、attempt 绑定与截止时间契约；
3. 测试套件设计具备充分的独立性与敏感度，证据记录详实可信，符合项目质量与交付规范。可以推进合并。
