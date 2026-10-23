# T-137 独立代码审查报告：Reflect 页、复盘移入与定期复盘默认关闭

本审查基于只读检查 `full.diff`、[`T-137-reflect-page.md`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/T-137-reflect-page.md)、[`candidate-RESULTS.md`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/candidate-RESULTS.md) 以及运行摘要 [`green.json`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/green.json) 与 [`exits.txt`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/exits.txt)。

---

## 审查发现（Findings）

### 1. 【测试缺口】“关系不明进未归属”分支无测试断言与夹具覆盖
- **文件与行号**：[`test_t137_reflect_e2e.py`#L722-L737](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/tests/test_t137_reflect_e2e.py#L722-L737)，对照 [`ReflectPage.tsx`#L135-L147](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/app/ReflectPage.tsx#L135-L147)
- **严重度**：**P2**
- **失败场景**：
  [`T-137-reflect-page.md`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/T-137-reflect-page.md) 核心条款明确要求：“层级与侧栏同一来源……关系不明的进‘未归属’”。前端在 [`ReflectPage.tsx`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/app/ReflectPage.tsx#L135) 编写了 `const loose = roots.filter(node => !controller(node));` 与渲染分组 `{loose.length > 0 && <div className="reflect-loose"><div className="agent-task-label">未归属</div>...}`。但在 [`test_t137_reflect_e2e.py`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/tests/test_t137_reflect_e2e.py#L683-L710) 生成的夹具中，全部 6 个节点均为：2 个根主控（`i1` 构思主控、`e1` 执行主控）、1 个子执行主控（`e2`）和 3 个从属于 `e2` 的会话（`T-1 worker`、`T-2 worker`、`reviewer`）。`green.json` 证明 `loose` 数组在测试中恒为空，测试断言未覆盖“未归属”分区的显示与行为。

### 2. 【测试缺口】“已有设置不被改写”未提供存量升级测试证据
- **文件与行号**：[`test_t137_reflect_e2e.py`#L675-L682](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/tests/test_t137_reflect_e2e.py#L675-L682)，对照 [`retrospective.ts`#L427-L430](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/src/retrospective.ts#L427-L430)
- **严重度**：**P2**
- **失败场景**：
  Ticket 验收条款第 1 条要求：“已有的设置不改写（只追加的设置表照旧）”。虽然代码层面仅调整了出厂常数 `defaults = { enabled: false, ... }`，未引入任何破坏历史库表的变更，但 [`test_t137_reflect_e2e.py`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/tests/test_t137_reflect_e2e.py#L675) 仅针对全新空数据目录进行了测试（`schedule_off_by_default`），未构造“库内已有历史设置（如 `enabled: true`）的存量目录”来证明其加载与保存时不被改写，该条款缺少独立测试事实支撑。

### 3. 【边界缺陷】同一终端角色交接在同一毫秒时优先归属给已结束角色
- **文件与行号**：[`reflect.ts`#L393-L394](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/src/reflect.ts#L393-L394)
- **严重度**：**P3**
- **失败场景**：
  [`reflect.ts`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/src/reflect.ts#L393-L394) 的角色解析逻辑为：
  ```typescript
  const roleAt = (launch: string, time: string) => held.find(row => row.launch === launch && row.confirmed_at! <= time &&
    (row.state !== 'ended' || (row.ended_at ?? closed.get(row.launch) ?? '9999') >= time));
  ```
  若同一终端先后持有角色 R1 与 R2，且 R1 的结束时间戳 `ended_at` 与 R2 的生效时间戳 `confirmed_at` 精确落在同一毫秒 `T`：此时如果有会话在 `time === T` 启动，因为 `held.find` 是正序遍历，R1 满足 `confirmed_at <= T` 且 `ended_at >= T`（`T >= T` 为真），`roleAt` 会将该会话归属到已结束的 R1，而非新角色 R2。

### 4. 【测试缺口】监视器（monitor）角色未在端到端用例中实际派发
- **文件与行号**：[`test_t137_reflect_e2e.py`#L690-L737](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/tests/test_t137_reflect_e2e.py#L690-L737)，对照 [`reflect.ts`#L378](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/src/reflect.ts#L378)
- **严重度**：**P3**
- **失败场景**：
  Ticket 条款中要求展示“执行主控、worker、审查员、监视器”。[`reflect.ts`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/src/reflect.ts#L378) 维护了 `monitor: '监视器'` 映射，但测试用例仅派发了 worker 与 reviewer，监视器节点的树上展示与层级未被实际测试执行。

### 5. 【代码实现细节】RetrospectiveSections 中 version 状态未加入 useEffect 依赖
- **文件与行号**：[`RetrospectiveSections.tsx`#L169-L184](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/app/RetrospectiveSections.tsx#L169-L184)
- **严重度**：**P3**
- **失败场景**：
  组件定义了 `const [version, setVersion] = useState(0)`，并在保存操作成功后调用 `setVersion(v => v + 1)`，但数据加载的 `useEffect` 依赖数组为 `[project]`，未包含 `version`。操作完成后的页面更新依赖 5 秒的定时轮询，未能做到提交后通过 effect 触发即时重新拉取（沿袭原 T-136 实现，迁移时未作规整）。

---

## 重点核对项详细分析

### 1. reflect.ts 的树
- **已结束的主控与会话是否都列出**：**通过**。[`reflect.ts`#L392](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/src/reflect.ts#L392) 对 `roleRequests` 仅过滤了 `confirmed_at`，保留了 `state === 'ended'` 的历史终端主控；managed 会话全量取自 `launch_records`，结合 `panes.status` 的 `lifecycle` 和 `pane_archived` 时间，已结束的会话均以 `ended` 状态进入树。
- **同一终端先后多个角色时的归属**：**通过**。按会话的 `started_at` 检索终端在当时生效的角色（`confirmed_at <= time && (state !== 'ended' || ended_at >= time)`）。终端关闭未产生 `role_request_ended` 时，回退到 `orchestration_events` 的 `shell_closed` 时间；若仍未记则兜底 `'9999'`。
- **关系不明是否进“未归属”**：**实现通过，测试欠缺**。`parent` 无法追溯时置为 `null`，非主控的 root 节点在前端被归为 `loose` 并统一置于“未归属”标题下，不会胡乱猜测归属；但测试夹具未覆盖该分支（见 Finding 1）。

### 2. 打分挂载与门禁一致性
- **打分挂载**：**通过**。[`reflect.ts`#L408](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/src/reflect.ts#L408) 严格限定 `record.role === 'worker'`，审查员、监视器及主控不会被附加打分；打分对象根据门禁 `score_recorded` 中的 `launch_id` 严格与实际交付的 worker launch 匹配，未交付或未打分的 worker（如 `T-2`）为 `null`。
- **字段与展示一致性**：**通过**。`Score` 组件渲染了结果、边界纪律（含理由）、工程品味（含理由）以及备注，内容与门禁原始事件完全对应。变异 `score-on-attempt` 被断言抓住。

### 3. 只读性与 roleRequests 新字段
- **只读性**：**通过**。`reflect_tree` 在 [`daemon.ts`#L344](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/src/daemon.ts#L344) 显式注册为只读命令；[`reflectTree`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/src/reflect.ts#L381) 内部全部为 SELECT 查询和内存操作，无数据库写行为。
- **roleRequests 兼容性**：**通过**。仅在 [`roleRequests.ts`#L442](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/src/roleRequests.ts#L442) 增加了两个可空字符串字段 `confirmed_at` 与 `ended_at`，老字段定义和事件回放逻辑均未受破坏。既有测试（`t136`, `t133-t107`, `t107-live`）全部以 0 状态码通过。

### 4. 默认关闭与复盘设置
- **默认关闭**：**通过**。[`retrospective.ts`#L429](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/src/retrospective.ts#L429) 将出厂默认值设为 `enabled: false`，注入时钟不会自启。
- **页面开关与执行者保存**：**通过**。通过表单 `data-schedule-runner` 调整 CLI、模型、强度后保存，注入时钟验证了以保存的新执行者启动了一次复盘。
- **建议不送构思主控**：**通过**。前端文案由“已批准，交构思主控”改为“已批准”；系统无向构思主控分发任务的机制。

### 5. 原“复盘”页签与功能迁移
- **页签移除**：**通过**。[`renderer.tsx`#L314](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/app/renderer.tsx#L314) 将页签按钮彻底替换为 Reflect，去除了 `data-retrospective-tab`，测试断言 tabs 中无“复盘”。
- **功能一致性**：**通过**。原复盘页面重命名为 [`RetrospectiveSections.tsx`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/app/RetrospectiveSections.tsx)，作为子模块直接嵌入 Reflect 页，立即复盘、定期复盘设置、建议决策和复盘报告完整保留。

### 6. 测试设计与变异覆盖
- **期望独立性**：**通过**。测试中 `SCORE`、`FILES`、`MODEL` 等断言期望均硬编码自票面需求，不使用被测实现的输出作为基准。
- **变异与红态真实性**：**通过**。
  - `red-parent`：父提交上默认开启且缺少 Reflect 页，在 `schedule_off_by_default` 上失败（exit=1）。
  - `mutant-schedule-on-by-default`：被 `schedule_off_by_default` 抓住（exit=1）。
  - `mutant-ended-not-listed`：被会话树节点不足 6 个抓住（exit=1）。
  - `mutant-role-by-terminal-only`：被 `sessions_under_the_role_held_when_they_started` 抓住（exit=1）。
  - `mutant-score-on-attempt`：被 `score_on_scored_worker_only` 抓住（审查员也被打分，exit=1）。
- **声称覆盖但实际未覆盖项**：见 Finding 1（未归属分支）、Finding 2（存量配置升级）、Finding 4（监视器角色）。

---

## 总体结论

### **INCOMPLETE**

**理由**：
1. **验收证据不完整（不可四舍五入）**：对照 [`T-137-reflect-page.md`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/T-137-reflect-page.md) 票面明确条款，“关系不明的进‘未归属’”与“已有的设置不改写”属于明确交付要求。虽然实现代码已落位，但端到端测试用例中夹具未构造孤儿会话与存量配置库，导致这两个路径在测试证据（`green.json`）中完全缺失；[`candidate-RESULTS.md`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/candidate-RESULTS.md) 自身结论亦如实记录为 `INCOMPLETE`。依照“不得将不完整结果四舍五入为 PASS”的原则，必须裁定为 `INCOMPLETE`。
2. **走向 PASS 的最小闭环**：
   - 在 [`test_t137_reflect_e2e.py`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t137/workbench/tests/test_t137_reflect_e2e.py) 中增加一个脱离主控关系的独立/孤儿会话，断言其在 Reflect 页的“未归属”区域正确展示（闭环 Finding 1）；
   - 增加一个预置历史设置的场景，验证存量设置不被修改（闭环 Finding 2）。
