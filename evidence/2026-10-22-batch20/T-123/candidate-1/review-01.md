基于对提交 `f0188d772`（基线 `4116c8b44`）、差异补丁及代码库当前实现的只读审查，逐项重点审查结论与具体发现如下。

---

### 重点 1：任务解析与项目作用域隔离

1. **终端主控越界检查**：
   - 终端主控发起命令时，`workbench/src/daemon.ts`（第 248 行）将终端角色的 `roleRequest.project` 绑定至门禁调用者上下文 `actor.project`。
   - 门禁入口 `workbench/src/gates/core.ts` 的 `request()`（第 3482 行）统一调用 `this.resolveTask(decoded.task, decoded.project ?? actor?.project)`。
   - 若终端仅给裸名 `name`，由于 `project` 已被强制限定为终端所属项目，必然解析为 `${roleRequest.project}+${name}`，不可能触及另一项目的同名任务或卡片；
   - 若终端传入包含 `+` 的完整 ID（如 `beta+T-1`），`resolveTask()` 检查 `project === undefined || taskProject(full) === project`，因项目前缀不符直接抛出 `task_project_mismatch` 并在门禁事件流中留下失败记录；
   - 若终端在请求体中另传 `project` 字段且不等于自身所属项目，`daemon.ts`（第 244 行）在请求进入门禁前即拦截并拒绝（`role_project_mismatch`）。
   - 结论：**终端主控无法经由任何命令触及另一个项目的任务或卡片**。
2. **管理凭据裸名歧义处理**：
   - 管理凭据（operator）调用时不带 `actor.project`。在未显式提供 `--project` 的情况下，`resolveTask()` 检索所有后缀匹配该裸名的已有任务。
   - 若匹配数量恰为 1，正常解析；若匹配数量大于 1，明确抛出 `task_ambiguous` 并附带候选项所属的项目列表；若为 0（如尚未创建的新任务），有运行时环境抛出 `unknown_task`，仅在无运行时的测试夹具回退为同名默认值。
3. **完整 ID 与项目矛盾处理**：
   - 完整 ID 自带项目。若调用者在请求中额外给出与前缀不同的 `project`，`resolveTask()` 一律抛出 `task_project_mismatch`，绝不猜测或静默覆盖。
4. **移除 daemon.ts 前缀检查后的完整性**：
   - 所有受管任务命令（`taskCommands`）均要求 `input.task`。
   - `create` 命令在 `daemon.ts`（第 239 行）仍显式校验 `input.project === roleRequest.project`，缺省即拒绝；在门禁内部 `project_id` 直接取自 `taskProject(taskId)`，无论外部入参如何，项目属性强绑定完整 ID。
   - `run`、`attach`、`answer_issue`、`answer_issues` 等命令均走 `request()` 入口将 `args.task` 换成完整 ID 并加排他操作锁，不存在权限缺口。

---

### 重点 2：旧库迁移（`migrateTaskIds`）

1. **表与列的遍历**：
   - 迁移遍历了 `state.sqlite3` 中的所有非系统表，改写名为 `task` 的列及 `tasks.id`，并在 JSON 列中递归重写 `task`、`task_id`、`taskId` 与 `task:<名>` 引用。
   - `tasks` 记录成功补全 `name: parsed.task_id`，保留了旧裸名。
2. **幂等性与触发器**：
   - 重复执行时，由于已迁移数据的 `instr(id, '+') > 0`，`renamed.size` 为 0 直接退出，满足幂等。
   - 触发器在事务开始后先从 `sqlite_master` 暂存其 SQL 并 `DROP`，数据更新完毕后原样 `CREATE` 重建，事务异常时 SQLite 的 DDL 事务支持可保证回滚。
3. **无归属草稿的处理**：
   - 若草稿既未建任务也无历史 `card_draft_owned` 事件，迁移抛出 `task_migration_unowned_drafts` 阻止后台启动，不猜测归属，符合设计规范。
4. **发现的隐患**：
   - 详见后文发现 2（两库非原子迁移）、发现 3（`relay_requests` 遗漏改写）、发现 6（未物理删除 `card_draft_owned` 记录）与发现 7（`locks/` 孤立文件）。

