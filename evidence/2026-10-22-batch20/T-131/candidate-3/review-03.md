# T-131 候选 3 独立复审报告：并发冲突现场保留引用放行与多 Worker 并行健全性

- **审查对象**：提交 [`d436fd390`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts)（父提交 `ea68df9d9`）
- **变更差异**：`/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/agy-t131c3-vfiE/full.diff`
- **执行模式**：严格只读独立审查（未运行任何 shell 命令，未创建/编辑文件，未提交代码，纯读文件工具查验）
- **依据规范**：[.project-map/tickets/T-131-parallel-workers-one-project.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-131-parallel-workers-one-project.md)、[review-02.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-131/candidate-2/review-02.md)、[workbench/README.md](file:///Users/luckye/Documents/Code/a2a/workbench/README.md)
- **总体结论**：**`PASS`**

---

## 一、四大重点核对结论

### 1. P1 缺陷修复与正则边界收紧审查
- **代码位置**：[`workbench/src/gates/core.ts:2567`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L2567)
  ```typescript
  : ref.startsWith(`refs/a2a/verifications/${other.task_id}/`) ? /^a(\d+)\/v\d+(?:-candidate|-base)?$/.exec(ref.slice(`refs/a2a/verifications/${other.task_id}/`.length))
  ```
- **正则结构核查**：
  1. **精确前缀与剥离**：必须以 `refs/a2a/verifications/${other.task_id}/` 开头，杜绝任务间命名空间跨越；
  2. **非捕获可选组**：`(?:-candidate|-base)?` 严格限定只能在无后缀、`-candidate` 或 `-base` 三者中选择，无法匹配诸如 `-candidate-extra`、`-candidate2`、`-other` 等非法后缀；
  3. **严格锚定**：首尾分别带有 `^` 与 `$` 锚定，不允许在末尾附加任何路径段或字符；
  4. **捕获索引不变性**：由于使用非捕获组 `(?:...)`，Attempt 编号提取捕获组依然是唯一的第 1 捕获组 `found[1]`（`^a(\d+)`），确保 `fence` 判定逻辑 `fence >= 1 && fence <= other.fence` 准确稳定；
  5. **核查结论**：**P1 已彻底修好**。放行范围严格且仅限制在门禁合法生成的 `-candidate` 与 `-base` 两个后缀，未向任何其他名称放宽。

---

### 2. 门禁全生命周期共享引用写入路径完备性核对
对 [`workbench/src/gates/core.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts) 全文（第 1 行至第 4233 行）所有调用 `update-ref`、`retainCommit` 及其他 Git 引用修改的逻辑进行了逐行排查：

| 引用写操作入口 | 源码行号 | 写入的引用格式 | `reviewRefsUnchanged` 对应放行规则 | 核查结果 |
| :--- | :--- | :--- | :--- | :--- |
| `claim`（任务认领） | [第 1575-1581 行](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L1575-L1581) | `refs/heads/a2a/<name>-a<N>` | 第 2568 行：`ref.startsWith('refs/heads/a2a/${name}-')`，匹配 `/^a(\d+)$/` 且序号有效 | **放行** |
| `cleanupAttempt`（Attempt归档） | [第 1312、1319 行](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L1312) | `refs/a2a/attempts/<task_id>/a<N>` | 第 2566 行：`ref.startsWith('refs/a2a/attempts/${other.task_id}/')`，匹配 `/^a(\d+)$/` | **放行** |
| `cleanupAttempt`（集成后删除分支） | [第 1327 行](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L1327) | 删除 `refs/heads/a2a/<name>-a<N>` | 第 2586 行：集合差集并入 `otherOwns(ref)` 检查，归属合法他人分支 | **放行** |
| `cleanupVerification`（验证归档） | [第 1372 行](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L1372) | `refs/a2a/verifications/<task_id>/a<N>/v<K>` | 第 2567 行：匹配 `/^a(\d+)\/v\d+(?:-candidate|-base)?$/`（无后缀形式） | **放行** |
| `verifyCandidate`（合并冲突保留） | [第 1795-1796 行](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L1795-L1796) | `…/v<K>-candidate` 与 `…/v<K>-base` | 第 2567 行：匹配可选组 `-candidate` 与 `-base` | **放行** |
| `advanceWorkBranch`（原子集成） | [第 2000、2012、4126 行](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L2000) | 推进 `task.integration_ref` | 第 2577-2587 行：核查 `events` 历史推进链 `head = intent.M` | **放行** |

其余所有 `worktree add`（包括第 1749、1751 行验证工作区、第 2109、2110 行红态工作区、第 2465 行审查工作区）均显式携带 `--detach` 参数，不创建任何 Git 引用。
- **核查结论**：**门禁内部所有涉及共享引用写入的合法路径均已 100% 覆盖，不存在任何遗漏或会被非预期误拒的合法写路径。**

---

### 3. `--retained-ref` 场景与红态证明力审计
- **红态可重现性验证**：
  - 证据记录：[`evidence/2026-10-22-batch20/T-131/candidate-3/e2e/red-candidate-2-retained.log`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-131/candidate-3/e2e/red-candidate-2-retained.log)
  - 运行命令：在基线父提交 `ea68df9d9`（候选 2）上挂载新测试并执行 `--retained-ref`；
  - 失败现场：`exit=1`，审查回收被拒，T-2 任务进入 `paused`，审查状态陷入 `unknown`：
    ```
    AssertionError: both_reviews_passed_on_their_own_task: {'T-1': {'task_state': 'verified', 'review': 'passed', ...}, 'T-2': {'task_state': 'paused', 'review': 'unknown', ...}}
    ```
  - 证明力：**真实入口准确捕获了候选 2 遗漏冲突保留引用的误拒缺陷**。
- **绿态修复验证**：
  - 证据记录：[`evidence/2026-10-22-batch20/T-131/candidate-3/e2e/retained-ref.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-131/candidate-3/e2e/retained-ref.json)
  - 运行特征：在 T-2 审查进行期间，使用 `git update-ref` 同时写入门禁命名规范下的 `v1-candidate` 与 `v1-base` 两个现场引用；
  - 结果：`exit=0`，10 项核心检查全数通过，T-1 与 T-2 均完成审查、打分并成功双双集成至主工作分支。
- **变异矩阵辨别力审计**：
  - `foreign-plain`（`exit=0`）：验证非法分支 `refs/heads/foreign` 仍能被可靠拦截；
  - `foreign-other-task`（`exit=0`）：验证他人任务命名空间下的伪造引用 `refs/a2a/attempts/demo+T-1/rogue` 仍能被可靠拦截；
  - `mutant-other-namespace-prefix-only`（`exit=1`）：证明前缀匹配等松懈退化实现必然被测试断言捕获。
- **核查结论**：**红态与对抗性变异证据严谨可信，确凿证明了修复的有效性与边界辨别力。**

---

### 4. README 文档与代码一致性审查
- **核对位置**：[`workbench/README.md:458-462`](file:///Users/luckye/Documents/Code/a2a/workbench/README.md#L458-L462)
  > “同一仓库里别的任务可以同时在跑（T-131），所以共享引用的核对放过两类改动：别的任务自己的引用，只认门禁给它起的名字（`refs/heads/a2a/<任务>-a<N>`、`refs/a2a/attempts/<任务>/a<N>`、`refs/a2a/verifications/<任务>/a<N>/v<K>`，以及验收冲突时保留现场的 `…/v<K>-candidate`、`…/v<K>-base`，N 不超过该任务当前的 attempt 序号）；工作分支经门禁记下的集成，从审查开始时的值一路推进到当前值。其余引用有任何改动都拒绝。已知边界：审查期间用户自己往工作分支提交，仍按引用被改拒收（T-131 之前就是这样）；同一仓库登记为两个项目、且有同名任务时，对方的 attempt 分支与本任务同名，按引用被改拒收。”
- **核查结论**：
  - 文档准确补齐了冲突保留引用的完整命名格式；
  - 描述的 Attempt 序号上界校验、工作分支事件回溯机制、已知物理边界与代码完全一致；
  - 候选 2 复审报告中的 P3 文档缺陷已完全闭环。

---

## 二、发现项清单（Defect Findings）

经只读深度核对，本轮候选 3 中**未发现任何 P0、P1、P2 严重度缺陷**。

上一轮复审中关于票据文件存在的疑虑经核实确认：[`.project-map/tickets/T-131-parallel-workers-one-project.md`](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-131-parallel-workers-one-project.md) 确实已在仓库中建立且内容完备，不构成缺陷。

---

## 三、总体审查结论

# `PASS`

### 验收通过理由
1. **P1 缺陷精准收敛**：[`core.ts:2567`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L2567) 采用非捕获组正则 `/^a(\d+)\/v\d+(?:-candidate|-base)?$/`，仅放行冲突现场保留引用，未向其他任意名称放宽，逻辑严密；
2. **门禁引用写路径全覆盖**：排查 `core.ts` 全部 4233 行中的所有 `update-ref` 与 `retainCommit` 调用，确认均已被放行规则完备覆盖，无任何新增误拒隐患；
3. **红绿态证据闭环**：以父提交 `ea68df9d9` 运行新测试重现了红态（`exit=1`，审查被拒），候选 3 在干净隔离 worktree 下绿态通过（`exit=0`，10 项全过），变异测试具备充分的坏实现辨别力；
4. **文档同步更新**：[`workbench/README.md`](file:///Users/luckye/Documents/Code/a2a/workbench/README.md) 精确描述了放行规则与已知边界，与代码完全一致。本候选满足集成门禁标准。
