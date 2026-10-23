# T-133（方案 A Codex 一侧）与 T-107 #3 独立只读审查报告

本审查以**纯只读**方式进行，未修改任何工作区文件，未执行任何命令；所有事实与判断均严格基于工作区代码文件、探针记录、端到端测试与真实运行摘要。

---

## 一、审查对象与依据基准

1. **审查对象**：
   - **T-133 方案 A Codex 一侧**：Codex 主控提交与提问答复记录，Enchanted 钩子注入与信任模型；
   - **T-107 #3**：受管会话未答复问题上报时，侧栏状态显示为“等待主控回答”，问题面板照旧展示。
2. **用户逐字裁决（2026-10-22）**：
   > “1. A 2. 一二都要.”
   - 第 1 条：Codex 主控也记录，由用户在自己的 Codex 里信任一次 Enchanted 的钩子，信任由 Codex 写入用户配置，a2a 不写用户配置、不用 `--dangerously-bypass-hook-trust`；
   - 第 2 条：worker 有未答复的问题上报时侧栏显示“等待主控回答”，问题面板照旧列出。
3. **审查材料核对**：
   - 变更差异：[`candidate.diff`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/candidate.diff)（`d0f89b48a..d0c006ee1`）
   - 实现源码：[`workbench/src/daemon.ts`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/daemon.ts)、[`workbench/src/sidebar.ts`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/sidebar.ts)、[`workbench/src/panes.ts`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/panes.ts)、[`workbench/terminal/bin/codex`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/codex)
   - 探针原件：[`probe-RESULTS.md`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/probe-RESULTS.md)、[`probe-04-hooks.jsonl`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/probe-04-hooks.jsonl)、[`probe-05-hooks.jsonl`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/probe-05-hooks.jsonl)、[`probe-06-hooks.jsonl`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/probe-06-hooks.jsonl)
   - 候选运行与结果：[`candidate-3-RESULTS.md`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/candidate-3-RESULTS.md)、[`candidate-4-RESULTS.md`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/candidate-4-RESULTS.md)、[`codex-green.json`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/codex-green.json)、[`claude-green.json`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/claude-green.json)、[`exits.txt`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/exits.txt)
   - 规格票据：[T-133 ticket](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-133-user-input-records-view.md)、[T-107 ticket](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-107-workbench-sidebar-projects-agent-tree.md)

---

## 二、专项核对要点分析

### 1. 实现是否符合用户决定与探针事实

