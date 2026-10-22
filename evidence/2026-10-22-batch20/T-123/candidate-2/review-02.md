基于对提交 `a04c60a50`（T-123 候选 2，父提交 `f0188d772`，基线 `4116c8b44`）、候选间差异补丁、全量差异补丁及代码库当前文件的只读审查，逐项重点审查结论与具体分析如下。

---

### 重点 1：上一轮七条发现的处置核实

1. **第 1 条（P1：`contracts/a2aMembership.ts` 契约正则未同步更新）**：
   - **处置核实**：[taskIdPattern](file:///Users/luckye/Documents/Code/a2a/workbench/src/contracts/a2aMembership.ts#L9-L10) 统一定义并导出至 [`a2aMembership.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/contracts/a2aMembership.ts#L10)，[`A2ATaskMembership.taskId`](file:///Users/luckye/Documents/Code/a2a/workbench/src/contracts/a2aMembership.ts#L16) 直接引用该正则；[`qualityProtocol.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/qualityProtocol.ts#L2)、[`relay.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/relay.ts#L5) 与 [`core.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L14) 均通过 [`contracts/index.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/contracts/index.ts#L3) 统一种子正则，消除了契约层对包含 `+` 的任务 ID 的拒收隐患。**修复正确且完整。**

2. **第 2 条（P1：跨库两阶段提交中断后，成员资格库遗留旧 ID 且无法接续）**：
   - **处置核实**：[`workbench/src/gates/core.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L1082-L1083) 在扫描构建 `renamed` 时，补充了对 `this.membership.database` 中未含 `+` 记录的检索；新增了独立的断点恢复单元测试 [`test_t123_migration_resume.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t123_migration_resume.ts#L59-L63)，并用变异 `memberships-not-resumed` 证伪了坏实现。**修复正确且完整。**

3. **第 3 条（P2：`relay_requests.input` 中的 JSON 未纳入重写）**：
   - **处置核实**：[`workbench/src/gates/core.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L1115) 将 `column === "input"` 纳入 JSON 改写候选列；在单元测试中直接覆盖了 `relay_requests.input` 的任务字段重写，并由变异 `input-not-rewritten` 证伪了坏实现。**修复正确且完整。**

4. **第 4 条（P2：CLI 参数契约阻断 `--project`）**：
   - **处置核实**：[`workbench/src/gates/cli.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/cli.ts#L149-L151) 对所有非全局无任务的命令统配了 `...(!noTask ? ["task", "project"] : [])`；端到端测试 [`test_t123_project_identity_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t123_project_identity_e2e.py#L421-L425) 增加了经真实子进程调用 `status --task T-1-1 --project beta` 的断言，变异 `cli-refuses-project` 在 red-09 成功熔断。**修复正确且完整。**

5. **第 5 条（P2：`workbench_snapshot` 裸名与 launch 完整 ID 比较误拒）**：
   - **处置核实**：[`workbench/src/daemon.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L520) 改为使用解析后的 `result.task.task_id` 与 `record.task` 比对；端到端测试增加了 `snapshot_by_bare_name` 检查，变异 `snapshot-raw-name` 在 red-10 成功熔断。**修复正确且完整。**

6. **第 6 条（P2：历史 `card_draft_owned` 事件保留的不改理由核实）**：
   - **不改理由是否站得住：完全站得住。**
     - **规则一致性**：项目规则明确规定“门禁优先：运行记录追加写入”，审计日志物理 `DELETE` 会破坏不可变证据链；且票面 [T-123 Acceptance](file:///Users/luckye/Documents/Code/a2a/workbench/../.project-map/tickets/T-123-project-scoped-task-and-card-ids.md#L35) 明确要求“迁移前后的任务、卡片版本、事件条数一致”，物理删除会导致事件行数前后不符。
     - **语义澄清**：执行主控在票面实现方案中已将歧义文字明确修正为“删除 `card_draft_owned` 机制（不再写入、不再检查）；已有的 `card_draft_owned` 事件是追加式历史，原样保留”。
     - **假阳性测试修复**：候选 2 在修前旧版终端中真实保存了未建任务的草稿 `T-D`，产生了真实的历史事件；迁移后核实了该草稿归入 `legacy+T-D`、历史事件行数保持且后续无新写入，变异 `migration-ignores-drafts` 在 red-08 证明了草稿迁移路径已被有效行使。

7. **第 7 条（P3：`locks/` 旧锁文件不清理的不改理由核实）**：
   - **不改理由是否站得住：完全站得住。**
     - **文件锁安全**：SQLite / POSIX 文件操作锁（`BEGIN IMMEDIATE`）依赖锁定期间文件 inode 的绝对稳定，代码设计原则为“保留 inode，从不 unlink”，在运行或迁移期间动态 `unlink` 存在破坏互斥语义或引发孤立句柄的并发风险。
     - **无副作用**：迁移后新生成的任务操作锁严格采用 `locks/<project>+<name>.sqlite3` 路径，旧文件名 `locks/<旧名>.sqlite3` 永不再被引用，占用空间极小且不干扰任何互斥判定。

---

### 重点 2：迁移的续迁逻辑深度分析

1. **成员资格加入改名集合后，是否可能把任务库里已迁移的值再改一次**：
   - **结论：不可能。**
   - **分析**：
     - 若第一次迁移在 `this.db` 提交后、`this.membership.database` 提交前被异常打断，`this.db` 中所有任务相关列和 JSON 字段已经全部升级为形如 `p+T-0`；
     - 第二次启动时，`this.db` 检索 `instr(id, '+')=0` 返回空；`this.membership.database` 检索返回旧 ID `T-0`，从而在 `renamed` 中加入映射 `T-0 => p+T-0`；
     - 当 `migrate(this.db, ...)` 再次遍历 `this.db` 时，由于当前表中的字段值全为 `p+T-0`，而 `renamed` 的键集只有 `T-0`（不含 `p+T-0`）：
       - 普通列：`renamed.get('p+T-0')` 为 `undefined`，保持原值；
       - JSON 列：`rewrite()` 仅检查字段名为 `"task" | "task_id" | "taskId"` 且值命中 `renamed.has(item)` 的项。由于 `item` 是 `p+T-0`，`renamed.has('p+T-0')` 为 `false`，原值保持不变；`tasks.data.name` 字段名为 `"name"`，不属于改写字段，同样不被触碰；
       - 因此，对已迁移库的 DML 执行结果是严格的零变更（no-op）。

2. **任务库与成员资格的项目不一致时是否产生冲突**：
   - **结论：不会产生冲突。**
   - **分析**：
     - 行号 [`core.ts:1083`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L1083) 包含守卫 `if (!renamed.has(String(row.id)))`，如果某个任务 ID 已在 `tasks` 表登记，优先采用任务表声明的 `project_id`，成员资格库中的值不会覆盖该映射；
     - 在业务契约上，受管任务在创建及成员绑定时始终受门禁 `task.project_id === membership.projectId` 强校验约束，旧库中不存在合法的跨项目同名冲突。

3. **再次启动的幂等性**：
   - **结论：完全幂等。**
   - **分析**：两库均成功提交后，再次重启时 `tasks`、`memberships`、`task_card_versions` 均不满足 `instr(id, '+')=0`，`renamed.size === 0`，[`core.ts:1096`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L1096) 立即 `return`，不执行任何 DDL 事务或更新。[`test_t123_migration_resume.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t123_migration_resume.ts#L64-L67) 的 `second_start_changes_nothing` 断言对此提供了直接证据。

---

### 重点 3：新增与修改测试的独立性与证据核验

1. **测试独立性与证伪能力**：
   - **单元测试**（[`test_t123_migration_resume.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t123_migration_resume.ts)）：
     - 独立通过底层 SQLite 驱动初始化裸表数据，不依赖编排后台或 CLI 包装；
     - 覆盖“全量旧库冷迁”、“任务库迁完/成员库未迁的中断接续”、“已迁完成二次启动幂等”三种物理状态；
     - 变异 `memberships-not-resumed` 与 `input-not-rewritten` 均能精准阻断在对应场景断言，反事实证伪成立。
   - **端到端测试**（[`test_t123_project_identity_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t123_project_identity_e2e.py)）：
     - 覆盖双项目同名任务并行创建、跨项目写读拦截与操作记录审计、操作者无项目裸名歧义拒绝、CLI `--project` 参数透传解析、T-128 二次重启后的孤儿 Attempt 回收续跑、直至两项目独立集成到各自 Git 仓库；
     - 包含 9 个独立的端到端变异（`global-task-id`、`ambiguous-name-picks-first`、`gone-only-first-restart`、`full-id-ignores-project`、`migration-skips-events`、`migration-ignores-drafts`、`cli-refuses-project`、`snapshot-raw-name` 及修前父提交基线 `red-01-parent`），且均在预期断言点熔断退出 1。
2. **`RESULTS.md` 真实性核对**：
   - 逐项核对 `evidence/.../candidate-2/e2e/exits.txt`（17 项运行）与 `unit/exits.txt`（10 项运行）；
   - `green-01` 实际包含 22 个显式 `check` 检查点，与报告记录精确一致；
   - 夹具归档清单 [`fixtures.archive.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-123/candidate-2/fixtures.archive.json) 记录了 17 项完整归档，不存在夸大、伪造或与证据不符之处。

---

### 重点 4：全量改动审查发现清单

经对提交 `a04c60a50` 所涉及的契约、门禁核心、后台服务、窗格管理、中继、侧栏、界面渲染及测试用例的全文深度审查：
- **P0 / P1 / P2 / P3 发现**：**无**（明确确认没有遗留缺陷）。

---

### 总体结论

**PASS**

**评估结论**：
候选 2 完整且正确地修复了审查 01 提出的全部实质性缺陷，对历史审计日志保留与锁文件安全的工程决策具备充分的规范和事实支撑；数据迁移具备原子接续能力与严格幂等性；测试用例与坏实现变异独立且证伪充分，证据真实严密，满足合并准入标准。