---

### 重点 3：任务 ID 字符集统一

1. **统一正则与使用**：
   - `workbench/src/gates/qualityProtocol.ts` 导出了 `taskIdPattern = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\+[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/`。
   - `workbench/src/relay.ts` 与 `workbench/src/gates/core.ts`（`key()`）均统一引用该正则。
   - `workbench/hooks/prepare-commit-msg` 仅做非空和无换行检查，未限制字符集，尾注 `A2A-Task: <项目>+<任务名>` 生成正常。
   - `terminalCli.ts` 透传 JSON，不限制字符集。
2. **遗漏校验点**：
   - 详见后文发现 1（`a2aMembership.ts` 契约仍使用旧正则）。

---

### 重点 4：T-128（panes.ts 恢复循环）

1. **状态放宽与判定**：
   - `workbench/src/panes.ts`（第 463 行）将 `if (this.store.lastEvent(record.id, ["pane_recovered"])?.data.daemon !== daemon) continue;` 放宽为 `if (!this.store.lastEvent(record.id, ["pane_recovered"])) continue;`。
   - **不会把运行中的记录错当成已停止**：`registerGone()` 内通过 `/usr/bin/python3 processSnapshot.py` 严格轮询 `shell_pid` 与 `leader_pid` 最长 10 秒；若进程未退出，抛出异常并写入 `pane_gone_unconfirmed`，**不会**把 pane 置为 `stopped: true` 或加入 `this.panes`。
   - **不会处理已归档记录**：第 462 行显式跳过了包含 `pane_archived` 事件的记录。
   - **不会重复恢复 monitor**：第 461 行有 `if (this.panes.has(record.thread)) continue;`；若前次循环已恢复过，本次跳过；且 `restore()` 内部（第 512 行）在启动前通过 `process.kill(shell_pid, 0)` 确认前代进程无响应，不会出现重复进程。

---

### 重点 5：界面路由与同名任务显示

1. **同名任务不混淆**：
   - `workbench/src/sidebar.ts`：返回的 `agents` 行中，`task` 保留完整 ID，`task_name` 为裸名；项目列表按项目隔离展示子会话。
   - `workbench/app/renderer.tsx`：导航切换使用 `item.task_id`（完整 ID），头部显式展示 `${task.project_id} / ${task.name}`。
   - `workbench/app/FlowPage.tsx`：泳道 key 为 `lane.task`（完整 ID），标题同时展示 `{lane.name} · {lane.title}` 与 `{lane.project}`。
   - 内部操作、路由与选择器均绑定完整 ID 或 launch UUID，仅在展示文本上使用 `name`，不同项目的同名任务互不混淆。
2. **快照查询中的裸名缺陷**：
   - 详见后文发现 5（`workbench_snapshot` 和 `pane_layout` 未解析裸名）。

---

### 重点 6：测试独立性与证据核实

1. **变异与坏实现的证伪能力**：
   - 6 个红态变异（`global-task-id`、`ambiguous-name-picks-first`、`gone-only-first-restart`、`full-id-ignores-project`、`migration-skips-events` 及父提交基线）均能有效区分坏实现并在对应断言处熔断。
2. **对 T-121 / T-122 / T-124 测试的修改**：
   - T-121 测试将旧的 `card_draft_not_owned` 拒绝断言适配为 `task_project_mismatch`，并增加了同名任务草稿在两个项目中独立保存创建的互斥性断言，断言强度有所提升。
   - T-122 与 T-124 增加了 `task_name` 的验证，无削弱。
3. **证据真实性与夸大**：
   - 端到端及单元证据与 `RESULTS.md` 大体相符，但存在对 `card_draft_owned` 清理证据的夸大陈述（详见后文发现 6）。

---

### 审查发现清单

