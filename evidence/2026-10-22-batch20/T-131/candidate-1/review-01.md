# T-131 独立审查报告：支持多个 Worker 并行运行

- **审查对象**：提交 `8f584d45c`（T-131 候选 1，父提交 `03b2d66a3`）及文档补充 `5d4fcd26c`
- **差异文件**：`/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/agy-t131-e6bA/full.diff`
- **审查模式**：只读模式（未执行任何 shell 命令，未修改任何文件，未提交）
- **报告语言**：中文

---

## 重点审查项分析

### 1. 并发假设核查：去掉 `single_worker_slice` 后的后台隔离性

在 [`workbench/src/panes.ts:620-623`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L620-L623) 中，原有的 `single_worker_slice(kind)` 限制被正式移除。针对后台各组件是否存在隐含的“全局单 worker”假设，审查核对如下：

1. **Pane 与线程生命周期隔离**：
   - [`panes.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts) 中所有终端 Pane 均以 `thread`（即 `attempt.thread_id`，UUID）作为主键注册在 `this.panes` Map 中。
   - 每个 Worker 分配有独立的伪终端进程（node-pty spawn）、独立的鉴权 `token`、独立的 PTY 写入队列 `serializeWrite` 以及专用的输出缓冲区 `drain`。
   - 不存在任何假定 `kind === 'worker'` 全局唯一的查询（如 `find(p => p.kind === 'worker')` 并在多处共用）。
2. **Launch 绑定与 Hook 信号路由**：
   - CLI 启动时生成的 `launch` 标识为每次启动独占（UUID）。
   - [`workbench/src/daemon.ts:560-647`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L560-L647) 处理 Claude/Codex 钩子信号（`signal`）时，严格通过 `panes.byLaunch(launch)` 精确匹配发起请求的特定 Pane，不会向其他 Worker 广播或串发。
3. **请求目录与 Relay 回执隔离**：
   - 每个 Worker 启动时在操作系统临时目录创建私有的请求目录（`mkdtempSync("/tmp/a2a-requests-")`），并通过环境变量 `A2A_REQUEST_DIR` 传入其 CLI。
   - [`workbench/src/relay.ts:68-160`](file:///Users/luckye/Documents/Code/a2a/workbench/src/relay.ts#L68-L160) 接收请求时，严格基于该目录内的身份声明绑定核验 `task`、`attempt`、`session`、`fence` 和 `spec_rev`。回执仅写回其私有请求目录，不存在两个并发 Worker 读写同一请求/回执管道的可能。
4. **门禁锁、恢复与 Stop 转交**：
   - 门禁操作锁 [`operationLock`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L880-L895) 粒度是 Task 级（`locks/${taskId}.sqlite3`），并行运行的不同任务之间互不阻塞；路径声明冲突检查由独立的全局 `$claims.sqlite3` 锁负责短时串行保护。
   - Stop 转交与紧急停止（`settleInboxFeedback` 与 `emergencyStop`）通过传入的 `taskId` / `threadId` 精确检索目标 Pane 并执行中断，不会波及其他正在运行的 Worker。
   - **核查结论**：后台各层均具备严密的按 Task / Thread / Launch / RequestDir 维度的命名空间隔离，未发现残留的单 Worker 假设，不会发生串包、串信号或状态串扰。

---

### 2. 引用校验安全性与完整性：`reviewRefsUnchanged`

在 [`workbench/src/gates/core.ts:2553-2579`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L2553-L2579) 中，为了支持其他 Worker 在当前审查进行期间并发工作，放宽了引用未变动检查规则。审查核查如下：

#### (1) 放过的引用改动范围
检查函数通过以下规则判断引用变动是否合法：
1. **未改动引用**：`before.get(ref) === after.get(ref)`；
2. **其他任务的 Attempt 分支**：`branch.exec(ref)?.[1] === taskName(other.task_id) && taskName(other.task_id) !== taskName(task.task_id)`；
3. **其他任务的内部引用**：`ref.startsWith('refs/a2a/attempts/${other.task_id}/')` 以及 `ref.startsWith('refs/a2a/verifications/${other.task_id}/')`；
4. **集成链推进**：目标集成分支（`task.integration_ref`）允许推进，但**必须**能够通过 SQLite `events` 表中记录的 CAS 链（`seq > started.seq` 的 `integrated` 与 `integrated_reconciled` 事件）从旧 HEAD 一步步严格重放达成。

#### (2) 边界与安全性推演
- **任务名前缀碰撞（如 `T-1` 与 `T-10`）**：
  - 正则表达式为 `^refs\/heads\/a2a\/(.+)-a\d+$`，提取捕获组后使用严格全等 `branch.exec(ref)?.[1] === taskName(other.task_id)` 进行比对，不会发生前缀误匹配。
  - 内部引用包含末尾斜杠 `${other.task_id}/`，`refs/a2a/attempts/task-1/` 不会前缀匹配 `refs/a2a/attempts/task-10/`。
- **事件序号基线与 CAS 链安全性**：
  - 基线序号从 `review_requested` 事件的 `started.seq` 开始查找，且严格比对 `others.has(row.task)` 与 `intent.integration_ref === task.integration_ref`。
  - 推进过程强制核验 `intent.G === head` 并步进到 `intent.M`，最终核验 `after.get(ref) === head`。任何未经门禁记录的直接 commit 或非连续跳变都会直接导致检查失败，伪造集成链在逻辑上是不可能的。
- **`integrated` 与 `integrated_reconciled` 结构兼容性**：
  - 代码通过 `const intent = details.intent ?? details;` 正确抹平了 `integrated`（外层包有 intent）与 `integrated_reconciled`（直接存 intent）的结构差异。
- **合法门禁写引用的完备性**：
  - 新 Attempt 创建（`refs/heads/a2a/...-a<N>`）、Attempt 归档（`refs/a2a/attempts/...`）、Verification 归档（`refs/a2a/verifications/...`）、分支清理与删除均在放宽规则内。门禁核心未对冲突回写单独设立 `refs/a2a/conflicts/` 引用，冲突重做依然工作在任务分支上，因此无需额外规则。

#### (3) 潜在薄弱点与发现
- 审查员/Worker 若能绕过沙箱直接写 Git 引用，`otherOwns` 仅核对前缀与正则，未校验该引用是否在 SQLite 中有真实的 attempt 记录（见后文 **Finding 1 (P2)**）。
- 多项目同名任务在同库下的逻辑边界问题（见后文 **Finding 2 (P3)**）。

---

### 3. 测试有效性与 RESULTS.md 审计

审查核对了 [`workbench/tests/test_t131_parallel_workers_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t131_parallel_workers_e2e.py) 及其执行证据 [`RESULTS.md`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-131/candidate-1/RESULTS.md)：

