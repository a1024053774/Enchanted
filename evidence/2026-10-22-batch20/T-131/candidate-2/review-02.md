# T-131 候选 2 独立复审报告：多 Worker 并行运行与共享引用校验收紧

- **审查对象**：提交 `c6921bf44`（T-131 候选 2）及文档更新 `85b212a60`
- **差异文件**：`/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/agy-t131c2-riVH/full.diff`
- **审查模式**：严格只读模式（未执行任何 shell 命令，未创建或修改任何文件，未提交）
- **依据规范**：[.project-map/MAP.md](file:///Users/luckye/Documents/Code/a2a/.project-map/MAP.md)、[workbench/README.md](file:///Users/luckye/Documents/Code/a2a/workbench/README.md)、[review-01.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-131/candidate-1/review-01.md)
- **总体结论**：**`INCOMPLETE`**（发现 1 项关于冲突回写合法引用误拒的缺陷 [P1]，待修复收敛后方可 PASS）

---

## 一、重点审查项分析

### 1. `reviewRefsUnchanged` 的 `attemptOf` / `otherOwns` 正确性分析

在 [`workbench/src/gates/core.ts:2559-2573`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L2559-L2573) 中，候选 2 引入了辅助函数 `attemptOf` 与 `otherOwns` 对放行的引用进行严格校验。分析如下：

```typescript
    // Only the names the gate gives a task's refs, for attempts it has already made (review 01 P2).
    const attemptOf = (ref: string, other: A2ATask) => {
      const name = taskName(other.task_id);
      const found = ref.startsWith(`refs/a2a/attempts/${other.task_id}/`) ? /^a(\d+)$/.exec(ref.slice(`refs/a2a/attempts/${other.task_id}/`.length))
        : ref.startsWith(`refs/a2a/verifications/${other.task_id}/`) ? /^a(\d+)\/v\d+$/.exec(ref.slice(`refs/a2a/verifications/${other.task_id}/`.length))
        : name !== taskName(task.task_id) && ref.startsWith(`refs/heads/a2a/${name}-`) ? /^a(\d+)$/.exec(ref.slice(`refs/heads/a2a/${name}-`.length)) : null;
      return found ? Number(found[1]) : null;
    };
    const otherOwns = (ref: string) => [...others.values()].some((other) => {
      const fence = attemptOf(ref, other);
      return fence !== null && fence >= 1 && fence <= other.fence;
    });
```

#### (1) 三种引用名的解析与边界
1. **隐藏 Attempt 归档引用**：`refs/a2a/attempts/${other.task_id}/a${N}`
   - 由 [`cleanupAttempt`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L1295) 生成。
   - `ref.slice(...)` 剥离前缀后通过 `/^a(\d+)$/` 严格匹配，正确解析出 Attempt 序号 `N`。
2. **隐藏 Verification 归档引用**：`refs/a2a/verifications/${other.task_id}/a${N}/v${K}`
   - 由 [`cleanupVerification`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L1371) 生成。
   - `ref.slice(...)` 剥离前缀后通过 `/^a(\d+)\/v\d+$/` 严格匹配，正确提取 Attempt 序号 `N`。
   - **注意**：此处对门禁内部产生的**冲突回写保留引用**存在遗漏（详见后文【发现 1】）。
3. **任务分支引用**：`refs/heads/a2a/${name}-a${N}`
   - 由 [`claim`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L1578) 生成。
   - `ref.slice(...)` 剥离前缀后通过 `/^a(\d+)$/` 严格匹配，正确提取 Attempt 序号 `N`。

#### (2) `fence` 上下界有效性
- 门禁每次为任务派发新 Attempt 时，执行 `task.fence = attempt.fence`（从 1 开始单调递增），并通过事务即时写入 `tasks` 表；
- `reviewRefsUnchanged` 在审查结束核对边界时动态查询当前 `SELECT data FROM tasks`，获取最新的 `other.fence`；
- `fence >= 1 && fence <= other.fence` 保证了只有合法创建过的 attempt 编号才会被放行，伪造的非数字、负数、0 或超出当前任务真实执行进度的超前编号（如 `a999`）会被准确拒绝。

#### (3) 任务名前缀碰撞（T-1 与 T-10、含连字符任务名）
- **内部隐藏引用**：前缀均显式带有尾部斜杠（`refs/a2a/attempts/${other.task_id}/` 与 `refs/a2a/verifications/${other.task_id}/`），字符 `/` 切断了 `demo+T-1/` 与 `demo+T-10/` 的前缀碰撞。
- **分支引用**：
  - 前缀带有后缀连接符 `refs/heads/a2a/${name}-`；
  - 针对 `T-1` 与 `T-10`：`refs/heads/a2a/T-10-a1` 在第 18 字符位是 `'0'` 而非 `'-'`，无法匹配 `T-1` 的前缀；
  - 针对含连字符的任务名（如 `proj-alpha` 与 `proj-alpha-extra`）：`proj-alpha-extra` 的分支剥离 `refs/heads/a2a/proj-alpha-` 前缀后剩余 `"extra-a1"`，随后经 `/^a(\d+)$/` 匹配因开头为 `"extra"` 而返回 `null`。因此即使任务名包含连字符，也不会被错误归属到较短同前缀的任务下。

#### (4) 本任务自身的引用隔离
- `others` 在查询时通过 `.filter(other => other.task_id !== task.task_id)` 显式排除了本任务；
- 内部隐藏引用因包含唯一的 `task_id`，绝不会匹配任何 `other`；
- 分支引用有前置守卫 `name !== taskName(task.task_id)`：本任务自身分支在任何比较分支下都求值为 `false`。审查期间若审查员或外部异常修改了本任务自己的分支，必报 `review_shared_refs_changed`，保证了审查对象的不可篡改性。

#### (5) 门禁合法写入引用的完备性审查
核对门禁核心生命周期内对 Git 引用的全部写操作：
- **新 attempt**：`refs/heads/a2a/<name>-a<N>` 正常放行；
- **清理后的隐藏引用**：`refs/a2a/attempts/<task_id>/a<N>` 正常放行；被删除的 attempt 分支在集合差集中因符合 `otherOwns` 正常放行；
- **验收引用（正常）**：`refs/a2a/verifications/<task_id>/a<N>/v<K>` 正常放行；
- **放弃（abandon）**：放弃时未执行清理，reclaim 后按普通 attempt 归档，正常放行；
- **冲突回写（conflict rework）**：**【存在误拒缺陷】**
  在 [`workbench/src/gates/core.ts:1792-1796`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L1792-L1796) 中，当并发的任务在验收合并发生冲突时，门禁会写入两个合法的冲突现场保留引用：
  - `refs/a2a/verifications/${taskId}/a${attempt.fence}/v${ordinal}-candidate`
  - `refs/a2a/verifications/${taskId}/a${attempt.fence}/v${ordinal}-base`
  这两个引用后缀为 `-candidate` 和 `-base`，被 [`core.ts:2566`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L2566) 的正则 `/^a(\d+)\/v\d+$/` 拒之门外，导致并发的正常审查会话在回收时被误拒（见后文【发现 1】）。

---

### 2. 审查 01 的 P2 与 P3 处理分析

#### (1) P2（放行规则过宽，前缀即放行）的解决情况
- 审查 01 指出：候选 1 仅校验 `startsWith` 前缀和正则捕获，任何伪造在他人命名空间下的引用（如 `refs/a2a/attempts/other/rogue`）都会被放行。
- 候选 2 方案：引入了结构化解析 `attemptOf`，并将 `fence` 约束在数据库真实记录的 `[1, other.fence]` 范围内，杜绝了任意名称和超前 attempt 编号的伪造。
- 结论：**P2 本身的核心安全隐患已解决**，但收紧正则时遗漏了合法冲突后缀（衍生出新的 P1 缺陷）。

#### (2) P3-1（同仓库两个项目有同名任务时的分支冲突）的处理
- 候选 2 在 [`workbench/README.md:462-463`](file:///Users/luckye/Documents/Code/a2a/workbench/README.md#L462-L463) 显式记录为已知边界：“*已知边界：……同一仓库登记为两个项目、且有同名任务时，对方的 attempt 分支与本任务同名，按引用被改拒收。*”
- 合理性评估：在底层 Git 仓库共享的场景下，Git 分支引用为平坦命名空间 `refs/heads/a2a/${name}-a${fence}`。若两个不同项目存在同名任务，在物理 Git 分支上本就会直接重名碰撞。在现有分支命名规范未引入 project 前缀的前提下，将其作为已知边界并在文档中明示，**处理合理**。

#### (3) P3-2（票文件不存在）的处理
- 候选 2 在 [`RESULTS.md:17`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-131/candidate-2/RESULTS.md#L17) 中称：“*“T-131 票文件不存在”是误报：票已在 `03b2d66a3` 提交。*”
- 核查事实：提交 `03b2d66a3` 仅在 [`.project-map/MAP.md:75`](file:///Users/luckye/Documents/Code/a2a/.project-map/MAP.md#L75) 中追加了一行索引描述，仓库 [`.project-map/tickets/`](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/) 目录下确实不存在独立的 `T-131-*.md` 文件。审查 01 指出的“缺少独立 ticket 文件”并非误报，而是两方对“切票”是否包含独立 md 文件的理解差异。此项不影响运行安全性（见后文【发现 2】）。

---

### 3. 测试与 RESULTS.md 审计

#### (1) 新反例与变异测试的辨别力
审查核对了 [`workbench/tests/test_t131_parallel_workers_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t131_parallel_workers_e2e.py)：
1. **反例 `foreign-other-task`**（行 95-96）：
   在 T-2 审查期间注入 `refs/a2a/attempts/demo+T-1/rogue`。在候选 2 下准确触发 `review_shared_refs_changed`，T-2 任务进入 `paused`，测试验证通过（`foreign-other-task.json: exit=0`）。
2. **变异 `other-namespace-prefix-only`**（行 86-87）：
   将校验逻辑还原为候选 1 的前缀匹配：
   `return fence !== null || ref.startsWith('refs/a2a/attempts/${other.task_id}/');`
   在此变异下运行 `foreign-other-task`，由于前缀匹配放过了 `rogue`，未能触发预期的拒绝，准确被测试断言捕获（`AssertionError: foreign_ref_during_review_refused: []`，`exit=1`）。确凿证明了反例与变异具备针对坏实现的辨别力。
3. **既有变异**：
   - `strict-ref-equality`：正确因 T-2 产生合法 verification 引用导致 T-1 回收超时失败（`exit=1`）；
   - `integration-chain-ignored`：正确因主分支正常 CAS 推进被拒导致 T-2 审查失败（`exit=1`）；
   - `any-ref-accepted`：正确因放过非法分支导致断言失败（`exit=1`）；
   - `red-parent`（基线 `03b2d66a3`）：正确因 `single_worker_slice` 限制导致第二 worker 无法启动（`exit=1`）。

#### (2) `RESULTS.md` 真实性核对
- [`evidence/2026-10-22-batch20/T-131/candidate-2/RESULTS.md`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-131/candidate-2/RESULTS.md) 中所列的 9 项运行状态、退出码与 [`e2e/exits.txt`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-131/candidate-2/e2e/exits.txt) 及各个 json/log 证据完全一致，未发现伪造、夸大或粉饰数据的情况。

---

## 二、发现项清单

### [P1] `workbench/src/gates/core.ts:2566`
- **文件与行号**：[`workbench/src/gates/core.ts:2566`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L2566)
- **发现说明**：`attemptOf` 对验证引用的正则匹配过于严苛（`/^a(\d+)\/v\d+$/`），遗漏了门禁在发生验收合并冲突时合法写入的现场保留引用。
- **具体失败场景**：
  1. 任务 A 与任务 B 在同一个共享 Git 仓库中并行工作；
  2. 任务 A 交付后进入独立审查阶段，审查开始时记录了当前的共享引用快照 `before`；
  3. 审查进行期间，任务 B 也提交了候选代码并由门禁执行 [`verifyCandidate`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L1702)；
  4. 任务 B 在与工作分支最新 HEAD 进行 `git merge` 时发生内容冲突（merge failed），门禁执行 [`core.ts:1792-1796`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L1792-L1796)，合法写入了保留引用：
     - `refs/a2a/verifications/${taskId_B}/a${fence_B}/v${ordinal}-candidate`
     - `refs/a2a/verifications/${taskId_B}/a${fence_B}/v${ordinal}-base`
  5. 此时任务 A 的审查员完成审查并请求回收（`reclaimReview`）；
  6. 门禁检查引用完整性 [`reviewRefsUnchanged`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L2553)，发现上述两个新增引用。进入 `attemptOf` 匹配时，`ref.slice(...)` 得到类似 `"a1/v1-candidate"` 与 `"a1/v1-base"`；
  7. 正则 `/^a(\d+)\/v\d+$/` 无法匹配带 `-candidate` 或 `-base` 的后缀，导致 `attemptOf` 返回 `null`，`otherOwns` 返回 `false`；
  8. 任务 A 的审查边界检查判定失败，抛出 `review_shared_refs_changed`，任务 A 的审查流程被非预期打断并陷入 `paused` 状态。
- **建议**：
  将 [`core.ts:2566`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L2566) 的正则表达式放宽支持可选的 `-candidate` 与 `-base` 后缀：
  ```typescript
  : ref.startsWith(`refs/a2a/verifications/${other.task_id}/`) ? /^a(\d+)\/v\d+(-(?:candidate|base))?$/.exec(ref.slice(`refs/a2a/verifications/${other.task_id}/`.length))
  ```
  并在 [`workbench/README.md:459-460`](file:///Users/luckye/Documents/Code/a2a/workbench/README.md#L459-L460) 文档中同步补充冲突保留引用的说明。

---

### [P3] `workbench/README.md:459-460`
- **文件与行号**：[`workbench/README.md:459-460`](file:///Users/luckye/Documents/Code/a2a/workbench/README.md#L459-L460)
- **发现说明**：文档中对共享引用放行格式的描述未包含冲突保留引用格式。
- **具体影响**：文档列出的三种格式为 `refs/heads/a2a/<任务>-a<N>`、`refs/a2a/attempts/<任务>/a<N>`、`refs/a2a/verifications/<任务>/a<N>/v<K>`，读者与后续审计者无法获知冲突场景下 `-candidate` 与 `-base` 的合法性。
- **建议**：配合 P1 修复，在文档中补全对冲突回写保留引用的说明。

---

### [P3] `evidence/2026-10-22-batch20/T-131/candidate-2/RESULTS.md:17`
- **文件与行号**：[`evidence/2026-10-22-batch20/T-131/candidate-2/RESULTS.md:17`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-131/candidate-2/RESULTS.md#L17)
- **发现说明**：报告指出“T-131 票文件不存在是误报，票已在 03b2d66a3 提交”。经核实，`03b2d66a3` 仅修改了 `MAP.md` 的索引行，`.project-map/tickets/` 下确实未按项目规范建立对应的 `T-131-*.md` 文件。
- **具体影响**：自动化工具或审计者沿 ticket 约定路径索引时会发生文件缺失。
- **建议**：建议更正此条说明，并按项目地图规范在 `.project-map/tickets/` 补齐 ticket 文档。

---

## 三、总体审查结论

# `INCOMPLETE`

### 理由
1. **P2 闭环及变异有效性成立**：候选 2 对他人引用的命名约束与 `fence` 上界判定逻辑严密，E2E 反例 `foreign-other-task` 及变异 `other-namespace-prefix-only` 确凿证明了其能有效拦截伪造的非法引用与退化实现，`RESULTS.md` 真实可信。
2. **存在合法场景误拒缺陷 [P1]**：`attemptOf` 中对验证引用的正则过度收紧为 `/^a(\d+)\/v\d+$/`，直接导致并发任务遭遇验收冲突时的合法保留引用（`v<K>-candidate` 与 `v<K>-base`）无法被识别为他人合法操作，从而将并发的审查会话错误打崩（误报 `review_shared_refs_changed`）。
3. **放行条件**：
   - 修复 [`workbench/src/gates/core.ts:2566`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L2566)，兼容 `-candidate` 与 `-base` 引用后缀；
   - 同步修正 [workbench/README.md](file:///Users/luckye/Documents/Code/a2a/workbench/README.md) 描述；
   - 增加针对并发冲突引用出现时不误拒的测试或断言验证。完成上述收敛后方可给出 `PASS`。
