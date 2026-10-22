# T-136 候选 2（提交 `338c51b4f`）独立审查报告

本审查以 `full.diff`（基准父提交 `01e0effd7`）、上一轮审查报告（[`evidence/2026-10-22-batch20/T-136/candidate-1/review-01.md`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-1/review-01.md)）、真实 Haiku 运行证据（[`evidence/2026-10-22-batch20/T-136/candidate-1/real-haiku/`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-1/real-haiku/)）以及本轮端到端运行产物（[`evidence/2026-10-22-batch20/T-136/candidate-2/e2e/`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-2/e2e/)）为准，采用纯只读方式核对。

---

## 一、候选 2 端到端运行观察清单（`candidate-2/e2e/`）

在审查执行期间，本轮端到端全部 5 项任务均已执行完毕，读取到的文件及状态如下：

1. [`candidate-2/e2e/commands.sh`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-2/e2e/commands.sh)：包含 `green`、`red-candidate-1`、`mutant-archive-not-in-range`、`mutant-start-failure-silent`、`t135-green` 五个任务调度脚本。
2. [`candidate-2/e2e/exits.txt`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-2/e2e/exits.txt)：
   - `mutant-archive-not-in-range exit=1`
   - `red-candidate-1 exit=1`
   - `green exit=0`
   - `mutant-start-failure-silent exit=1`
   - `t135-green exit=0`