- **会话 ID 匹配**：
  - 探针 `probe-04` 证明 Codex 钩子载荷中的 `session_id` 等于其环境变量 `CODEX_THREAD_ID`，即角色申请时记录的 `native_session`。
  - [`daemon.ts:305`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/daemon.ts#L305) 显式核验 `payload?.session_id !== held.native_session`，不符则直接丢弃不记；未批准或已释放（`release`）的主控终端提交均被拦截。
- **答复格式解析**：
  - 探针 `probe-05` 证实 Codex 提问答复以 `<send_user_message_question_reply>` 包裹的 JSON 数组作为一次 `UserPromptSubmit` 返回。
  - [`panes.ts:122-132`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/panes.ts#L122-L132) 的 `codexQuestionReply` 解析出对应 `tool === "request_user_input_async"` 的 `call_id` 并格式化为 `问题：答复`，写入 `form: "answer"`、`reply_to: reply.call`，非格式化内容退化为普通消息。
- **提问期间状态流转**：
  - 探针 `probe-04` 表明 Codex 的提问工具 `request_user_input_async` 会立刻返回 `{"accepted":true}`，随后模型调用 `clocksleep` 等待。
  - [`terminal/bin/codex:11-12`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/codex#L11-L12) **有意不给 Codex 注入 `PostToolUse` 钩子**，且 `PreToolUse` 设置了 `matcher="request_user_input_async"`。因此进入等待后状态保持 `waiting_user_answer`，直到用户答复（新的 `UserPromptSubmit`）到达才推进到 `running`，回合结束发 `Stop` 变 `idle`。状态流转逻辑完全闭环。
- **去重键**：
  - Codex 答复记录使用 `terminal:${terminal.id}:${reply.call}` 作为门禁去重键，具备确定性防重入保证；普通提交因 Codex 没有 `prompt_id`，采用每次钩子调用一条（详见发现 P2 #1 分析）。
- **信任不由 a2a 写入**：
  - [`terminal/bin/codex:10`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/codex#L10) 使用 `command="\"$A2A_TERMINAL_BIN/a2a\" hook"`，命令定义在所有终端间保持字面一致，使 Codex 计算出的配置哈希稳定。
  - 脚本与后台代码没有任何写入 `~/.codex/config.toml` 的逻辑，也未使用 `--dangerously-bypass-hook-trust`；初次启动由用户在 Codex TUI 中审查并选信任，Codex 自身将哈希持久化至配置中，后续终端复用信任。

### 2. 侧栏“等待主控回答”的判定一致性与误报/漏报审查

- **门禁答复受理条件对比**：
  - 门禁核心 [`gates/core.ts:855-856`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L855-L856) 接受答复的前置条件为：
    1. `view.state !== "已关闭"`；
    2. `!view.answer`。
  - 侧栏判定 [`sidebar.ts:131`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/sidebar.ts#L131)：
    `filter((view: any) => view.state !== '已关闭' && !view.answer).map((view: any) => String(view.issue.thread_id))`
  - **结论**：过滤条件与门禁接受答复的业务条件**逐字完全一致**。
- **优先级与覆盖规则**：
  - [`sidebar.ts:162`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/sidebar.ts#L162)：
    `['ended', 'unrestored', 'waiting_user_answer'].includes(native) ? native : waiting === null ? 'unknown' : waiting?.has(record.thread) ? 'waiting_controller_answer' : native`
  - 原生处于 `ended`（已结束）、`unrestored`（未恢复）和 `waiting_user_answer`（等待用户回答）时明确保留，不被上报状态覆盖；
  - 任务上报读取失败（`waiting === null`）时如实降级为 `unknown`，不上调状态；
  - 答复送达或关闭后，会话从 `waiting` 集合移除，状态即刻恢复为 `native`；
  - 问题面板未做变更，照旧通过 `issues` 命令展示。
  - **结论**：不存在逻辑层面的误报或漏报。

### 3. 异常、Fallback、死代码与平行路径审查

- **死代码清理**：
  - 候选 3 中曾在后台设置过“Codex 的 PostToolUse 不算答复”的守护分支，因包装脚本未注入 `PostToolUse` 导致该分支永远不可达；在候选 4 中该死代码已彻底删除，变异测试也调整为显式注入该钩子的坏实现。
- **异常捕获与状态标记**：
  - [`daemon.ts:328-331`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/daemon.ts#L328-L331) 在写入失败时设置 `setUserInputObserverStatus("failed", ...)` 并重新抛出，未静默吞异常；
  - `codexQuestionReply` 的 `catch` 仅用于处理非协议格式文本退化，符合“不合规包裹保留为原文提示词”的设计预期。
- **平行路径**：
  - Claude 与 Codex 主控终端复用了相同的 `terminal_hook` 路由、相同的 `terminal_turn` 编排事件流及相同的记录表，仅根据 CLI 协议差异做字段适配，未开辟平行状态存储或第二套门禁通道。

### 4. 测试独立性、红态与变异证明

- **独立性验证**：
  - 测试预设常量（`REQUEST_IDEATION`、`IDEA_PROMPT`、`QUESTION`、`CHOICE`、`RELEASE`）独立定义，断言直接比对预设元组与底层数据库/DOM 节点，未以被测代码输出作为期望基准。
- **修前红态与变异击杀（`exits.txt` 证实全数通过）**：
  1. `codex-red-parent`（`d0f89b48a`，exit=1）：修前包装脚本无钩子，未能触发多钩子审查弹窗；
  2. `codex-mutant-hooks-not-passed`（exit=1）：包装脚本短路不传钩子，测试在审查断言失败；
  3. `codex-mutant-post-hook-passed`（exit=1）：包装脚本错误注入 `PostToolUse`，导致提问时瞬间切回 `running`，等待超时失败；
  4. `codex-mutant-reply-as-message`（exit=1）：后台将答复记为普通消息，`only_approved_prompts_recorded` 断言失败；
  5. `claude-red-parent`（`d0f89b48a`，exit=1）：修前无未答复上报状态，侧栏断言超时；
  6. `claude-mutant-issue-not-waiting`（exit=1）：侧栏保留 `native` 状态，侧栏断言超时。

### 5. README 与缺口说明如实性

- [`workbench/README.md:14-27`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/candidate.diff#L14-L27) 完整补充了 Codex 主控钩子机制、信任流程、提问状态以及已知边界（信任前为未知、Plan 模式同步提问不记、Esc 中断后持续显示运行中等）；
- [`workbench/README.md:36-37`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/candidate.diff#L36-L37) 与 [`sidebar.ts:188-190`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/sidebar.ts#L188-L190) 移除了原有的“等待主控回答显示未知”陈旧缺口，如实更新了 Codex 的已知限制，文案与事实完全一致。

---

## 三、发现项清单（Findings）

### [P2] 发现 1：Codex 主控普通提示词提交使用随机 UUID 作为去重键，丧失重放去重防护
- **文件与行号**：[`workbench/src/daemon.ts:327`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/daemon.ts#L327)
- **代码片段**：
  ```typescript
  `terminal:${terminal.id}:${reply ? reply.call : codex ? randomUUID() : submission}`
  ```
- **失败场景**：
  门禁的 `appendUserInput` 依赖第二个参数写入 `user_input_events` 表实现幂等去重。
  Claude Code 具有天然唯一的 `payload.prompt_id`，去重键为 `terminal:${terminal.id}:${payload.prompt_id}`；Codex 对提问的答复具有 `reply.call`，去重键为 `terminal:${terminal.id}:${reply.call}`。
  但对于 Codex 普通输入（`reply === null`），代码每次调用均生成全新的 `randomUUID()`。如果 Codex CLI 因网络抖动、进程异常重试或终端 hook 进程发生重放调用，门禁将无法感知重复，导致同一句用户输入在 `user_inputs` 表中被多次重复写入，记录页展示重复行。
  *(注：该做法根源在于 Codex 提交载荷中没有 `prompt_id`，且同一回合内的答复与原提问共用 `turn_id`，直接使用 `submission`（即 `turn_id`）会导致冲突；代码注释与 README 已明确注明“每次钩子调用记一条”，但设计上客观放弃了普通提问的去重幂等性)*。

---

### [P3] 发现 2：侧栏快照对各任务执行串行异步 `issues` 查询，存在 N+1 轮询开销
- **文件与行号**：[`workbench/src/sidebar.ts:129-133`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/sidebar.ts#L129-L133)
- **代码片段**：
  ```typescript
  const unanswered = new Map<string, Set<string> | null>();
  for (const task of new Set(launches.map(record => record.task).filter((task): task is string => typeof task === 'string'))) {
    const result = await gates.call({ command: 'issues', task });
    unanswered.set(task, result.ok ? new Set((result.issues ?? []).filter((view: any) => view.state !== '已关闭' && !view.answer)
      .map((view: any) => String(view.issue.thread_id))) : null);
  }
  ```
- **失败场景**：
  侧栏在每次轮询快照时，遍历所有活跃启动记录关联的任务集合，使用 `for ... of` 配合 `await gates.call({ command: 'issues', task })` 进行串行查询。
  当工作区中并行任务数量增加时，每个任务依次发起异步门禁调用，累加了侧栏快照的响应延迟。当前在单机本地 SQLite 环境下耗时仍为毫秒级，但采用 `Promise.all` 并发拉取或提供任务批量查询更具防御性。

---

### [P3] 发现 3：Claude 端到端测试在答复后对 worker 状态的断言仅使用了非等待排他断言
- **文件与行号**：[`workbench/tests/test_t133_t107_terminal_controller_e2e.py:640-642`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/test_t133_t107_terminal_controller_e2e.py#L640-L642)
- **代码片段**：
  ```python
  electron.until('答复之后不再等待主控回答', f"(()=>{{const r=document.querySelector('.agent-row[data-agent-launch=\"{worker}\"]');"
                 "return !!r&&r.dataset.agentState!=='waiting_controller_answer'})()", 60)
  report['observed']['worker_after_answer'] = agent(worker)
  check('answered_issue_no_longer_waits', True)
  ```
- **失败场景**：
  测试在主控答复上报后，断言条件为 `r.dataset.agentState !== 'waiting_controller_answer'`。若此时侧栏发生异常回归导致 worker 状态错误变为 `'unknown'`，该断言依然会误判为通过（虽然 `claude-green.json:78` 抓取到的实际状态为合法的 `'idle'`，但断言自身未显式验证是否回退到积极的期望状态）。

---

### [P3] 发现 4：`codexQuestionReply` 对 `replies` 数组内对象的字段类型缺乏防御性校验
- **文件与行号**：[`workbench/src/panes.ts:130`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/review-t133-c4/panes.ts#L130)
- **代码片段**：
  ```typescript
  return { call, text: replies.map(reply => `${reply.question}：${reply.answer}`).join("\n") };
  ```
- **失败场景**：
  `replies.map` 直接访问 `reply.question` 和 `reply.answer`，若外部输入的畸形 JSON 数组项缺失对应键（例如 `[{ "questionItemId": "..." }]`），将拼接出包含 `undefined：undefined` 的异常文本并入库。虽然顶层包裹在 `try ... catch` 中不会引发进程异常崩溃，但对数组项键值类型的显式校验更为稳健。

---

## 四、总体结论与理由

**总体结论：PASS**

### 判定理由：
1. **完全符合用户裁决与安全约束**：
   严格落地了 2026-10-22 用户“1. A 2. 一二都要.”决定。Codex 钩子通过每会话参数注入，哈希稳定，信任由 Codex 自身持久化至用户配置；a2a 不触碰全局配置、不使用危险绕过参数。
2. **状态流转与门禁规则精准一致**：
   侧栏“等待主控回答”的判定条件与门禁接受答复的业务前置条件（未关闭且无答复）完全契合；不覆盖 `ended`、`unrestored` 与 `waiting_user_answer`，逻辑推导无误报与漏报漏洞。
3. **测试证据扎实闭环**：
   候选 3 中残留的 PostToolUse 死代码已清除；新检查在修前父版本均呈红态，所有设计变异均被有效击杀；真实 Electron、真实 Codex/Claude CLI 环境下的绿态运行日志已留存完整。
4. **发现项风险可控**：
   本次发现的 1 项 P2 与 3 项 P3 均属于受底层 CLI 机制限制的设计权衡或轻微防御性冗余，不存在阻碍发布（P0/P1）的功能性或安全性缺陷，实现具备合并质量。