#### [P1] `workbench/src/contracts/a2aMembership.ts:13`
- **文件与行号**：`workbench/src/contracts/a2aMembership.ts` 第 13 行
- **具体失败场景**：
  `A2ATaskMembership` 的 Schema 定义仍保留旧的无 `+` 字符正则：
  ```ts
  taskId: TrimmedNonEmptyString.check(Schema.isPattern(/^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/)),
  ```
  尽管 `qualityProtocol.ts` 已经更新了 `taskIdPattern`，但此处未同步更新。如果未来或其他模块使用 `Schema.decodeUnknownSync(A2ATaskMembership)` 校验任务成员资格数据，所有符合 T-123 规范的新任务 ID（形如 `alpha+T-1`）均会抛出 Schema 校验失败（Refusal / ParseIssue）。
- **建议**：
  将该字段正则改为使用 `taskIdPattern` 或允许包含 `+` 的格式。

---

#### [P1] `workbench/src/gates/core.ts:391-392`
- **文件与行号**：`workbench/src/gates/core.ts` 第 391-392 行、第 339-353 行
- **具体失败场景**：
  数据迁移分两次独立事务执行：
  ```ts
  migrate(this.db, tables, { tasks: "id" });
  migrate(this.membership.database, ["memberships"], { memberships: "id" });
  ```
  由于 `state.sqlite3` 与 `membership.sqlite3` 是两个物理文件，若第一条 `migrate(this.db)` 提交后、第二条提交前发生进程异常或断电：下一次后台启动时，第 339 行检索 `tasks WHERE instr(id,'+')=0` 返回空集，第 348 行检索 `task_card_versions` 亦为空集，导致第 353 行 `if (!renamed.size) return;` 提前退出。
  此时 `this.membership.database` 将永久遗留未迁移的旧任务 ID，再无机会执行迁移，造成两库数据永久不一致。
- **建议**：
  将 `memberships` 表是否存在无 `+` 的记录也纳入 `renamed` 构建与前置判断条件中；或者在 `membership.sqlite3` 未迁移完成时记录迁移标志位，确保跨进程重启能够接续完成两库迁移。

---

#### [P2] `workbench/src/gates/core.ts:372`
- **文件与行号**：`workbench/src/gates/core.ts` 第 372 行
- **具体失败场景**：
  `migrateTaskIds` 在扫描表中需要 rewrite 的 JSON 字段时，过滤条件为：
  ```ts
  const json = columns.filter(column => column === "data" || column === "details");
  ```
  在 `relay_requests` 表中，请求入参 JSON 存储在 `input` 列中（见 `workbench/src/relay.ts` 第 33 行）。迁移时虽然更新了 `relay_requests.task` 普通列，但未能改写 `relay_requests.input` 字符串内的 JSON 字段（如 `task`）。虽然历史 relay 记录通常不影响后续运转，但这违反了票面关于“改写各表 JSON 里的 task 引用”的承诺。
- **建议**：
  将 `input` 列也加入 JSON 改写候选列中：`column === "data" || column === "details" || column === "input"`。

---

#### [P2] `workbench/src/gates/cli.ts:39-41, 58`
- **文件与行号**：`workbench/src/gates/cli.ts` 第 39-41 行、第 58 行等
- **具体失败场景**：
  CLI 参数契约表 `commands` 中，`card_validate`、`card_save`、`card_show`、`status`、`dispatch`、`run` 等命令未在 `optional` 数组中声明 `"project"`（仅 `card_template` 和 `create` 声明了 `"project"`）。
  `cli.ts` 第 154 行执行强校验：`Object.keys(values).some((key) => !allowed.includes(key))`。如果操作者在命令行上通过 `--project <项目> --task <裸名>` 调用 `status`、`card_save` 等命令，CLI 会直接抛出 `Error: invalid command arguments`。虽然底层门禁契约支持带 `project` 参数，但 CLI 入口将其阻断，导致操作者在 CLI 下无法使用“裸名 + `--project`”，必须手写完整 ID。
- **建议**：
  在 `cli.ts` 的 `commands` 中为所有需要 `task` 的命令将 `"project"` 补充到 `optional` 列表中。

---

