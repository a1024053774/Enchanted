# T-133（方案 A）与 T-107（#2、#4、#5）代码独立审查报告

本审查以只读方式核对当前目录下的 [full.diff](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133/full.diff)、[candidate-RESULTS.md](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133/candidate-RESULTS.md)、[codex-probe-RESULTS.md](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133/codex-probe-RESULTS.md)、[green.json](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133/green.json) 及 [exits.txt](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133/exits.txt)，对照需求基线 [T-133-user-input-records-view.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-133-user-input-records-view.md) 与 [T-107-workbench-sidebar-projects-agent-tree.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-107-workbench-sidebar-projects-agent-tree.md) 的“用户决定”一节。

---

## 一、重点核对项目审查

### 1. `terminal_hook` 过滤边界与 `a2a hook` 运行时安全
- **未批准、已结束、会话 ID 不符时的进库防线**：
  - 在 [`daemon.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L853-L872) 中，当请求为 `terminal_hook` 且来源为 `terminal` 身份时，`unlogged` 被同步置为 `true`，彻底关闭了 `request_received`、`request_result` 和 `request_rejected` 事件日志记录，请求载荷中的输入提示词绝不会经由事件总线泄露进库。
  - 在 [`daemon.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L182-L191) 处理函数中，后台执行 `const held = roleRequests.approved(terminal.id)`：
    - **未批准**：`held` 为 `undefined`；
    - **已结束**（已释放/超时/进程退出）：[`roleRequests.approved()`](file:///Users/luckye/Documents/Code/a2a/workbench/src/roleRequests.ts#L70-L73) 仅返回状态为 `approved` 的记录，已结束状态（`ended`）返回 `undefined`；
    - **会话 ID 不符**：`payload?.session_id !== held.native_session` 校验为真。
    - 以上三者均直接返回 `{ ok: true, kept: false }`，不调用 [`appendUserInput`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L555-L562) 且不写入 `terminal_turn`，提示词及状态绝不进库。
- **`a2a hook` 的标准输出与退出码**：
  - 在 [`terminalCli.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/terminalCli.ts#L386-L395) 中，`command === "hook"` 内部全流程由 `try ... catch` 包裹，既不调用 `print` 也不调用 `process.stdout.write`；无论守护进程是否可达、写入是否报错，均静默吞掉异常并无条件 `return 0`。不会污染模型上下文，也不会因非 0 退出截断用户的回合。

### 2. 提示词完整性、提问答复记法与防重放机制
- **提示词是否为整句**：
  - 在 [`daemon.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L196) 中，`text` 取自 [`claudeSubmittedText(payload.prompt)`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L289-L292)。长文本粘贴被 Claude 自身包装的 `<pasted_content id="...">` 会被正则剥离并还原真实输入，普通输入则原样入库，记录的正是用户提交的完整整句。
- **`AskUserQuestion` 答复的记法**：
  - 在 [`daemon.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L206-L218) 中，钩子拦截 `PostToolUse` 且 `tool_name === "AskUserQuestion"` 时，若返回 `answers` 对象，转换为多行 `问题：答复` 格式（如 `先做哪一个？：T-1 先做`）；若为其他结构则转为 JSON 字符串。表单形态记为 `form: "answer"`，`reply_to` 与 `target.request` 准确指向该问题的 `tool_use_id`。
- **重复提交与钩子重放**：
  - 门禁 [`appendUserInput`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L555-L562) 使用底层事件去重表 `user_input_events`，对于提示词使用 `source = terminal:${terminal.id}:${payload.prompt_id}`，对于答复使用 `source = terminal:${terminal.id}:${payload.tool_use_id}`。
  - 由于 `INSERT OR IGNORE INTO user_input_events` 执行幂等去重，当发生钩子网络重试或重复回放时，相同的 `prompt_id` 或 `tool_use_id` 会返回 `changes === 0`，不重复写入 `user_inputs`，防重放机制完备。

### 3. 侧栏状态推导与状态上调判定
- **推导来源与上调防范**：
  - 在 [`sidebar.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/sidebar.ts#L356-L365) 中，终端主控的状态优先取该角色在 `orchestration_events` 里的最后一个 `terminal_turn`（`turns.findLast(...)`）。
  - 各类状态仅来源于结构化事件：`UserPromptSubmit`（运行中）、`PreToolUse`+`AskUserQuestion`（等待用户回答）、`PostToolUse`+`AskUserQuestion`（运行中）、`Stop`/`idle_prompt`（空闲）。没有匹配事件时显示为 `unknown`（未知），Codex 主控由于探针未上钩子同样保持 `unknown`，不存在无证据推导为运行中或空闲的“上调”缺陷。
- **“确认生效后到第一个事件之间算运行中”是否成立**：
  - **成立**：在终端主控交互流程中，用户在 Claude 会话中输入“请申请主控”，模型在此回合内调用 Bash 工具执行 `a2a request`，用户在界面点击批准后，`a2a request` 紧接着发送 `role_request_confirm`，确认成功返回给正在运行中的模型工具调用。此时模型当前的这一回合仍在活跃执行中，直至该回合模型输出完毕触发 `Stop` 钩子。因此在此区间内视为主控处于“运行中”完全符合物理执行事实。

### 4. 执行主控上级绑定与跨项目/状态隔离
- **后台严格校验**：
  - 在 [`roleRequests.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/roleRequests.ts#L334) 与 [`daemon.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L233-L242) 中：
    - **跨项目校验**：`isIdeation` 校验 `held.project === project` 与 `record.project === project`，非同项目一律拒收；
    - **已结束的构思主控**：已释放/退出的终端主控其 `roleRequests.approved(launch)` 为空，而受管主控要求 `panes.status(record.thread).lifecycle === "running"`，已停止或已结束的构思主控一律返回 `false` 并触发 `invalid_role_parent` 拒绝；
    - **非执行主控带 parent**：条件明确要求 `parent === null || (approved && roleRequest.role === "executor" ...)`，若为非执行主控（如 `ideation`）却传入 `parent`，立即被 `refuse` 拒绝。
- **侧栏层级呈现与容错**：
  - 在 [`sidebar.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/sidebar.ts#L167-L179) 中，侧栏在组装树形时二次校验了父会话关系及环路检测（`visited` 检测）。若绑定的构思主控在后续生命周期中结束退出，侧栏会自动将失去有效父级的执行主控归入 `parent = null`（未归属区），不会导致界面树渲染崩溃或层级错乱。

### 5. 测试真实度、变异捕获与覆盖面
- **期望值独立性**：
  - 端到端测试 [`test_t133_t107_terminal_controller_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t133_t107_terminal_controller_e2e.py) 中的各项期望（状态轮转、上级下拉选项、记录页文案、Git 状态行）直接根据用户决定与 Git 底层事实（`git rev-list --left-right --count`）手算构建，不从代码输出回填。
- **变异与红态捕获**：
  - `red-parent`：在修前版本 `836b9eeb0` 运行，因缺少钩子导致状态无法流转为 `idle` 而失败；
  - `mutant-recorded-without-role`：放宽角色校验，放弃身份后的输入被记下，被 `only_approved_prompts_recorded` 精准捕获；
  - `mutant-terminal-state-unknown`：强制保持 `unknown` 状态，被 `ideation_idle_after_first_turn` 捕获；
  - `mutant-parent-not-saved`：丢弃 `parent_launch` 存储，被 `executor_under_ideation` 捕获；
  - `t107-live-mutant-terminal-shown-idle`：将终端主控默认状态改为 `idle`，被现有测试 `terminal_controllers_unknown_not_upgraded` 捕获。
- **覆盖声明与真实覆盖核对**：
  - 详见后文发现 P2 #1：T-133 验收要求的三种输入组合（主控终端打字、worker 窗格打字、面板答复）实际由两个测试分立覆盖，未在单个测试场景中聚合验证。

### 6. Codex 一侧停下的理由是否成立
- **完全成立**：
  - [T-133 用户决定](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-133-user-input-records-view.md#L34-L42) 明确规定：“先用探针确认在用户真实的 `~/.codex` 下是否会弹出钩子信任、是否会写用户配置；会写的话停下报告，不用 `--dangerously-bypass-hook-trust` 绕过”。
  - [codex-probe-RESULTS.md](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133/codex-probe-RESULTS.md) 的三个探针确凿证明：Codex CLI (0.163.0) 只要通过 `-c` 注入未信任的钩子，均会弹出 Hook 审查弹窗；一旦确认信任，Codex 会将 hash 直接持久化写入用户全局的 `config.toml`；且无法通过会话参数预填信任条目。
  - 候选严格遵循了“会写用户配置即停下报告、不擅自绕过安全信任”的红线要求，停止理由充分成立。

---

## 二、发现与问题清单（Findings）

### [P2] 发现 1：T-133 验收标准第一条要求的三种输入未在同一次运行中闭环证明
- **文件与行号**：[candidate-RESULTS.md:49](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133/candidate-RESULTS.md#L49)、[test_t133_t107_terminal_controller_e2e.py:466-476](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t133_t107_terminal_controller_e2e.py#L466-L476)
- **失败场景**：
  [T-133 Acceptance 第一条](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-133-user-input-records-view.md#L21-L24) 明确要求：“真实 Electron：夹具里用户在主控终端和受管 worker 窗格各打一段字、在面板答复一条；视图列出三条，worker 那条标人工介入，内容与库读回一致；后台注入的派发文字不出现”。
  当前实现中，受管窗格打字与面板答复由历史测试 `test_t133_t134_records_metrics_e2e.py` 验证，而主控终端打字由新测试 `test_t133_t107_terminal_controller_e2e.py` 验证。若记录页在处理“同一项目中混合存在 worker 窗格输入与主控终端输入”时存在任务筛选或会话归属冲突，分离的测试将无法暴露此缺陷。

### [P2] 发现 2：Claude Code 主控在运行中被 Esc 中断时存在最长 60 秒的状态滞后窗口
- **文件与行号**：[sidebar.ts:360-361](file:///Users/luckye/Documents/Code/a2a/workbench/src/sidebar.ts#L360-L361)、[candidate-RESULTS.md:54](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133/candidate-RESULTS.md#L54)
- **失败场景**：
  当用户在终端内按 Esc 键主动中断正在运行命令或思考的 Claude Code 时，Claude Code 不会触发 `Stop` 钩子，亦无中断事件触发。侧栏在此期间由于未能获得任何新事件，状态仍维持上一次的 `running`；必须等待 Claude Code 闲置达到 60 秒后发出 `Notification (idle_prompt)` 钩子，侧栏才会转为 `idle`。在用户主观感知上，这 60 秒内界面显示模型仍在“运行中”，构成临时的状态错误与滞后。

### [P3] 发现 3：记录页查询对缺少 `source_ref` 的畸形数据存在未防护的属性访问
- **文件与行号**：[userInputRecords.ts:22](file:///Users/luckye/Documents/Code/a2a/workbench/src/userInputRecords.ts#L22)
- **失败场景**：
  ```typescript
  role: input.channel === 'controller-terminal' ? requested.get(input.source_ref.label ?? '') ?? null
  ```
  若数据库中存在外部注入、历史遗留或手动插入的 `controller-terminal` 异常记录且其 `source_ref` 字段为 `null` 或未定义，`input.source_ref.label` 会直接抛出 `TypeError: Cannot read properties of undefined (reading 'label')`，导致整个 `user_input_records` 命令崩塌，用户界面记录页将持续显示读取失败。应防御性编写为 `input.source_ref?.label ?? ''`。

### [P3] 发现 4：侧栏轮询对 `terminal_turn` 执行全表无索引扫描
- **文件与行号**：[sidebar.ts:356](file:///Users/luckye/Documents/Code/a2a/workbench/src/sidebar.ts#L356)
- **失败场景**：
  侧栏每 3 秒执行一次轮询快照，其中执行 SQL：
  `SELECT json_extract(data,'$.role_request') AS role_request, json_extract(data,'$.state') AS state FROM orchestration_events WHERE type='terminal_turn' ORDER BY seq`。
  随着工作台长期运行，`orchestration_events` 表中的回合事件将无限累积，且未按当前活跃的项目或 `role_request.id` 范围加条件过滤，全表提取后在内存中使用 `findLast`。虽然在轻量会话中无明显卡顿，但在持续多日运行的高吞吐项目下会造成不必要的 CPU 与内存开销。

---

## 三、总体结论与理由

**总体结论：INCOMPLETE**

### 理由阐述：
1. **符合停止网关与用户授权约束**：Codex 端的钩子方案经探针验证会弹框并写入用户全局 `~/.codex/config.toml` 配置，严格触发了 T-133 用户决定中的停下条件。候选按规定停在当前阶段，状态标记为 `BLOCKED`，未越权使用 `--dangerously-bypass-hook-trust` 强制合入，此行为符合规范。
2. **待决事项仍在挂起**：[T-107 #3](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-107-workbench-sidebar-projects-agent-tree.md#L95)（是否保留“等待主控回答”状态或将其显示为未答复问题上报）仍处于等待用户回复阶段。
3. **已实现部分质量合格**：针对 Claude Code 的终端主控钩子拦截、整句提取入库、AskUserQuestion 答复记录、上级构思主控多维安全核验、Git 分支事实行以及 5 组针对性变异与红态测试均已真实跑通，代码无破坏性逻辑缺陷；但受制于未完成的 Codex 侧与验收分离覆盖问题，按照项目验收准则，不得将未闭环结果舍入为 PASS，维持候选自述的 **INCOMPLETE** 结论。
