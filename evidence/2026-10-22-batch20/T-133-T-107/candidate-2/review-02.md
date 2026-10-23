# T-133（方案 A）与 T-107（#2、#4、#5）独立代码复审 02 报告

本复审以纯只读方式核对当前工作区下的 [review-01.md](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133/review-01.md)、[full.diff](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133/full.diff)、[candidate-2.diff](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133/candidate-2.diff)、[candidate-2-RESULTS.md](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133/candidate-2-RESULTS.md)、[green-02.json](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133/green-02.json) 与 [exits.txt](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133/exits.txt)，对照基线票据 [T-133-user-input-records-view.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-133-user-input-records-view.md) 与 [T-107-workbench-sidebar-projects-agent-tree.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-107-workbench-sidebar-projects-agent-tree.md)。

---

## 一、上一轮审查（review-01）处理核对

| review-01 发现项 | 严重度 | 候选 2 处理状态 | 审查判定与理由 |
| --- | --- | --- | --- |
| **发现 1：T-133 验收标准第一条要求的三种输入未在同一次运行中闭环证明**<br>([candidate-RESULTS.md:49](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133/candidate-RESULTS.md#L49)) | P2 | **已处理** | **通过**。在端到端测试 [`test_t133_t107_terminal_controller_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t133_t107_terminal_controller_e2e.py#L224-L283) 中，同一个夹具和同一项目 `demo` 下派出了受管 worker（T-1），模拟了问题上报与桌面答复、窗格键入并回车，并在同一个项目记录页中聚合断言了三种输入的共存与人工介入标记差异。详见下文第二节分析。 |
| **发现 2：Claude Code 主控在运行中被 Esc 中断时存在最长 60 秒的状态滞后窗口**<br>([sidebar.ts:360-361](file:///Users/luckye/Documents/Code/a2a/workbench/src/sidebar.ts#L360-L361)) | P2 | **不改** | **理由成立**。Claude Code 官方钩子体系中没有中断/取消事件（无 SIGINT/Cancel hook）；已在 [`sidebar.ts:374`](file:///Users/luckye/Documents/Code/a2a/workbench/src/sidebar.ts#L374) 与 README 缺口说明中如实写明，不采用脆弱的终端屏幕轮询或正则猜测推导状态，符合项目“语义识别不靠正则、不上调状态”的设计红线。 |
| **发现 3：记录页查询对缺少 `source_ref` 的畸形数据存在未防护的属性访问**<br>([userInputRecords.ts:22](file:///Users/luckye/Documents/Code/a2a/workbench/src/userInputRecords.ts#L22)) | P3 | **已修复** | **通过**。在 [`userInputRecords.ts:25`](file:///Users/luckye/Documents/Code/a2a/workbench/src/userInputRecords.ts#L25) 中已改为可选链访问 `input.source_ref?.label ?? ''`，消除了潜在的 `TypeError` 崩溃风险。 |
| **发现 4：侧栏轮询对 `terminal_turn` 执行全表无索引扫描**<br>([sidebar.ts:356](file:///Users/luckye/Documents/Code/a2a/workbench/src/sidebar.ts#L356)) | P3 | **不改** | **理由成立**。`terminal_turn` 仅记录已被批准为主控的项目终端回合，在本地单桌面生命周期中数据量与人类真实交互回合数等同（几十至几百条），SQL 仅提取两个字段并在 SQLite 内存缓存中毫秒级完成；在未形成物理性能瓶颈前不过早引入索引与额外查询逻辑，符合最小充分改动原则。 |

---

## 二、新测试与改动专项审查

### 1. `answer_issue` 只对 `operation_busy` 重试是否掩盖真实失败？
- **审查结论**：**未掩盖真实失败**。
- **证据与逻辑分析**：
  在 [`test_t133_t107_terminal_controller_e2e.py:238-245`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t133_t107_terminal_controller_e2e.py#L238-L245) 中：
  ```python
  def answer():
      result = fixture.request('answer_issue', fixture.operator, task='demo+T-1', issue=views[0]['issue']['id'], answer=ANSWER)
      assert result.get('ok') or result.get('error') == 'operation_busy', result
      return result.get('ok')
  fixture.wait('答复问题', answer, 60)
  ```
  1. **严格的错误过滤边界**：代码中使用了显式断言 `assert result.get('ok') or result.get('error') == 'operation_busy', result`。如果门禁返回任何非 `operation_busy` 的逻辑错误（例如 `unknown_task`、`invalid_issue`、`unauthorized`、参数格式错误或后台 crash），断言会在首轮调用中立即触发 `AssertionError` 导致测试当场失败退出，绝不会被静默吞掉。
  2. **锁死场景的硬超时防护**：若因门禁死锁导致持续返回 `operation_busy`，`fixture.wait` 设置了 60 秒的总超时限制，超时后抛出 `AssertionError: 超时：答复问题`。
  3. **并发锁争用的根因匹配**：在 a2a 门禁架构中，受管 worker 在执行工具调用（如 `git commit`、`submit`）时会瞬时持有任务级 `operationLock`（SQLite `BEGIN IMMEDIATE`）。测试侧的 operator 调用若恰好在同一微秒到达，门禁正常返回 `operation_busy`。因此，仅允许对该瞬时锁冲突进行轮询重试完全符合门禁并发协议，不掩盖任何真实缺陷。

### 2. `three_kinds_in_one_view` 检查是否独立于实现、是否确实抓住所声称的缺陷？
- **审查结论**：**独立于实现，且切实抓住了分离测试未能验证的交互归属缺陷**。
- **证据与逻辑分析**：
  在 [`test_t133_t107_terminal_controller_e2e.py:275-282`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t133_t107_terminal_controller_e2e.py#L275-L282) 中：
  ```python
  marked = {row['id'] for row in electron.evaluate("[...document.querySelectorAll('.user-input-page tr[data-input-id]')].filter(r=>r.dataset.intervention&&r.querySelector('.record-intervention')).map(r=>({id:r.dataset.inputId}))")}
  typed = [i for i in stored if i['text'] == TYPED]
  answer = [i for i in stored if i['form'] == 'answer' and ANSWER in i['text']]
  check('three_kinds_in_one_view', len(typed) == 1 and len(answer) == 1 and typed[0]['id'] in marked and answer[0]['id'] in marked and
        not any(i['id'] in marked for i in terminal_rows) and all(i['id'] in by_id for i in typed + answer + terminal_rows) and
        not any('显式交付' in text for text in by_id.values()), dict(marked=sorted(marked), stored=report['observed']['stored']))
  ```
  1. **期望来源的独立性**：`TYPED`、`ANSWER`、`terminal_rows` 的断言基准来自独立的测试预设常数与底层数据库原始记录；人工介入标记的提取直接检验真实 Electron DOM 的 `dataset.intervention` 与样式节点 `.record-intervention`；
  2. **对核心缺陷的捕获力**：测试检验了在同一项目视图内：
     - 受管 worker 窗格键入的输入必须带有“人工介入”标记；
     - 受管 worker 问题面板的答复必须带有“人工介入”标记；
     - 主控终端提交的所有整句（`terminal_rows`）绝对不能带有“人工介入”标记；
     - 后台注入的派发模板文本（`显式交付`）绝不在记录列表出现；
     - 全部三种输入类型行共存于同一个用户输入记录表中（`all(i['id'] in by_id ...)`）。
  3. **细微断言严格度提示**：见后文发现 P3 #1。

---

## 三、发现与问题清单（Findings）

### [P3] 发现 1：`three_kinds_in_one_view` 对 DOM 渲染文本内容未做逐条字段断言
- **文件与行号**：[`workbench/tests/test_t133_t107_terminal_controller_e2e.py:280-282`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t133_t107_terminal_controller_e2e.py#L280-L282)
- **失败场景**：
  在 `check('three_kinds_in_one_view', ...)` 中，校验数据行是否呈现在视图中的条件为：
  `all(i['id'] in by_id for i in typed + answer + terminal_rows)`。
  此处 `by_id` 是 `{row['id']: row['text']}` 的映射，该断言仅检查了对应记录的 `id` 属性是否存在于 DOM 节点的 `data-input-id` 中，但未显式检查文本内容（例如未断言 `TYPED in by_id[typed[0]['id']]` 或 `ANSWER in by_id[answer[0]['id']]`）。若前端 RecordsPage 发生回归（例如因列索引映射错误导致文本列被渲染为空白或渲染为其他占位符），只要行节点的 `data-input-id` 仍然存在，该断言依然会误判通过。
  *(注：根据 `green-02.json:120-144` 的实际捕获数据，当前界面的 `records_rows` 确实渲染了完整正确的文本，该项属于测试断言完备性层面的轻微缺陷)*。

### [P3] 发现 2：Reflect 树推导中当 managed 节点的 `parent_launch` 缺少匹配的主控历史时回退到 launch ID 无法匹配终端主控
- **文件与行号**：[`workbench/src/reflect.ts:49`](file:///Users/luckye/Documents/Code/a2a/workbench/src/reflect.ts#L49)
- **失败场景**：
  ```typescript
  const parent = parent_launch === null ? null : roleAt(parent_launch, node.started_at ?? '')?.id ?? (ids.has(parent_launch) ? parent_launch : null);
  ```
  终端主控在 `nodes` 列表中的 `id` 是角色申请的 UUID `row.id`（例如 `547d04fa-...`），而其 `launch` 是终端的 launch UUID（例如 `9c3df0f3-...`）。`ids` 集合记录的是 `nodes.map(n => n.id)`。
  若数据库中存在由于时钟偏差、事件丢失或时间戳不合导致 `roleAt` 未能查出匹配角色记录的终端主控，后续的回退逻辑 `ids.has(parent_launch)` 将无法命中（因为传入的是 `launch` ID 而不是 `row.id`），导致该会话被视作未归属区（`parent = null`）。对于受管主控（其 `id` 即为 `launch`），回退逻辑则正常生效。该设计虽符合“关系不明进未归属”原则，但在终端父级检索防御上存在细微的不对称性。

---

## 四、票务层面挂起事项单列（非代码审查否决理由）

根据审查指示，以下两项属于依赖用户决定的外部阻断，在 ticket 层面单列记录：

1. **Codex 侧钩子方案停下（Ticket T-133 用户决定第 41 条）**：
   - 探针证据（`codex-probe-RESULTS.md`）已确凿证实：Codex CLI 在注入钩子时必然触发信任弹窗，并在信任后直接修改用户宿主机的全局 `~/.codex/config.toml`；会话参数无法静默预填信任。
   - 候选严格遵照“会写用户配置即停下报告、不擅自绕过安全信任”的红线要求，保持在 `BLOCKED` 状态，未强行合入不安全实现。该行为符合规范，等待用户决定最终产品策略。
2. **侧栏“有未答复的问题上报”状态展示（Ticket T-107 #3 用户决定）**：
   - 用户针对该项回复“把‘有未答复的问题上报’显示成它 具体是什么意思？”，目前仍处于等待用户答复明确产品定义的阶段。

---

## 五、总体结论与理由

**总体结论：INCOMPLETE**

### 理由阐述：
1. **复审 01 发现项已闭环**：review-01 中的 4 项发现均已妥善处置。P2 级发现（三种输入在同一次运行中闭环）通过新增端到端场景与针对性断言得到了完整证据支撑；P3 级缺少属性防护的代码已修复；其余两项不改理由合理充分。
2. **新测试与实现质量过关**：针对 `answer_issue` 的重试机制经代码剖析仅放行良性并发锁争用，未掩盖真实失败；`three_kinds_in_one_view` 成功在同一真实 Electron 界面中核验了主控终端打字、受管窗格打字和面板答复的共存与介入标记逻辑；`candidate-2.diff` 引入的 Reflect 树与复盘默认值修改没有引入新破坏性问题。
3. **未完成状态如实上报，不向上舍入为 PASS**：根据项目核心准则（*“Report status with PASS, INCOMPLETE, BLOCKED, or NO_GO, and never round an incomplete result up to PASS”*），尽管 Claude Code 一侧的代码实现质量已达到合并要求，但由于 Codex 一侧按安全规则仍处于 `BLOCKED` 状态、且 T-107 #3 仍在挂起等待用户定夺，整体 ticket 需求尚未全面收口。故本次复审维持 **INCOMPLETE** 结论。