1. **测试独立性**：
   - 测试启动真实的编排后台守护进程、真实 Socket、真实 node-pty 以及真实交互式 Claude Code 进程，工作在独立的临时 Git 仓库与 worktree 沙箱中，并非单元 mock。
2. **屏障（Barrier）的并发证明力**：
   - **Worker 并发屏障**：测试在 Mock Tool Server 端设置了 `both_started` 线程事件，两个并发 Worker（T-1 与 T-2）各自发出的第一次 tool 调用都必须到达，屏障才被释放。如果 Worker 是串行执行的，T-1 等待响应时无法唤醒 T-2，必然触发 120 秒超时。该屏障在物理时序上确凿证明了两个 Worker 的同时并行。
   - **Review 并发交织屏障**：T-2 审查员在执行边界检查时被 `release_t2_review` 屏障挂起，直到 T-1 的集成（修改 `main` 并生成 verification 引用）全部落盘后才被释放，真实模拟了审查期间并发任务推进集成引用的竞态条件。
3. **变异测试（Mutation Testing）辨别力**：
   - `red-parent`：在基线提交（`03b2d66a3`）上运行，由于存在 `single_worker_slice`，第二个 Worker 无法启动，准确在 `both_started` 屏障超时（125.1s）。
   - `mutant-strict-ref-equality`：恢复原有严格不变断言，T-1 审查回收准确因检测到 T-2 的 verification 引用而失败（51.5s）。
   - `mutant-integration-chain-ignored`：抹去集成链回放逻辑，T-2 审查回收准确因主分支推进被拒而失败（51.0s）。
   - `mutant-any-ref-accepted`：变异为无条件放过所有引用改动，在 `--foreign-ref` 注入非法分支 `refs/heads/foreign` 时被测试断言捕获（53.1s）。
4. **RESULTS.md 真实性**：
   - 报告中所列的 7 项运行耗时、退出码与 [`candidate-1/e2e/exits.txt`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-131/candidate-1/e2e/exits.txt) 及对应的 JSON 证据完全吻合，未见数据篡改或夸大。

---

### 4. 其他问题

