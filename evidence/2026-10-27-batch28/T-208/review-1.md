# T-208 独立审查报告

**结论**：`可合并`

---

## 逐项核对详情

### 1. 根因与修复核对

1. **状态名来源确认**：
   - **底部门禁状态条**：在 [`workbench/app/renderer.tsx:1192`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L1192)，底部状态条由 `<div><span className="gate-label">门禁</span><strong data-gate-state={task?.state ?? 'unknown'}>{gateNames[task?.state ?? ''] ?? '未知'}</strong></div>` 渲染。其中第 142 行 `const gateNames = gateStateNames;`，若表内无对应键，则回退显示 `'未知'`。
   - **顶部任务标签**：在 [`workbench/app/renderer.tsx:1113`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L1113)（任务条）与第 1159 行（项目任务卡），均使用 `{gateNames[item.state] ?? item.state}`。若未定义，则直接回退显示原始英文代码。
   - **门禁记录标题**：在 [`workbench/app/TaskRecord.tsx:87, 91`](file:///Users/luckye/Documents/Code/a2a/workbench/app/TaskRecord.tsx#L87-L91)，引入并使用 [`gateStateNames`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gateReceipts.ts#L8-L11)：`<summary>门禁记录 · {gateStateNames[state] ?? state} · ...</summary>`，查不到即显示原始英文状态名。
   - **终端门禁回执**：在 [`workbench/src/gateReceipts.ts:19-20`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gateReceipts.ts#L19-L20) 的 [`receiptLines`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gateReceipts.ts#L10-L24) 中，同样依赖 `gateStateNames[task.state] ?? task.state` 格式化回执行。
   - 修复在 [`workbench/src/gateReceipts.ts:10`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gateReceipts.ts#L10) 补齐了 `reviewing: '审查中', rework: '返工中'`，确实定位在上述所有位置的这单一事实源上。

2. **其他状态名表排查**：
   - **流程页**（[`FlowPage.tsx`](file:///Users/luckye/Documents/Code/a2a/workbench/app/FlowPage.tsx) / [`flowStages.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/flowStages.ts) / [`flow.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/flow.ts)）：流程泳道使用的是基于门禁事件类型（`event.type`）推导的 5 个固定业务阶段（`implementation` 认领与实现、`delivery` 交付、`checks` 机械检查、`review` 独立审查、`integration` 集成），会话图标使用 `icons` 与 `agent.state_label`，不直接读取或映射任务门禁状态，不存在缺词。
   - **指标页**（[`MetricsPage.tsx`](file:///Users/luckye/Documents/Code/a2a/workbench/app/MetricsPage.tsx)）：使用固定的机械检查项名表 `checks`（`identity_version`、`path_boundary` 等），不包含任务门禁状态名表。
   - **侧栏与项目列表**（[`sidebar.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/sidebar.ts) / [`renderer.tsx`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx)）：维护的是会话运行状态 [`AgentState`](file:///Users/luckye/Documents/Code/a2a/workbench/src/sidebar.ts#L12)（`running`、`waiting_user_answer` 等）和 `stateLabels`；侧栏项目下的任务项透传门禁任务原样数据，最终在 `renderer.tsx` 由 `gateNames` 格式化。
   - **记录页**（[`RecordsPage.tsx`](file:///Users/luckye/Documents/Code/a2a/workbench/app/RecordsPage.tsx)）：维护表单形态 `forms`、通道 `channels` 与角色名 `roles`，不涉及任务状态名。
   - 排查结论：界面除 [`gateStateNames`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gateReceipts.ts#L8-L11) 外无其他遗漏 `reviewing`/`rework` 的任务状态名表。

3. **门禁源码非 `task.state = "..."` 写入形式核对**：
   - **存在此现象**。在 [`workbench/src/gates/core.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts) 中存在以下 2 处任务状态赋值未写为 `task.state = "..."`：
     1. [core.ts:3872](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L3872)（`command === "create"` 初始化任务对象）：`state: "creating"`（对象字面量直接赋初值）。
     2. [core.ts:4115](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L4115)（`command === "abandon"` 放弃或升级任务）：`task.state = data.result === "放弃" ? "abandoned" : "upgraded";`（三元条件赋值）。
   - 影响详见下文“问题清单”第 1 条。

---

### 2. 测试区分能力核对

1. **红态运行**（[`red-1.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-208/red-1.json)）：
   - 执行参数为 `--revision f5ae30f78`（修前代码）。
   - `checks` 通过 `still_in_review_when_read`，失败项准确记录为 `review_state_named`（读取到底部 `bar` 为 `{"state": "reviewing", "text": "未知"}`）与 `every_gate_state_named`（`missing: ["reviewing", "rework"]`），准确捕获修前真实缺陷。
2. **绿态运行**（[`green-2.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-208/green-2.json)）：
   - 执行参数未带变异或旧版本，测试全部 3 项检查通过，底部门禁条读取为 `{"state": "reviewing", "text": "审查中"}`，`missing: []`。
3. **变异体运行**（[`mutant-rework-unnamed-2.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-208/mutant-rework-unnamed-2.json)）：
   - 变异体故意将 `rework: '返工中'` 移除，保留 `reviewing: '审查中'`。
   - 运行时 `still_in_review_when_read` 与 `review_state_named` 均通过，唯一在 `every_gate_state_named` 失败（`missing: ["rework"]`）。这证实了源码状态覆盖检查并非形式化空跑，能够有效拦截缺项。
4. **时效保证（`still_in_review_when_read`）**：
   - 夹具中审查员对“审查这一次交付”的指令执行脚本化命令 `sleep 40`，保证在 40 秒内保持在审查中。
   - 测试在等到门禁状态变为 `reviewing`（第 97 行）后，点击侧栏打开窗格并读取底部状态条。
   - 读取完成后，立即调用门禁接口读取当前任务状态 `report['state_after_read'] = status()['state']`，并断言其值必须仍为 `reviewing`（第 108-109 行）。这排除了“读取页面时审查已结束/已退出导致误判”的可能性。
5. **预期来源**：
   - 预期完全来自需求 [T-208](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-208-reviewing-state-unknown.md) 及 [UAT-03](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/UAT-03/RESULTS.md) 发现 3，非从当前实现倒推。

---

### 3. 顶部任务标签与轮询判断核对

- **事实依据**：在 [`workbench/app/renderer.tsx:795`](file:///Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx#L795)，侧栏数据刷新通过 `setInterval(..., 3000)` 每 3 秒拉取一次。顶部标签（`task-strip`）依赖 `project.tasks`，该数据随侧栏更新，与打开窗格时由主进程路由即时获取的窗格快照存在天然的时间差。
- **探针数据**（[`probe-tab-refresh.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-208/probe-tab-refresh.json)）：
  - 第 0 秒：门禁状态 `reviewing`，底部已是 `审查中`，而顶部标签仍是上一轮缓存的 `已认领`。
  - 第 4 秒（超过 3 秒轮询周期）：门禁因审查员未交结论而超时暂停（`paused`），此时顶部标签同步刷新为 `已暂停`，与底部及门禁当前状态完全一致。
- **判断评估**：RESULTS 中指出顶部任务标签有最大 3 秒的异步轮询延迟、不属于代码写死或缺失翻译的问题，该判断在数据与实现原理上有充分支撑。

---

### 4. 文案与事实一致性核对

1. 文案与改动代码事实完全一致：门禁底层状态机保持未改动，仅补全前端状态展示字典。
2. 票上的每项验收条件均有真实自动化运行证据（`red-1.json`、`green-2.json`、`mutant-rework-unnamed-2.json`）与截图归档凭证（`red-1-screenshot.archive.json`、`green-2-screenshot.archive.json`）。
3. 坦承说明了未做项（`rework` 仅通过静态源码覆盖测试验证，未在真实 UI 上触发一次完整的打回返工交互流程），且保留了解释了初次调优时无效运行的证据文件，符合工程规范。

---

## 发现的问题清单

1. **测试静态覆盖断言存在模式匹配遗漏**
   - **位置**：[`workbench/tests/test_t208_gate_state_names_e2e.py:115`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t208_gate_state_names_e2e.py#L115)
   - **失败场景**：测试使用正则表达式 `r'task\.state = "([a-z_]+)"'` 提取门禁写入的状态集。但在 [`workbench/src/gates/core.ts:3872`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L3872)（对象字面量 `state: "creating"`）与 [`workbench/src/gates/core.ts:4115`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L4115)（三元表达式 `task.state = data.result === "放弃" ? "abandoned" : "upgraded";`）中，赋值形式均不匹配该正则。导致测试实际提取的状态集仅有 12 个，漏提取了 `creating`、`abandoned` 和 `upgraded` 3 个有效状态。虽然生产代码 [`gateStateNames`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gateReceipts.ts#L8-L11) 中现已恰好包含此 3 个状态，但这使得测试所谓的“从门禁源码中提取每一个状态逐个核对”对非直接等号字面量赋值存在盲区。未来若新增状态以字面量对象或条件表达式写入，该测试将无法防范缺漏。
   - **严重程度**：P2

---

## 结论

**`可合并`**

候选改动聚焦根因，改动最小且安全，未引入任何副作用或破坏性变更；端到端测试真实覆盖了 Electron UI、原生 CLI 交互与状态读取，红态与变异体反例完备。上述 P2 问题属测试工具静态分析正则的严密性缺陷，不影响功能正确性。

---

## LIMITATIONS

1. 本审查为独立只读审查，未执行任何 shell 命令，未修改文件，未启动后台或应用进程。
2. 审查基于代码静态分析、Git 候选 diff 以及已有测试运行证据 JSON 的交叉核对；未在物理屏幕上挂载外置盘直接肉眼核验截图像素，依赖自动化测试对 DOM 节点 innerText 和 dataset 属性的直接抽取结果。