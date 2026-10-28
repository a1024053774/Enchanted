# T-206 独立审查报告

基于对候选改动 [/private/tmp/t-206-review/change.diff](file:///private/tmp/t-206-review/change.diff)、票据 [T-206-record-input-on-send.md](file:///Users/luckye/Documents/Code/a2a/.project-map/tickets/T-206-record-input-on-send.md)、证据目录 [evidence/2026-10-27-batch28/T-206/](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-206/RESULTS.md) 及其关联测试与源码的只读核对，审查结论如下。

---

## 审查核对项

### 1. 根因层与架构完整性
- **修复位置**：
  - 核心逻辑位于 [`workbench/src/panes.ts:userInput`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L1351-L1407)、新增纯模块 [`workbench/src/inputDraft.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/inputDraft.ts) 以及 [`workbench/src/daemon.ts:recordInput`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L730-L743)。
  - 此处是 xterm `window_input` 字节流与门禁用户输入记录的唯一交汇点，修在根因层，符合票内做法。
- **并发、异常与 Fail-Closed**：
  - 在 [`panes.serializeWrite`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L1327-L1337) 锁内，首先克隆当前草稿并在副本上运行 [`feedInput`](file:///Users/luckye/Documents/Code/a2a/workbench/src/inputDraft.ts#L34-L69) 获得发出条目；
  - 记录通过 `record(entry.text, entry.content)` 先写入门禁与数据库。若记录抛出错误，直接中断，PTY 绝不写入（`pane.pty.write` 不会执行），且 `pane.draft` 不被更新，严格满足 fail-closed 原则；
  - PTY 写入成功后才正式提交 `pane.draft = draft`；若 PTY 写入失败，捕获并标记 `terminal_input_write_unknown`，草稿同样不更新；
  - 并发输入受 `pane.writes` 顺序 Promise 链保护，多个数据块严格串行执行，草稿状态不会交叉竞争错乱。
- **无错误吞噬与无兼容分支**：
  - 所有 `catch` 块均如实登记失败并再次抛出，无异常吞噬；
  - 彻底删除了旧版“每段按键均记录”的旧路径，没有留下兼容开关、shims 或并行的旧 API。

### 2. 正确性细节
- **退格与编辑键**：
  - 退格（`\x7f` / `\b`）：当 `cursor > 0` 时光标前移并通过 `splice` 删除前一个字符；
  - 光标移动（`←` / `→` / `Home` / `End` / `Delete`）：由 `SEQUENCES` 与控制字符处理，均有严密的 `Math.max(0, ...)` 与 `Math.min(draft.chars.length, ...)` 边界保护；
  - 编辑键（`←` 等）在发出时随 `content.keys` 准确记录（如 `green-1.json` 中的 `after_2` 记录了 `abdc` 与 `keys: ["←"]`）。
- **粘贴（Bracketed Paste）**：
  - 遇到 `\x1b[200~...` 标记时，整段文本插入草稿当前光标位置并更新光标，返回空数组，不单独产生记录；在后续用户按回车发出时作为整句发出。
- **清除键（Ctrl-C / Ctrl-D）**：
  - 遇到 `\x03` 或 `\x04` 时调用 `Object.assign(draft, emptyDraft())`，草稿彻底重置，未发出的草稿被清空且不留任何记录。
- **Esc 与控制序列**：
  - 单独 Esc（`data === "\x1b"`）：直接在终端层设置中断标记并向 PTY 发送 Esc，草稿模块直接 `return []`，不修改草稿，不记录用户输入；
  - 复合 Esc 序列（如方向键、功能键）：循环解析并作为编辑键处理；无法准确模拟的键（如 `↑`/`↓` 翻历史、`Tab` 补全）记录键名并标记 `text_uncertain: true`。
- **二进制与协议上报**：
  - 匹配 `protocolReport` 正则的鼠标报告、焦点报告不进入草稿，不记录用户输入；二进制输入进入草稿但标记不确定，不单独记录。
- **多回车处理**：
  - [`feedInput`](file:///Users/luckye/Documents/Code/a2a/workbench/src/inputDraft.ts#L43-L47) 遍历输入流，遇到每个 `\r` 或 `\n` 时，若积攒文本非空（`text.trim()`），均 push 一条记录并重置草稿；随后在 [`panes.userInput`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L1376) 循环中逐条 `await record(...)` 记录；空回车被过滤，不产生空白脏记录。
- **防 Agent 注入误记**：
  - Agent 消息经由 a2a 系统的 [`dispatch`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L1408)、[`wakeThread`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L1424) 及门禁回执注入，直接入队列 [`drain`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L1442) 写入 PTY，绝不调用 `userInput` 或 `recordInput`，不会被误记为用户输入。

### 3. 人工介入与指标一致性
- **门禁与指标一致**：
  - 门禁 [`gates.appendUserInput`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L581-L615) 会为每条 `user_inputs` 派生一条 `human_intervention` 事件；由于现在只在回车发送时记录一条，人工介入数与用户发出的消息条数严格 1:1；
  - 主测试 [`green-1.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-206/green-1.json#L76-L79) 证实 3 句发出消息对应 3 条记录与 3 次 `human_intervention`。
- **指标与紧急停止**：
  - [`workbench/src/metrics.ts:attention`](file:///Users/luckye/Documents/Code/a2a/workbench/src/metrics.ts#L99-L110) 的 `interventions` 统计用户在受管窗格提交的回车（`turn_submit_intent`，`source: "user"`）；
  - `stops` 依然按 `emergency_interrupt_intent` 以及写进终端的 Esc 字节（`terminal_input_write_intent` 且数据为 ASCII 27）统计；由于 Esc 依然作为字节写进终端，紧急停止指标计算逻辑依然完全成立。

### 4. 测试有效性与反事实证明
- **红态与变异体反事实**：
  - [`red-3.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-206/red-3.json)（在修前 commit `30ee51d30` 上执行）：精确在 `one_record_for_first_message`、`one_record_for_edited_message`、`cleared_draft_and_esc_not_recorded`、`interventions_follow_records` 4 项失败，终端字节项 `terminal_bytes_unchanged` 通过（记录为逐键产生的 29 条介入与输入）；
  - [`green-1.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-206/green-1.json)（修后）：5 项检查全部 `PASS`；
  - [`mutant-record-every-key.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-206/mutant-record-every-key.json)：精确在与修前相同的 4 项检查失败；
  - [`mutant-cursor-ignored.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-206/mutant-cursor-ignored.json)：仅在 `one_record_for_edited_message` 失败；
  - [`mutant-ctrl-c-keeps-draft.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-206/mutant-ctrl-c-keeps-draft.json)：仅在 `cleared_draft_and_esc_not_recorded` 失败；
  - 预期严格来自用户需求描述（用户输入整句回车后记录、退格与编辑正确反映、Ctrl-C 清除不记），而非实现的自带答案。
- **旧测试改动核对**：
  - 对 [`test_t157_turn_identity.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t157_turn_identity.ts)、[`test_t166_queued_input.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t166_queued_input.ts)、[`t108_answer_lifecycle_contracts.mjs`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/t108_answer_lifecycle_contracts.mjs)、[`test_t078_pane_runtime.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t078_pane_runtime.ts)、[`test_t078_permission_accounting.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t078_permission_accounting.ts)、[`t078_input_failures.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/t078_input_failures.py)、[`test_t145_mouse_reports_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t145_mouse_reports_e2e.py)、[`test_t133_t134_records_metrics_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t133_t134_records_metrics_e2e.py) 的断言调整，均系为了适配“发送才记录一条、未发出的单键与 Esc/单回车不记”的新规则；
  - 没有弱化底层物理校验（如终端字节接收、写锁顺序、Prompt ID 绑定、指标总汇等均完整保留），并在 [`test_t145`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t145_mouse_reports_e2e.py#L354) 中新增了 `unsent_key_not_recorded` 负例核验。

### 5. 文案与事实一致性
- [`workbench/README.md`](file:///Users/luckye/Documents/Code/a2a/workbench/README.md#L345) 准确更新了“受管 worker 直接输入继续记录人工介入：按回车发出时记一条完整消息，不逐键记录；Esc、Ctrl-C、单按回车等操作不单独记录，被 Ctrl-C 清掉的草稿不记”；
- 票据 T-206 验收条件与 [`evidence/2026-10-27-batch28/T-206/RESULTS.md`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-27-batch28/T-206/RESULTS.md) 记录完全相符；
- 未做事项均在 `RESULTS.md` 的“没做”部分真实说明。

---

## 审查问题清单

未发现 P1（阻断/严重错误）或 P2（功能缺陷）级别问题。仅记录 1 项已知设计层面的低优先级观察（P3）：

- **位置**：[`workbench/src/inputDraft.ts:36`](file:///Users/luckye/Documents/Code/a2a/workbench/src/inputDraft.ts#L36)
- **场景**：若粘贴内容中存在 Windows 风格的换行符 `\r\n`，`replaceAll("\r", "\n")` 会将其转换为 `\n\n`。由于受管窗格运行在 macOS/Linux 的 PTY 上，xterm.js 在 bracketed paste 模式下会将换行规范化为 `\r`，因此日常粘贴行为正常；且草稿按单行编辑器模拟多行内容，即使多行换行被回车发出时也是以整句记入。
- **严重程度**：P3

---

## 结论

**可合并**

---

## LIMITATIONS

1. **只读审查限制**：本次审查严格遵守独立审查员指令，仅使用了文件读取工具，未执行 shell 命令、未修改任何文件、未启动应用窗口或后台守护进程。所有测试运行结果与指标数据均直接核对自 `evidence/2026-10-27-batch28/T-206/` 及其子目录下的原始持久化 JSON 报告与 SQLite/日志文件。
2. **测试环境与 CLI 覆盖**：主端到端测试 [`test_t206_input_on_send_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t206_input_on_send_e2e.py) 仅在 Claude Code 环境下运行；Codex、agy 与 opencode 窗格依赖共享的 `panes.userInput` 抽象，本次未单独针对各个 CLI 进行端到端真机按键覆盖验证。
3. **复杂编辑场景的文字保真度**：单行草稿编辑器仅精确模拟了退格、左右光标移动、Home/End 与 Delete。对于 CLI 内部的多行换行编辑、历史命令翻找（上下箭头）、Tab 补全、Shell 专属的 Ctrl-U/Ctrl-K 等行编辑组合，草稿无法完全追踪 CLI 终端内部实际展开的字符缓冲区，此类消息均按规格标记为 `text_uncertain: true`，记录的文字可能与 CLI 最终解析的文字存在差异。
4. **历史测试执行缺陷**：`t078_input_failures.py` 改动的断言未在真实入口上复验，系因其上层测试脚本 `test_t078_input_entry.py` 仍在使用过时的前缀任务命名规范（T-123 之前的非项目限定任务名），导致门禁拒绝（`unknown_task`）；该项已在 `RESULTS.md` 中如实登记为“没做”。