1. **Ticket 规范文件留存**：
   - [`.project-map/MAP.md:75`](file:///Users/luckye/Documents/Code/a2a/.project-map/MAP.md#L75) 中索引并描述了 T-131，但仓库 `.project-map/tickets/` 目录下未提交独立的 `T-131-*.md` 文件（见后文 **Finding 3 (P3)**）。
2. **失败现场（Discovery）归档**：
   - 探索失败现场按 T-088 规范归档在外置磁盘，仓库内保留了 `candidate-1/e2e/fixtures.archive.json` 索引，符合项目规则。

---

## 发现项清单

### [P2] `workbench/src/gates/core.ts:2563-2565`
- **文件与行号**：[`workbench/src/gates/core.ts:2563-2565`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L2563-L2565)
- **发现说明**：`otherOwns` 仅对其他任务的 ID 前缀和分支正则（`refs/heads/a2a/${other_task_name}-a\d+`）做字面量匹配，未核验该引用是否为数据库中合法记录且活跃的 Attempt 或 Verification。
- **具体失败场景**：
  虽然正常的审查员工作在剥离了 `.git` 的干净物理副本（`copyReviewCandidate`）中，但如果审查会话或恶意 Worker 实现了沙箱穿透、直接操作宿主 Git 仓库并创建伪造引用（例如写入 `refs/heads/a2a/another_task_name-a999` 或 `refs/a2a/attempts/another_task_id/rogue`），`reviewRefsUnchanged` 会将其误判为“属于其他任务的合法引用更新”而直接忽略放行，从而造成审查边界防御的局部盲区。
- **建议**：
  在 `otherOwns` 匹配到前缀或分支模式后，建议增加一层轻量级数据库核对（例如确认该 Attempt 或 Verification 引用确实记录在 `attempts` 表或 `events` 表中），确保只放行经过门禁登记的引用变动。

---

### [P3] `workbench/src/gates/core.ts:2560-2565`
- **文件与行号**：[`workbench/src/gates/core.ts:2560-2565`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L2560-L2565)
- **发现说明**：排除自身分支的条件为 `taskName(other.task_id) !== taskName(task.task_id)`。
- **具体失败场景**：
  若在极端边缘场景下，多个项目共用同一个底层 Git 仓库且注册在同一个 a2a 数据库实例中，若项目 A 和项目 B 恰好存在同名任务（例如项目 A 叫 `T-1`，项目 B 也叫 `T-1`，虽 `other.task_id !== task.task_id`，但 `taskName` 均为 `T-1`），则 `taskName(other.task_id) !== taskName(task.task_id)` 会计算为 `false`。此时项目 B 的 Worker 推进其 `a2a/T-1-a1` 分支时，项目 A 的审查员边界检查将无法把该分支识别为“他人分支”，从而误报 `review_shared_refs_changed` 失败。
- **建议**：
  若存在同库多项目并行可能，可在分支命名中引入项目前缀，或使判断逻辑基于全局唯一 Task ID 进行绑定。

---

### [P3] `.project-map/MAP.md:75`
- **文件与行号**：[`.project-map/MAP.md:75`](file:///Users/luckye/Documents/Code/a2a/.project-map/MAP.md#L75)
- **发现说明**：未提交独立的 `.project-map/tickets/T-131-*.md` 需求文档文件。
- **具体失败场景**：
  后续审计或自动化状态检查根据约定查找 `tickets/T-131-*.md` 时文件不存在，只能依赖 `MAP.md` 和 commit 记录进行反向溯源。
- **建议**：
  按规范在 `.project-map/tickets/` 下补齐提交 `T-131-parallel-workers.md`。

---

## 总体审查结论

# PASS

- **理由**：
  1. 移除 `single_worker_slice` 后，后台在进程、PTY、Token、请求目录、Relay 校验、信号路由与门禁锁层面均保证了严格的命名空间隔离，无串包或并发冲突隐患。
  2. `reviewRefsUnchanged` 的引用放宽规则严密，CAS 连续重放机制杜绝了伪造集成链的可能，字符级前缀判定规避了 `T-1` 与 `T-10` 等碰撞，且覆盖了门禁合法的引用生命周期操作。
  3. E2E 测试采用真实的真实交互式 CLI 和双向 HTTP 屏障，真实可靠地锁定了 Worker 并发与 Reviewer 竞态条件，全套变异测试均有效识别出对应坏实现，`RESULTS.md` 证据详实无夸大。
  4. 发现的 P2/P3 问题属于防御深度加固与文档完整性建议，不影响本候选方案的核心功能与并发安全性。
