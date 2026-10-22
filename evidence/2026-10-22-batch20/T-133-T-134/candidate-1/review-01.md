# T-133 与 T-134 候选变更独立审查报告

**审查范围**：
- 候选提交：`39af9b9b3`、`e4d45c511`（基于父提交 `7dd585c92`）
- 审查比对依据：`/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/agy-t133-stE1/full.diff`
- 规范与需求：[.project-map/tickets/T-133-user-input-records-view.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-133-user-input-records-view.md)、[.project-map/tickets/T-134-metrics-views.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-134-metrics-views.md)、[.project-map/specs/native-cli-orchestration-2026-10-10.md](file:///Users/luckye/Documents/Code/a2a/.project-map/specs/native-cli-orchestration-2026-10-10.md) 第 8 节
- 运行结果与摘要：[evidence/2026-10-22-batch20/T-133-T-134/candidate-1/RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-133-T-134/candidate-1/RESULTS.md) 及 `candidate-1/e2e/`

---

## 一、重点专项审查意见

### 1. `metrics.ts` 口径与计数审查（对照 Spec 第 8 节与 T-134）
- **模型实际观察值与 unknown 单列**：
  - Claude 会话实际模型和强度来自 `orchestration_events WHERE type='native_turn_facts'` 中的 `data.model` 与 `data.effort`；
  - Codex 会话从 `orchestration_events WHERE type='native_record' AND json_extract(data,'$.record.type')='turn_context'` 的 `payload.model` 与 `payload.effort ?? payload.reasoning_effort` 提取；
  - 均不采用启动或任务卡上的请求值（`model_requested`）；未产生回合事实或观察不到的会话（如终端主控）明确单列为 `unknown`。口径符合要求。
- **一次到位率定义**：
  - 严格限定为：在集成结果为“通过”的 attempt 中，同时满足 `delivery_rounds === 1`、`human_interventions === 0` 且各项检查项打回次数全为 0 的占比；
  - 打回原因按门禁的 8 个检查项（`identity_version`、`path_boundary`、`oracle`、`completion`、`red_state`、`rule_checks`、`independent_review`、`commit_trailers`）分别汇总累加。口径符合要求。
- **注意力消耗口径**：
  - 答题（`answers`）：取 `user_inputs` 中 `form === 'answer'` 且非 `ui-derived`、非 `gap` 的记录数；
  - 审批（`approvals`）：取 `form === 'approval' || form === 'denial'` 记录数；
  - 介入（`interventions`）：取 `orchestration_events` 中 `turn_submit_intent` 且 `source: 'user'`（用户在受管窗格中按回车提交一轮交互）的次数，避免将窗格中单次击键当成介入；
  - 叫停（`stops`）：取门禁 `events` 中的 `emergency_interrupt_intent`（紧急中断）与 `orchestration_events` 中 `terminal_input_write_intent` 写入 `char(27)`（用户按 `Esc` 键）的次数之和。口径符合要求。
- **打分汇总**：
  - 维度为 `CLI × 实际模型 × 强度 × 任务类型`，统计 attempt 总数、结果分布（通过/放弃/升级）及边界纪律与工程品味的平均值。口径符合要求。
- **无数据与过滤处理**：
  - 没有数据时返回 `null` 或空数组，前端统一展示为 `<span className="metric-none">无数据</span>`，未填充 0。

### 2. `userInputRecords.ts` 与记录页（对照 T-133 与门禁规则）
- **人工介入标记一致性**：
  - 门禁派生 `human_intervention` 的规则是：输入满足 `input.target.attempt && input.target.task && input.channel !== 'ui-derived' && input.form !== 'gap'`，并在 `events` 表中记录事件，其 `details.input_id` 绑定 `user_inputs.id`（包括窗格输入与问题面板答复）；
  - `userInputRecords.ts` 直接通过 `SELECT seq, json_extract(details,'$.input_id') FROM events WHERE type='human_intervention'` 关联，将对应事件的 `seq` 赋予 `record.intervention`；
  - 前端据此渲染 `record-intervention` 徽标。派生标记与门禁事件严格一致，**不存在漏标或多标**。
- **输入展示与过滤**：
  - 控制按键（回车、换行、Esc、退格、Tab、Ctrl-C 等）转换为中文按键提示（如 `（按键：回车）`），避免空白行；
  - 提供了按任务、会话的双重过滤联动，过滤准确。

### 3. 只读命令与错误展示
- **只读保证**：
  - `user_input_records` 和 `metrics` 已列入 `daemon.ts` 的 `readOnly` 命令集；
  - 后端实现仅使用 `SELECT` 查询，没有任何写事务、表修改或临时表操作，是绝对的纯只读命令。
- **读取失败不显示为空**：
  - 前端 `MetricsPage.tsx` 与 `RecordsPage.tsx` 在 IPC 请求 reject 时捕获异常并设置 `error` 状态；
  - 渲染层在 `error` 存在时渲染带 `role="alert"` 的错误提示，且由于条件阻断，绝不渲染“无数据”或空表格。测试变异 `mutant-error-shown-as-empty` 验证有效。

### 4. 测试独立性与变异有效性
- **独立期望**：
  - 测试脚本开头的期望值由设计者基于 T-1、T-2、T-3 三个夹具场景独立手算推导（一次到位率 0.333、打回 completion 1 次、注意力 T-2 各 1 次、模型为本地 mock 服务的实际回值 `SERVED_MODEL`、打分均值等），不依赖被测代码输出；
- **变异有效性**：
  - `intervention-unmarked`（记录页不标介入）：成功被捕获；
  - `requested-as-observed`（请求模型冒充实际模型）：成功被捕获；
  - `intervention-ignored`（忽略介入算作一次到位）：成功被捕获；
  - `error-shown-as-empty`（读取失败显示为无数据）：成功被捕获；
  - `red-parent`（父提交运行）：因无命令失败，证明了新代码引入的行为增量。

### 5. RESULTS 中 T-133 判定为 INCOMPLETE 的理由
- **判定充分成立**：
  - T-133 验收条件明确要求“夹具里用户在主控终端和受管 worker 窗格各打一段字……视图列出三条”；
  - 实际实现中，项目终端主控（`role === 'shell'`）目前只转发输入而不记录到 `user_inputs`，导致主控终端的输入未被持久化，测试中探针 `terminal_input_recorded: false`；
  - 依照项目规则“严禁将未完成项四舍五入为 PASS”，由于核心验收项未达成且需要用户裁定记录方案，RESULTS.md 记为 `INCOMPLETE` 完全合规且诚实。

---

## 二、发现与问题清单（Findings）

### [P1] 终端主控输入未持久化导致用户输入记录页缺失主控原话
- **位置**：[workbench/src/daemon.ts#L433-L446](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L433-L446)
- **严重度**：P1
- **失败场景**：
  在项目终端中运行的主控 CLI（`role === "shell"`），用户在窗格内键入的指令仅由 `panes.shellInput` 转发到终端 PTY，并未调用 `recordInput` 写入 `gates.appendUserInput`。因此，用户亲手发给主控的指令完全没有进入 `user_inputs` 表，记录页无法呈现主控会话的用户输入，直接导致 T-133 验收条件第一条不通过。
- **说明**：此项已在 RESULTS.md 中如实列出，需由用户裁定方案（如通过 CLI 的 hook 采集整句输入，或记录批准后的窗格键入）。

### [P2] 模型使用视图（Model Use）以会话创建时间过滤，导致跨时间窗口会话的回合数统计失真
- **位置**：[workbench/src/metrics.ts#L344-L386](file:///Users/luckye/Documents/Code/a2a/workbench/src/metrics.ts#L344-L386)
- **严重度**：P2
- **失败场景**：
  在 `metricsSnapshot` 中，`observed` 是全局按 `launch` 统计该 session 的所有 turn。而在筛选 `sessions` 时：
  ```ts
  .filter(record => inRange(record.created_at, record.project))
  ```
  如果某个常驻终端主控会话在 `since` 之前就已经打开，但在查询时间段内产生了大量 turns，该会话会被完全过滤掉，导致该时间段内的模型使用量完全漏计；反之，若会话在时间段内创建并持续运行到 `until` 之后，`session.turns` 统计的却是该会话包含 `until` 之后的全部回合。
- **改进建议**：模型使用统计若要严格支持时间范围，回合数应按 `orchestration_events` 发生时间落入 `[since, until)` 统计，或者在界面上明确提示“会话与回合数按会话创建时间归档”。

### [P2] 注意力消耗统计跨多 Attempt 任务时指标绑定与展示语义轻微混淆
- **位置**：[workbench/src/metrics.ts#L402-L413](file:///Users/luckye/Documents/Code/a2a/workbench/src/metrics.ts#L402-L413)、[workbench/app/MetricsPage.tsx#L89](file:///Users/luckye/Documents/Code/a2a/workbench/app/MetricsPage.tsx#L89)
- **严重度**：P2
- **失败场景**：
  计算 `attention` 时，通过 `score.task`（任务 ID）统计该任务下所有的 `user_inputs`、`turn_submit_intent` 和叫停事件，属于整个任务生命周期的总消耗。但返回结构为 `{ task: score.task, attempt: score.attempt, ... }`，并将该集成通过的 attempt_id 返回，前端表格渲染使用 `key={row.attempt}`。
  当一个任务经历了 Attempt 1（被打回/升级）和 Attempt 2（集成通过）时，数据显示的是整个任务在两次 attempt 中的总注意力和最终的 attempt_id，未在表头或数据字段中显式标明为“任务全周期累计消耗”，可能引起对具体单次 attempt 消耗的误判。

### [P3] Codex 实际模型提取缺少真实端到端测试覆盖
- **位置**：[workbench/tests/test_t133_t134_records_metrics_e2e.py#L634-L663](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t133_t134_records_metrics_e2e.py#L634-L663)
- **严重度**：P3
- **失败场景**：
  端到端夹具中仅接入了 Scripted Claude Worker，Codex 的 `native_record`（`turn_context` 解析 `payload.model` 和 `payload.effort`）逻辑虽然已编写，但未在自动化测试中跑过真实或脚本化的 Codex 日志链路。

### [P3] 记录页层级目前仅支持平铺下拉级联，未实现树形结构展开
- **位置**：[workbench/app/RecordsPage.tsx#L156-L163](file:///Users/luckye/Documents/Code/a2a/workbench/app/RecordsPage.tsx#L156-L163)
- **严重度**：P3
- **失败场景**：
  记录页当前通过任务下拉框与会话下拉框实现了二级级联筛选，满足查找需求，但尚未形成“项目 → 任务 → 会话”的树状视图展示。

---

## 三、审查结论

| Ticket | 结论 | 理由摘要 |
|---|---|---|
| **T-133** | **INCOMPLETE** | 记录页及人工介入派生逻辑正确，只读保证与错误展示完整；但受限于项目终端（shell）当前未接入输入持久化，主控终端原话无法进入用户输入记录，验收条件第 1 条未完全满足。保持 INCOMPLETE 符合项目规范，待用户裁定方案。 |
| **T-134** | **PASS** | 四个指标视图（模型使用、一次到位率与打回原因、注意力消耗、打分汇总）计算口径严格符合 spec 与 ticket，模型取实际观察值、unknown 单列、无数据不填 0、只读不写库、测试预期独立手算且变异用例充分有效。已满足验收条件。 |
