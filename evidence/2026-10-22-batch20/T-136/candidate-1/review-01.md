# T-136 候选 1（提交 `01e0effd7`）独立审查报告

本审查以 `full.diff`、任务卡、项目规格（`.project-map/specs/native-cli-orchestration-2026-10-10.md` 第 8 节）、运行证据（`evidence/2026-10-22-batch20/T-136/candidate-1/`）为准，采用只读方式进行核对。

---

## 审查重点核对结论

### 1. 复盘会话的写入范围是否受限于 `out/`（Claude 与 Codex Confinement）
- **Claude Code**：
  - 经由 `retrospectiveArgv`（[`retrospective.ts:610-620`](file:///Users/luckye/Documents/Code/a2a/workbench/src/retrospective.ts#L610-L620)）注入 `--permission-mode dontAsk`、`--setting-sources ""`（防止加载项目或用户的配置），并在 `--settings` 中限制：
    - `permissions.allow: ['Bash', 'Read', 'Glob', 'Grep', 'Edit(/${run.out}/**)']`，`permissions.deny: ['Edit(/${run.repo}/**)']`；
    - `sandbox.filesystem: { allowWrite: [run.out], denyWrite: [run.repo] }`，`allowUnsandboxedCommands: false`。
  - 由于未设置 `excludedCommands`，所有的 Bash 命令强制在沙箱内运行，无法借助 `git commit` 或外部 shell 重定向逃逸写项目目录；测试中使用 `Write` 工具写项目被权限拦截，使用 `Bash` 工具写项目被沙箱拦截。变异 `out-not-confined` 证明去掉了该限制后 shell 重定向确实会写进项目（`rc=0`）。
- **Codex**：
  - 启动参数配置为 `-C run.out`、`--sandbox workspace-write`、`-c projects={...={trust_level="trusted"}}`、`-c sandbox_workspace_write.network_access=false`、`-a never`。工作区定位在 `out/`，写权限被沙箱严格限制在工作区内，网络访问被禁用，且仅在本次临时会话内信任该空目录，不污染用户全局 Codex 配置。
- **结论**：写入范围约束严密，无绕过路径。

### 2. 复盘包的时间范围与内容是否与库一致
- **时间范围契约**：[`retrospective.ts:540`](file:///Users/luckye/Documents/Code/a2a/workbench/src/retrospective.ts#L540) 定义 `inRange(time) = (!since || time >= since) && time < until`（左闭右开区间 `[since, until)`），下一次复盘的 `since` 取上一次复盘的 `until`，时间切片无缝且无交集。
- **内容完整性**：
  - `tasks`、`gate_checks`、`rejections`、`reviews`、`scores`、`issues`、`panel`、`user_inputs`、`commit_trailers`、`metrics` 均依据库内记录与 Git 历史正确提取，未带尾注的提交被单独计数。
- **边界缺陷**：发现 `trajectory_archive` 字段未按 `[since, until)` 进行时间过滤，导致该项目所有历史会话的归档路径均被泄露到包中（见发现 1）。

### 3. 周期判定（due）逻辑
- **周期状态**：存储在追加式 SQLite 表 `retrospective_schedule` 中，保存时更新 `effective_from = now`。
- **时间槽位判定**：
  - `!schedule.enabled` 时直接返回 `null`，关闭后绝不启动（变异 `schedule-fires-when-disabled` 已验证）；
  - `due()`（[`retrospective.ts:439-449`](file:///Users/luckye/Documents/Code/a2a/workbench/src/retrospective.ts#L439-L449)）计算当地时间对应星期的槽位，若槽位早于 `effective_from` 则不触发，防止历史漏跑补发；
  - `startRetrospective` 在 `prepare()` 阶段即同步将包含 `scheduled_for` 的记录持久化，同一槽位再次检查时 `this.runs(project).some(...)` 必定匹配，不会发生重复启动。
- **异常边界缺陷**：若 `startShell` 在 PTY 启动时抛出异常，由于 `prepare()` 已将槽位写入库，会导致后续 tick 误认为该槽位已执行而不再重试（见发现 2）。

### 4. 导入是否可能重复导入、丢建议或静默卡住
- **重复导入**：[`retrospective.ts:489`](file:///Users/luckye/Documents/Code/a2a/workbench/src/retrospective.ts#L489) 先核对 `imported` 事件，已导入的跳过；导入成功后追加 `imported` 事件，且 `importFinished()` 是同步执行，无并发交叉风险。
- **建议格式容错**：同时支持 `[...]` 数组与 `{ suggestions: [...] }` 对象，空标题自动过滤。
- **静默卡住**：若 `suggestions.json` 解析失败或不是数组，调用 `failOnce` 记录 `import_failed`，并在前端展示明确的错误文案（如 `suggestions.json 不是合法 JSON`），文件修好后下次 tick 自动重试（变异 `import-failure-silent` 已验证）。
- **事务缺陷**：文件复制与建议逐条插入 SQLite 未包裹在事务中，若中间故障重试可能导致建议行重复（见发现 3）。

### 5. 只读命令是否写库
- [`daemon.ts:320`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L320) 将 `retrospective_list` 列入 `readOnly` 命令白名单。
- `retrospective_list` 内部仅调用 SQLite 的 `SELECT` 语句查询 schedule、runs、events 与 suggestions，无任何写库、写盘或触发 `importFinished()` 的副作用。
- 其余写命令（`retrospective_start`、`retrospective_schedule_save`、`retrospective_tick`、`retrospective_decide`）均强制要求 `operator_required`。

### 6. 测试期望的独立性与变异证明
- [`test_t136_retrospective_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t136_retrospective_e2e.py) 中的期望值均直接基于场景常量（如 `FILES`、`ISSUE`、`ANSWER`）独立计算，非简单回读实现的生成内容。
- 变异矩阵设计严密：
  - `red-parent`（基线父提交 `1dc2b76c3`）：证明修前版本无复盘功能；
  - `mutant-package-ignores-range`：证明未按范围过滤会导致二次复盘包含旧任务；
  - `mutant-out-not-confined`：证明缺少沙箱与权限配置会导致 shell 写入项目目录；
  - `mutant-schedule-fires-when-disabled`：证明关闭定期复盘时确实不触发；
  - `mutant-import-failure-silent`：证明解析失败时必须向界面显式上报错误；
  - `mutant-archive-source-not-isolated`：证明单个未决源失败不会阻塞归档。
- 全部 5 个变异均精准被杀，退出码均为 1。

### 7. 附带修复项审查
- **T-135 审查 01 的 P2 修复**（[`trajectoryArchive.ts:685-690`](file:///Users/luckye/Documents/Code/a2a/workbench/src/trajectoryArchive.ts#L685-L690)）：将单源同步复制抽离为 `copy(source)` 并放入 `try ... catch`，单个不可读源的失败被独立记录在 `trajectory_archive_failed` 且去重，不阻断后续会话的轨迹归档。回归测试 `t135-green` 通过。
- **T-132 审查 02 的 P3 修复**（[`renderer.tsx:253-256`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L253-L256) 与 [`IssuesPage.tsx:12`](file:///Users/luckye/Documents/Code/a2a/workbench/app/IssuesPage.tsx#L12)）：为 `issues`、`records`、`metrics`、`retrospective` 页面外层统一附加 `key={selectedProject ?? ''}`，切换项目时利用 React 卸载重建机制彻底重置状态，去除了组件内易引起竞态的 `setTasks(null)`。回归测试 `t132-green` 通过。

---

## 发现项清单（Findings）

### 发现 1：复盘包中的 `trajectory_archive` 缺少时间范围过滤
- **文件与行号**：[`workbench/src/retrospective.ts:550-555`](file:///Users/luckye/Documents/Code/a2a/workbench/src/retrospective.ts#L550-L555)
- **严重度**：P2
- **失败场景**：
  在 `retrospectivePackage()` 中，`tasks`、`gate_checks`、`issues`、`commit_trailers` 等均经过 `inRange` 或 `since/until` 过滤；然而 `launches` 与 `trajectory_archive` 仅按 `project === project` 进行匹配，未作时间范围过滤。当项目运行数月、积累大量历史任务时，每次复盘包中的 `trajectory_archive` 都会包含该项目历史所有 session 的归档记录，造成上下文膨胀并泄露时间范围外的旧数据。

### 发现 2：`prepare()` 预置运行记录导致 `startShell` 失败时槽位漏跑且永久“进行中”
- **文件与行号**：[`workbench/src/daemon.ts:286-295`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L286-L295)
- **严重度**：P2
- **失败场景**：
  在 `startRetrospective` 中，`retrospectives.prepare()` 同步向 SQLite 插入了带有 `scheduled_for` 的运行记录。若随后的 `panes.startShell()` 因系统资源耗尽（PTY 达到上限）或工作目录异常而抛错：
  1. 当前 tick 终止，该项目此槽位被记录在库；
  2. 下一分钟再次 tick 时，`due()` 查询 `this.runs(project).some(run => run.scheduled_for === slot.toISOString())` 为 true，认为该槽位已执行，直接返回 `null`；
  3. 前端复盘记录列表中该次 run 因无 `started`、`import_failed` 或 `imported` 事件，永久显示为“进行中”，且本周的定期复盘被静默漏过。

### 发现 3：`importFinished()` 中的建议入库与完成事件缺少事务保护
- **文件与行号**：[`workbench/src/retrospective.ts:504-512`](file:///Users/luckye/Documents/Code/a2a/workbench/src/retrospective.ts#L504-L512)
- **严重度**：P3
- **失败场景**：
  在 `importFinished()` 中，`copyFileSync(report, destination)`、`list.forEach(item => INSERT INTO retrospective_suggestions...)` 以及 `this.record(run.id, 'imported', ...)` 均直接执行，未包裹在 `BEGIN IMMEDIATE ... COMMIT` 事务中。若在插入多条建议的过程中发生写入异常（如磁盘满），部分建议已持久化但 `imported` 事件未生成；下次 tick 重试时，由于缺少 `imported` 事件会重新执行，为已插入的建议重新生成 UUID 并再次插入，造成建议重复。

### 发现 4：Codex 复盘会话未接入轨迹归档
- **文件与行号**：[`workbench/src/daemon.ts:291-292`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L291-L292)、[`workbench/src/trajectoryArchive.ts:57-62`](file:///Users/luckye/Documents/Code/a2a/workbench/src/trajectoryArchive.ts#L57-L62)
- **严重度**：P2
- **失败场景**：
  当用户在界面或定期配置中选择使用 Codex 执行复盘时，`daemon.ts` 记录的 `retrospective_started` 事件中 `native_session` 与 `native_home` 均为 `null`。而在 `trajectoryArchive.ts` 中，仅处理了 `claudeTranscript`。因此 Codex 复盘会话的原生 rollout 无法被 `trajectoryArchive` 捕获并增量压缩归档到 `archive/` 目录，破坏了 spec 第 8 节中“后台把它启动的每个会话的原生记录增量复制”的契约。

---

## 总体结论

**INCOMPLETE**

### 判定理由
1. **真实 Haiku 运行证据缺失**：依据候选自带的 [`RESULTS.md:5,69-71`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-136/candidate-1/RESULTS.md#L5-L71)，候选提交人明确将结论标记为 `INCOMPLETE，等真实 haiku 运行与独立审查`，`real-haiku/commands.sh` 尚待补充。依据项目规则（不能将未完成的检查进位为 PASS），在真实运行产物落地前不可判定为 PASS。
2. **代码逻辑缺陷**：存在 P2 级别缺陷需修复（复盘包中的 `trajectory_archive` 范围越界过滤缺失、启动失败时的槽位防重失效与死锁状态、Codex 轨迹归档缺失）。修复后需连同真实 Haiku 运行证据再次审查。
