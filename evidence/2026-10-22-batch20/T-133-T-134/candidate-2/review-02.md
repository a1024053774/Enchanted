# T-133 与 T-134 候选 2 独立审查报告

**审查范围**：
- 候选提交：`8a8e1720c`（基于候选 1 提交 `e4d45c511`）
- 改动依据：`/private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/agy-t134c2-ktxs/full.diff`
- 审查材料：上一轮审查报告 [review-01.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-133-T-134/candidate-1/review-01.md)、候选 2 结果 [RESULTS.md](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-133-T-134/candidate-2/RESULTS.md) 及运行摘要 [candidate-2/e2e/](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-133-T-134/candidate-2/e2e/)
- 规范与需求：[.project-map/tickets/T-133-user-input-records-view.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-133-user-input-records-view.md)、[.project-map/tickets/T-134-metrics-views.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-134-metrics-views.md)、[.project-map/specs/native-cli-orchestration-2026-10-10.md](file:///Users/luckye/Documents/Code/a2a/.project-map/specs/native-cli-orchestration-2026-10-10.md) 第 8 节

---

## 一、重点专项审查意见

### 1. 两条 P2 问题修复与时间范围口径审查

#### ① 模型使用视图时间范围筛选（原 P2 #1）
- **修复方案核验**（[metrics.ts#L11-L47](file:///Users/luckye/Documents/Code/a2a/workbench/src/metrics.ts#L11-L47)）：
  - 回合筛选：遍历 `native_turn_facts`（Claude）与 `native_record`（Codex `turn_context`）时，增加 `if (!inTime(String(row.time))) continue;` 过滤，严格只将发生时间在 `[since, until)` 半开区间内的回合累加至 `observed`；
  - 会话包含：由原先仅按 `inRange(record.created_at, record.project)` 筛选改为 `(!range.project || record.project === range.project) && (inTime(record.created_at) || observed.has(record.id))`；
  - 回合数输出：取 `facts?.turns ?? 0`，仅呈现范围内实际发生的回合数。
- **漏计与重复审查**：
  - **漏计审查（无漏计）**：
    - 在时间范围前创建、但在范围内产生过回合的长期会话，因其产生过符合时间的回合而存在于 `observed` 中，必然被纳入会话列表，且回合数准确反映时间窗口内的量，原“跨范围会话被整体漏掉”的问题已彻底解决；
    - 在时间范围内新创建但尚未发生回合（或空闲/待命）的会话，因 `inTime(record.created_at)` 为真而被保留，展现为 `model: 'unknown', turns: 0`，不漏计新建立的会话。
  - **重复审查（无单次快照重复，回合数无重复）**：
    - 单次查询快照内，`launch_records` 主键唯一，每个会话最多返回一行；Claude 与 Codex 的回合事实来源互斥，同一个回合不会被重复计算；
    - 回合数采用严格的左闭右开区间 `(!range.since || time >= range.since) && (!range.until || time < range.until)`，对于连续相邻的时间切片 `[T0, T1)` 与 `[T1, T2)`，在 `T1` 处严格互斥，回合数代数可加（总和严格守恒，无交叉重复）；
    - 跨窗口连续运行的长期会话在每个有活动的窗口均作为该窗口的活跃会话（active session）出现，属于合理的时间窗口活跃统计口径（需注意会话数与 DAU 类似，跨时间切片不能直接简单相加）。

#### ② 注意力消耗跨 Attempt 任务的指标绑定与展示（原 P2 #2）
- **修复方案核验**（[MetricsPage.tsx#L8-L15](file:///Users/luckye/Documents/Code/a2a/workbench/app/MetricsPage.tsx#L8-L15)）：
  - 界面新增明确口径说明：“每个集成的任务一行，数的是这个任务全部 attempt 的累计。”；
  - 表格行的 React key 由原来的 `key={row.attempt}` 改为 `key={row.task}`，与任务级全生命周期聚合语义完全对齐。原展示语义轻微混淆已消除。

---

### 2. 新测试与变异有效性审查

- **独立期望与测试切面**（[test_t133_t134_records_metrics_e2e.py#L363-L386](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t133_t134_records_metrics_e2e.py#L363-L386)）：
  - 测试在 T-2 任务的 worker 启动并执行部分回合之后、用户介入前精准记录时间戳 `report['t_mid']`；
  - 随后测试分别拉取全局指标与 `since=report['t_mid']` 的切片指标，对 T-2 worker 会话断言：`len(part) == 1 and 1 <= part[0]['turns'] < whole['turns']`。
- **红态与反事实证明**：
  - **红态回测（`red-candidate-1-range`，基于父提交 `e4d45c511`）**：在候选 1 的代码上运行该测试，由于候选 1 仅按创建时间过滤，在 `t_mid` 前创建的 T-2 worker 被彻底过滤排除，`part` 为空，准确命中断言失败：
    `AssertionError: range_counts_turns_in_range: {'whole_turns': 4, 'part': []}`（退出码 1）；
  - **变异用例（`mutant-range-by-created-only`）**：将候选 2 的过滤条件变异回仅按 `inTime(record.created_at)`，同样精准捕获到 `part: []` 并失败退出（退出码 1）；
  - **候选 2 绿态运行（`green`）**：全量 14 项检查全绿，T-2 worker 在全量下为 4 回合，在 `since=t_mid` 范围内为 3 回合（`1 <= 3 < 4`）。
- **结论**：新测试能够确切证明对原 P2 缺陷的修复，变异与红态控制充分有效。

---

## 二、发现与问题清单（Findings）

### [P1] 项目终端主控输入未持久化导致用户输入记录页缺失主控原话（未变，维持）
- **位置**：[workbench/src/daemon.ts#L504-L509](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L504-L509)
- **严重度**：P1
- **失败场景**：
  项目终端中运行的主控 CLI（`role === "shell"`），用户在窗格内键入的指令由 `panes.shellInput` 直接转发到终端 PTY，没有调用 `recordInput` 写入 `gates.appendUserInput`。用户直接发给主控的指令没有进入 `user_inputs` 表，记录页无法呈现主控会话的用户输入。
- **说明**：此项在候选 2 中如实未改（等待用户裁定方案），T-133 验收条件第一条因此仍未达成。

### [P3] Codex 实际模型提取缺少真实端到端测试覆盖（未变，维持）
- **位置**：[workbench/src/metrics.ts#L32-L36](file:///Users/luckye/Documents/Code/a2a/workbench/src/metrics.ts#L32-L36)
- **严重度**：P3
- **失败场景**：
  自动化端到端测试夹具当前接入的是 Scripted Claude Worker，Codex 的 `native_record`（`turn_context` 解析 `payload.model` 和 `payload.effort`）提取分支尚未由真实的端到端或脚本化 Codex 夹具链路覆盖。

### [P3] 记录页层级为二级级联筛选，未实现树形结构展开（未变，维持）
- **位置**：[workbench/app/RecordsPage.tsx#L156-L163](file:///Users/luckye/Documents/Code/a2a/workbench/app/RecordsPage.tsx#L156-L163)
- **严重度**：P3
- **失败场景**：
  记录页通过任务下拉框与会话下拉框实现了二级级联筛选，满足基本查询需求，尚未形成树状展开视图。

---

## 三、审查结论

| Ticket | 总体结论 | 理由摘要 |
|---|---|---|
| **T-133** | **INCOMPLETE** | 记录页核心逻辑与人工介入标记正确，但由于项目终端主控输入持久化方案待用户裁定，主控原话尚未进入记录，验收条件第 1 条（主控终端、受管窗格、面板答复各一条并读回）未完全达成。遵循项目规则，严禁四舍五入，维持 INCOMPLETE。 |
| **T-134** | **PASS** | 原两处 P2 缺陷均已彻底修复：模型使用视图的回合数已严格按事件发生时间过滤，跨范围会话不漏计，单次查询无重复且跨切片回合可加；注意力消耗增加了全周期累计说明并以任务为 key；新测试、红态（候选 1 回测）与变异用例充分有效。四个指标视图满足验收要求。 |