#### [P2] `workbench/src/daemon.ts:523`
- **文件与行号**：`workbench/src/daemon.ts` 第 523 行
- **具体失败场景**：
  在 `workbench_snapshot` 命令中：
  ```ts
  const result = await gates.call({ command: "status", task: input.task });
  if (!result.ok || !result.task) return result;
  const record = input.launch ? panes.launchRecord(input.launch) :
    result.task.current_attempt?.thread_id ? store.threadLaunch(result.task.current_attempt.thread_id) : undefined;
  if (record && record.task !== input.task) throw new Refusal("launch_task_mismatch");
  ```
  如果调用者使用裸任务名 `input.task = "T-1"` 调用 `workbench_snapshot`，`gates.call` 会成功解析并将完整 ID 写入 `result.task.task_id`（如 `demo+T-1`）；而 `record.task` 中存储的是完整 ID。
  第 523 行直接使用原始未归一化的 `input.task` 进行比较：`record.task !== input.task`（即 `'demo+T-1' !== 'T-1'`），导致合法查询被误拒为 `launch_task_mismatch`。同理，第 330 行 `pane_layout` 构造 `layoutScope` 时直接拼接 `input.task` 也会因为未解析裸名而查不到对应的已保存布局。
- **建议**：
  第 523 行应改为比较归一化后的完整 ID：`if (record && record.task !== result.task.task_id) throw new Refusal("launch_task_mismatch");`。

---

#### [P2] `workbench/src/gates/core.ts:337-393` 与 `evidence/.../RESULTS.md:45`
- **文件与行号**：`workbench/src/gates/core.ts` 第 337-393 行，`evidence/2026-10-22-batch20/T-123/candidate-1/RESULTS.md` 第 45 行
- **具体失败场景**：
  T-123 票面要求：“草稿卡片按 card_draft_owned 归入项目，之后删除 card_draft_owned”。`RESULTS.md` 亦声称：“最终库里没有 card_draft_owned”。
  但检查 `migrateTaskIds()` 代码，没有任何针对 `orchestration_events` 中 `type='card_draft_owned'` 的 `DELETE` 操作。
  端到端测试 `test_t123_project_identity_e2e.py` 之所以通过 `check('no_draft_ownership_records', final['owned'] == 0)`，是因为其创建修前旧库的代码（第 1075 行）是通过 `operator`（管理凭据）调用 `card_save`，在旧版 `daemon.ts` 下根本不会触发写入 `card_draft_owned` 事件。因此迁移前 `owned` 计数就是 0，属于假阳性测试。如果历史库中曾由终端主控保存过草稿并产生过该事件，迁移后该记录依然存留在事件库中。
- **建议**：
  若架构要求保留不可变审计日志，应更新票面规格与 `RESULTS.md` 说明该事件仅作弃用保留而不物理删除；若确实需要清理，应在迁移事务中显式执行删除并补全真实含有该记录的迁移回归测试。

---

#### [P3] `workbench/src/gates/core.ts:275`
- **文件与行号**：`workbench/src/gates/core.ts` 第 275 行
- **具体失败场景**：
  门禁任务操作锁存储于 `this.root/locks/<task>.sqlite3`。旧任务在迁移为 `<project>+<name>` 后，新操作锁使用新文件名，但迁移并未清理或重命名 `locks/` 目录下的旧锁文件。虽不影响互斥锁机制，但会遗留未引用的垃圾文件。
- **建议**：
  在 `migrateTaskIds` 中增加对 `locks/` 目录下旧文件的清理或重命名逻辑。

---

### 总体结论

**INCOMPLETE**

**原因**：
核心的项目隔离逻辑与任务 ID 命名空间改造方向正确，端到端同名任务隔离与恢复机制基本成立；但存在 **[P1]** `a2aMembership.ts` 契约定义仍阻断新任务 ID、**[P1]** 两库迁移缺乏跨库原子性/断点重试保护可能导致元数据永久不一致，以及 **[P2]** CLI 参数阻断 `--project`、`workbench_snapshot` 裸名比对报错与草稿所有权记录清理未落实等实现与证据不严密之处，未达到候选合入标准，需完成上述缺陷修复后重新评估。