3. [`candidate-2/e2e/green.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-2/e2e/green.json)：`status: "PASS"`，通过全部 12 项 checks（包含新增的 `second_package_archive_in_range` 与 `start_failure_recorded_on_run`）。
4. [`candidate-2/e2e/red-candidate-1.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-2/e2e/red-candidate-1.json)：针对候选 1（`01e0effd7`）运行，精准在 `second_package_archive_in_range` 断言失败（包内混入了历史旧会话 5 个 vs 范围内 3 个），退出码 1。
5. [`candidate-2/e2e/mutant-archive-not-in-range.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-2/e2e/mutant-archive-not-in-range.json)：移除范围过滤的变异体精准在 `second_package_archive_in_range` 失败，退出码 1。
6. [`candidate-2/e2e/mutant-start-failure-silent.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-2/e2e/mutant-start-failure-silent.json)：移除 `start_failed` 记录的变异体精准在 `start_failure_recorded_on_run` 失败，退出码 1。
7. [`candidate-2/e2e/t135-green.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-2/e2e/t135-green.json)：`status: "PASS"`，通过全部 6 项归档回归检查。

---

## 二、上一轮四条发现（F1–F4）复核与新引入问题分析

### F1. 复盘包中的 `trajectory_archive` 范围过滤（已修复）
- **实现核对**：[`workbench/src/retrospective.ts:130-132`](file:///Users/luckye/Documents/Code/a2a/workbench/src/retrospective.ts#L130-L132) 将查询改为了：
  ```sql
  SELECT launch, source, file, max(end) AS end FROM trajectory_archive
  WHERE created_at < ? GROUP BY launch, source HAVING max(created_at) >= ?
  ```
  参数传入 `(until, since ?? '')`。若 `since` 为 null 则 `since ?? ''` 为 `''`，匹配全部历史；若 `since` 有值，则仅包含在 `[since, until)` 内有新归档增量的会话，且 `max(end)` 截断至 `until` 之前。
- **验证核对**：新增端到端检查直接从底层 SQLite 读取预期会话集合并与复盘包比对，变异 `mutant-archive-not-in-range` 与父提交 `red-candidate-1` 均被成功击杀。

### F2. 启动失败后永久“进行中”与槽位处理（修复表象，引入新缺陷）
- **修复部分**：[`workbench/src/daemon.ts:85-98`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L85-L98) 将 `panes.startShell` 与 `panes.runInShell` 包裹在 `try ... catch` 中，捕获异常后调用 `retrospectives.record(run.id, "start_failed", { error: String(error) })`；在 `retrospectiveTick` 中为每个项目独立捕获启动错误，避免单项目失败影响其他项目与导入；界面在 [`workbench/app/RetrospectivePage.tsx:37-42`](file:///Users/luckye/Documents/Code/a2a/workbench/app/RetrospectivePage.tsx#L37-L42) 显式展示 `没能启动：${notStarted.data.error}`。
- **引入的新问题**：
  在 [`workbench/src/retrospective.ts:77`](file:///Users/luckye/Documents/Code/a2a/workbench/src/retrospective.ts#L77) 中，下一次复盘的默认起始时间依然是无条件获取最后一条记录：
  ```ts
  const since = range.since !== undefined ? range.since : this.runs(project).at(-1)?.until ?? null;
  ```
  当定期复盘或手动复盘启动失败（`start_failed`）后，该次复盘从未真正跑过。按照文档描述“用户可以手动再启动”，但当用户点击“立即复盘”时，`this.runs(project).at(-1)` 命中的正是那次启动失败的运行！导致下一次复盘的 `since` 被直接推到了失败时刻，**彻底丢弃了启动失败前整个周期的所有任务、门禁、问题、提交尾注**（详见下文“发现 1”）。

### F3. 导入无事务保护（已修复，未引入新问题）
- **实现核对**：[`workbench/src/retrospective.ts:121-130`](file:///Users/luckye/Documents/Code/a2a/workbench/src/retrospective.ts#L121-L130) 在插入建议和记录 `imported` 事件外层包裹了同步事务：
  ```ts
  this.db.exec('BEGIN IMMEDIATE');
  try {
    list.forEach(...);
    this.record(run.id, 'imported', ...);
    this.db.exec('COMMIT');
  } catch (error) { this.db.exec('ROLLBACK'); throw error; }
  ```
- **事务与门禁共用库分析**：
  1. `Retrospectives` 持有 `store.db`，而 `A2AGates` 持有独立的连接实例，两者均连接至 `state.sqlite3`，均启用了 `PRAGMA journal_mode=WAL` 与 `PRAGMA busy_timeout=5000`。
  2. 报告文件复制 `copyFileSync` 发生在事务开始前，事务内部仅包含纯内存循环、UUID 生成与极速的 SQLite INSERT，无任何异步（async/await）调度或文件 I/O，耗时在微秒级。
  3. `BEGIN IMMEDIATE` 置于 `try` 外层，确保事务未开启时不会调用 `ROLLBACK`。5 秒的 busy_timeout 足够避免与门禁发生锁冲突。未引入死锁或并发破坏。

### F4. Codex 复盘会话未接入轨迹归档（已修复，引入小健壮性隐患）
- **实现核对**：
  1. [`workbench/src/daemon.ts:89-90`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L89-L90) 在记录 `retrospective_started` 时注入了 `CODEX_HOME`；
  2. [`workbench/src/trajectoryArchive.ts:159-160`](file:///Users/luckye/Documents/Code/a2a/workbench/src/trajectoryArchive.ts#L159-L160) 支持 Codex 会话根据工作目录匹配原生 rollout；
  3. `codexRolloutIn` 在日期子目录下读取 `rollout-*.jsonl` 的第一行 `session_meta`，校验 `parsed.payload?.cwd === cwd`，并缓存在 `rolloutByCwd`。
- **Codex rollout 按 cwd 查找是否会认错会话**：
  - **核对结论：不会认错会话**。
  - 复盘会话的工作目录是每次随机生成的唯一目录 `run.out = join(this.root, id, 'out')`（其中 `id` 为 UUID），并且 Codex 启动参数显式传入了 `-C run.out`。
  - 项目内其他 worker、reviewer 使用 worktree 路径，外部会话也不会进入该 UUID 专属的私有子目录。因此 `parsed.payload?.cwd === cwd` 是严格单调且唯一的，不会与系统内任何其他 Codex 会话冲突。
- **引入的新隐患**：`firstLine()` 内部直接调用 `openSync`，未包裹 `try ... catch`，若扫描目录时遇到权限受限或被并发删除的文件，会导致整轮 `sources()` 抛错中断（详见下文“发现 2”）。

---

## 三、真实 Haiku 运行证据核对

核对 [`evidence/2026-10-22-batch20/T-136/candidate-1/real-haiku/run-02.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-1/real-haiku/run-02.json) 与 [`run-02-report.md`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-1/real-haiku/run-02-report.md)：
1. **真实入口**：测试经由真实 Electron 实例启动，在前端界面点击项目 demo，切换至“复盘”页，选择 `claude-haiku-5-5`，点击“立即复盘”按钮触发。
2. **凭据与环境**：携带用户真实的 `USER` 与 `LOGNAME`，从 macOS 钥匙串自动加载用户的真实 Claude 登录；去除了所有 Mock/Scripted 端点配置。
3. **写入范围（Confinement）**：`git status --porcelain` 验证除导入的报告复制至 `findings/` 外，项目工作区无任何多余修改；Claude 仅向 `out/` 写入了 `report.md` 和 `suggestions.json`。
4. **生成质量与契约**：Claude Haiku 调用了 3 次工具完成产出；生成的 [`run-02-report.md`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-1/real-haiku/run-02-report.md) 忠实引用复盘包内容，说明了由于新项目缺少门禁与任务，故相关项目为空；建议为 0 条且界面卡片同步渲染 0 条。
5. **结论**：真实运行证据充分、真实、可复现，满足 ticket 的真实入口验收标准。

---

## 四、新检查与变异证明核对

在 [`workbench/tests/test_t136_retrospective_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t136_retrospective_e2e.py) 中：
1. **F1 证明**：
   - 检查项 `second_package_archive_in_range`（行 256–265）使用 SQLite 只读直连查询 `trajectory_archive` 中落在 `[since, until)` 的会话集合，要求包内集合与该区间完全一致，且 `archived_before - archived_in_range` 非空（证明存在区间前的旧会话）。
   - 变异体 `archive-not-in-range`（移除 SQL 范围约束）与未打补丁的候选 1 父提交 `red-candidate-1`（`01e0effd7`）均精准在行 263 抛出 `AssertionError: second_package_archive_in_range`，退出码均为 1。
2. **F2 证明**：
   - 检查项 `start_failure_recorded_on_run`（行 306–317）模拟项目目录被移走的异常，断言启动请求被拒且库中仅追加 `start_failed` 事件。
   - 变异体 `start-failure-silent`（注释掉 `record(run.id, "start_failed", ...)`）在行 316 断言失败，退出码为 1。

新检查项期望值独立于实现生成内容，变异与旧版本反例充分证明了有效性。

---

## 五、审查发现项清单（Findings）

### 发现 1：复盘启动失败后，下次复盘计算 `since` 会永久跳过失败周期内的全部历史数据
- **文件与行号**：[`workbench/src/retrospective.ts:77`](file:///Users/luckye/Documents/Code/a2a/workbench/src/retrospective.ts#L77)
- **严重度**：**P2**
- **失败场景**：
  在 `Retrospectives.prepare()` 中，下一次复盘的默认起点定义为：
  ```ts
  const since = range.since !== undefined ? range.since : this.runs(project).at(-1)?.until ?? null;
  ```
  假设项目在第 1 周有 5 个任务完成并集成。
  第 1 周定期复盘启动时，系统调用 `prepare()` 创建 Run 1，记录 `since = null, until = T1`。
  随后 `panes.startShell` 遇到偶发错误（例如系统 PTY 上限、资源抖动或临时异常），抛错并记录 `start_failed`。Run 1 从未实际运行，没有产出报告，该周期的 5 个任务从未被复盘。
  用户在界面上看到“没能启动：...”的提示，按照文档说明点击“立即复盘”重新启动（Run 2）：
  此时 `prepare()` 查询 `this.runs(project).at(-1)`，由于该数组按插入顺序排列，末尾元素正是启动失败的 Run 1！
  因此 Run 2 的 `since` 被设置为 Run 1 的 `until`（`T1`），Run 2 的时间区间变为 `[T1, T2)`。
  **结果**：第 1 周的所有任务、门禁打回、审查打分、尾注等数据在 Run 2 的复盘包中全部被过滤掉；由于以后所有的复盘 `since` 都会基于 Run 2，导致第 1 周的全部数据在复盘历史上被**永久静默跳过**，从未被任何复盘会话处理。
- **修复建议**：计算默认 `since` 时应过滤掉启动失败的运行，仅取最后一次成功启动或导入完成的运行 `until`，例如：
  ```ts
  const lastEffective = this.runs(project).reverse().find(r => !this.events(r.id).some(e => e.type === 'start_failed'));
  const since = range.since !== undefined ? range.since : lastEffective?.until ?? null;
  ```

### 发现 2：`firstLine()` 缺乏打开异常防护，单个异常文件可能阻断整个后台的轨迹归档
- **文件与行号**：[`workbench/src/trajectoryArchive.ts:86`](file:///Users/luckye/Documents/Code/a2a/workbench/src/trajectoryArchive.ts#L86)、[`workbench/src/trajectoryArchive.ts:198`](file:///Users/luckye/Documents/Code/a2a/workbench/src/trajectoryArchive.ts#L198)
- **严重度**：**P3**
- **失败场景**：
  在 `codexRolloutIn()` 中，通过 `readdirSync` 遍历 `sessions/YYYY/MM/DD/` 目录并逐个调用 `firstLine(join(dir, name))`。
  `firstLine` 直接调用 `openSync(path, 'r')`，没有 `try ... catch` 保护。
  如果在遍历期间某个文件被 Codex 进程轮转删除、权限异常或无法打开，`openSync` 会抛出 `ENOENT` 或 `EACCES`。
  由于 `codexRolloutIn` 是在 `sources()` 中同步执行的（尚未进入 `sweep()` 内层针对单个 source 的 `try ... catch`），该异常会直接导致 `sources()` 崩溃，使当次 30 秒轮询完全中止，导致所有其它正常的会话（包括 Claude、Codex worker）在该轮次中均无法进行增量归档。
- **修复建议**：将 `firstLine()` 内部的 `openSync` 包裹在 `try ... catch` 中，打开失败直接返回 `null`。

---

## 六、总体结论

**INCOMPLETE**

### 判定理由
1. **上一轮缺陷主体已修复**：F1（范围过滤）、F3（导入事务保护）、F4（Codex 轨迹归档）均已妥善修复；真实 Haiku 运行证据齐备且全部通过；新增变异与父提交反例均按要求执行并通过。
2. **存在逻辑缺陷（发现 1，P2）**：在处理 F2（启动失败槽位）时，未处理启动失败后 `prepare()` 水位线计算的继承关系。启动失败后用户手动重新复盘，会导致失败周期内的所有历史任务、门禁记录在复盘包中被永久丢弃，违背复盘功能的目标。该 P2 缺陷修复成本极小（只需在寻找 `at(-1)` 时过滤 `start_failed`），修复并补充针对该场景的回归测试后方可合入。
