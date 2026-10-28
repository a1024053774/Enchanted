# T-207 独立审查报告

本审查由独立审查员完成。全程遵循只读约束，仅使用文件读取工具，未执行任何 shell 命令，未修改任何文件，未启动应用或后台服务。

---

## 1. 根因分析核对

**核对结论：相符。**

RESULTS.md 的根因链条与代码及试用原始事件完全吻合：
1. **工具钩子被拒**：用户按 Esc 后，`inputWindow`（`workbench/src/panes.ts:1372`）将 `pane.interrupted` 置为 `true`。用户随后输入内容并按回车启动新回合（Claude 通过 `UserPromptSubmit` 钩子触发 `user_prompt_unregistered`），但由于尚未执行放行（`releaseByUser`），`pane.interrupted` 依然保持 `true`。修前 `validateHookEnvelope`（`workbench/src/questions.ts:69`）对 `PreToolUse`、`PostToolUse` 等工具钩子硬性要求 `!pane.interrupted`，导致该用户回合内的所有工具钩子均被判定为 `question_turn_mismatch` 并抛出 `Refusal`。
2. **信任状态污染**：工具钩子校验失败后，`signal`（`panes.ts:1864`）捕获异常并记录 `native_question_unverified` 事件。根据 `currentTurnTrust`（`questions.ts:35-46`），一旦当前会话/提交出现 `native_question_unverified`，当前回合信任状态立即变为 `'unknown'` 且不可逆转。
3. **Stop 阶段拒收交付**：在回合结束到达 Stop 钩子时（`claudeStop`，`panes.ts:2009`；Codex 路径见 `panes.ts:1844`），均执行了 `check(currentTurnTrust(...) === 'verified', 'current_turn_untrusted')`。由于信任状态为 `'unknown'`，直接抛出 `current_turn_untrusted`，阻断了 `transfer`（文件转移入门禁中继目录）的执行，导致 worker 提交的交付请求 JSON 留在临时目录未被转移和受理。
4. **放行语义不补发**：用户随后在界面点击“放行”（`releaseByUser`，`panes.ts:1512-1516`）只重置了打断标记与状态并 drain 任务队列，并不主动扫描或处理请求目录中滞留的历史请求，导致门禁一直停留在 `claimed` 状态，必须等再跑一个回合且该回合成功 Stop 时才被顺带收下。

---

## 2. 身份核对与边缘场景分析

**核对结论：身份核对未放宽，逻辑严密。**

### (1) `active.interruption` 登记点
代码中仅在三处由用户输入触发新回合的地方为 `pane.active` 赋予 `interruption: pane.interrupted ? pane.interruption : null`：
- `panes.ts:1212`（Claude Code 忙时排队输入经本地 transcript 确认后转换为新回合）；
- `panes.ts:1392`（Codex 等非 Claude CLI 用户在终端输入并回车触发新回合）；
- `panes.ts:1819`（Claude Code 用户打字回车后，收到 CLI 报送的未登记 `UserPromptSubmit` 钩子）。
主控/门禁队列派发路径（`drain`，`panes.ts:1445`）在 `pane.interrupted` 时直接阻断不予发送，因此正常派发回合不会附带 `interruption`。

### (2) 关键边缘场景核对
- **被 Esc 打断的那个原回合**：
  - *Claude Code*：Esc 写入时调用 `retireClaudeSubmission(pane, "user-esc")`（`panes.ts:1402`），直接清除了 `pane.active` 和 `pane.claudePromptId`，原回合的迟到钩子因无 active/prompt mismatch 直接拒收。
  - *Codex*：Esc 写入时不退场，原回合 `pane.active` 是在 Esc 之前创建的，其 `active.interruption` 为 `null`/`undefined`。修后 `validateHookEnvelope` 要求 `pane.active.interruption != null && pane.active.interruption === pane.interruption`，由于 `null != null` 为假，被打断的原回合迟到钩子依然被拒收（单元测试用例 `turn_cut_off_by_esc` 证实）。
- **用户回合里再次按 Esc**：
  - 用户回合开始时绑定了打断事件号 $Seq_1$（`active.interruption = Seq_1`）。
  - 用户在该回合执行中再次按 Esc，PTY 写入新的打断事件 $Seq_2$（`pane.interruption = Seq_2`）。
  - 后续钩子到达时，`pane.active.interruption`（$Seq_1$）与 `pane.interruption`（$Seq_2$）不相等，立即被拒收（单元测试用例 `user_turn_cut_off_again` 证实）。
- **门禁打断（`interruptThread`）**：
  - `interruptThread`（`panes.ts:1524-1534`）同样设置 `pane.interrupted = true`，并将写入事件序号记入 `pane.interruption`。被门禁打断的原回合钩子同样因打断号缺失被拒；若用户随后在打断状态下手打新指令，新回合登记当前的门禁打断号，钩子可被正常受理。
- **窗格恢复（重启后重建的 active）**：
  - 窗格恢复路径（`restore`，`panes.ts:705`）显式初始化 `active: null, interrupted: false, interruption: null`。重启后启动的新回合在未被打断时走 `!pane.interrupted` 路径，行为正常。
- **Esc 写入前后短暂窗口的利用可能性**：
  - `inputWindow` 收到 `\x1b` 时同步置 `pane.interrupted = true`（此时 `pane.interruption` 尚未更新，若为首次打断则为 `null`）。所有写操作均排队进入 `serializeWrite`。
  - 在 PTY 写入完成前到达的钩子：因 `pane.interrupted` 为 `true` 且 `pane.interruption` 仍为 `null`，无法通过 `active.interruption != null && active.interruption === pane.interruption`，只能被拒绝。
  - 随后写入完成记录事件，`pane.interruption` 赋值为事件序号。因此不存在可被利用绕过核对的时间窗口。
- **其他依赖 `!pane.interrupted` 的路径**：
  - `PermissionRequest`：`questions.ts:66` 与 `panes.ts:1775-1786` 均未检查 `!pane.interrupted`，不受影响。
  - Stop 路径：Claude Stop、Codex Stop、OSC 7501 Reported Stop 对已匹配的当前回合均未硬编码 `!pane.interrupted` 检查，仅检查 `currentTurnTrust(...) === 'verified'`。只要工具钩子不再被误判为 unverified，Stop 均能正常进入 `transfer` 完成交付。
  - 原生问题作答（`answerQuestion`）：`panes.ts:2083, 2097` 依然显式检查了 `!pane.interrupted`。RESULTS.md 在“看到但没改”中如实说明：被打断后的用户回合中若模型调用原生提问工具，界面无法答复，只能在终端直接键入。这不影响本票（交付受理）的范围。

---

## 3. 架构与改动完整性

**核对结论：改动最小，无坏味道。**

- **无吞错**：改动未新增任何 `try-catch` 或异常吞噬逻辑。
- **无兼容分支或平行路径**：未引入新的降级接口、平行 API 或 shim 兼容层。
- **改动最小性**：生产代码改动极精简：
  - `panes.ts`：仅在 `Pane['active']` 类型上增加可选属性，并在 3 处用户回合激活处赋值 `interruption: pane.interrupted ? pane.interruption : null`；
  - `questions.ts`：仅在 `validateHookEnvelope` 的工具钩子检查中，将 `!pane.interrupted` 精确修正为 `(!pane.interrupted || pane.active.interruption != null && pane.active.interruption === pane.interruption)`。

---

## 4. 测试与变异体验证

**核对结论：测试有效、证据完整，预期忠实于需求。**

### (1) 端到端真实入口测试（`test_t207_user_turn_delivery_e2e.py`）
- **修前红态（`red-2.json`，revision `f5ae30f78`）**：
  - 在派发长命令中途按 Esc，再打字回车，worker 在该回合提交交付；
  - 结果：`delivered_at_turn_end` 超时失败（门禁停留在 `claimed`），8 个工具钩子出现 `question_turn_mismatch`，Stop 钩子报 `current_turn_untrusted`，精准复现 UAT-03 现场缺陷。
- **修后绿态（`green-1.json`）**：
  - 相同流程，4 项检查全部通过；回车后 6.8 秒门禁变为 `submitted`，无 `user_queue_release`，无多余回合，窗格维持 `interrupted: true`（打断语义未改变）。
- **变异体验证（`mutant-user-turn-not-marked-2.json`）**：
  - 变异：用户回合不登记 `interruption`（保持 `null`）；
  - 结果：精准在 `delivered_at_turn_end` 与 `user_turn_hooks_trusted` 两项检查上失败，且错误特征与修前完全一致，证实端到端测试对该机制具备区分能力。

### (2) 单元反例测试（`test_t207_interrupted_turn_hooks.ts`）
涵盖 7 个针对性用例，5 份测试结果对比：
- `hooks-green-1.json`（修后）：7 项全部通过。
- `hooks-red-f5ae30f78.json`（修前）：仅在两个打断后的合法用户回合用例（Codex、Claude）上失败，其余反例本就拦截。
- `hooks-mutant-no-interrupt-check.json`（完全移除打断检查）：`turn_cut_off_by_esc`、`user_turn_cut_off_again`、`no_recorded_interruption` 3 个反例被错误放行并导致测试失败。
- `hooks-mutant-any-interruption.json`（只判断非空，不比对是否相等）：`user_turn_cut_off_again` 被错误放行并导致测试失败。
- `hooks-mutant-null-equals-null.json`（移除 `!= null` 判断）：`no_recorded_interruption` 因 `null === null` 被错误放行并导致测试失败。

---

## 5. 顺带修改的 `test_t078_empty_declaration_entry.ts` 评估

**核对结论：修改合理，未削弱非相关检查，三版本对照充分支持结论。**

1. **补夹具 `draft` 字段**：
   - T-206 在 `panes.ts:1376` 引入了 `pane.draft` 管理机制。生产代码中所有 pane 创建处均包含 `draft: emptyDraft()`。
   - `test_t078_empty_declaration_entry.ts` 采用手写 mock pane 夹具，缺少 `draft` 属性，导致 `inputWindow` 访问 `pane.draft.chars` 时抛错。补充 `draft: {chars:[],cursor:0,keys:[],uncertain:false}` 属于修复测试夹具缺陷，使之符合产品契约。
2. **修改 `controls_are_actions_not_messages` 预期**：
   - T-206 用户裁定要求：“只记录我发送之后的完整消息,不要每次操作都要记录”。
   - 旧用例预期将 Ctrl-C、Ctrl-U 等控制键在没有回车时单记为 `action`，与 T-206 明确要求相悖。
   - 修改后断言 `rows` 为 `[]`（不记录未提交的控制键），同时继续严格断言 `f.writes` 包含了所有键位原始字节（`assert.deepEqual(f.writes, ['\x03','\x15','\x13','\x1b[A'])`），验证了按键正常下发给终端，并未削弱测试。
3. **三版本对照证据核对**：
   - `pre-t206-t078-empty-decl.out`（commit `30ee51d30`，早于 T-206）：失败 5 项。
   - `base-t078-empty-decl.out`（`f5ae30f78`，含 T-206）：失败 11 项（原 5 项 + 夹具缺 draft 影响 5 项 + 控制键记录断言 1 项）。
   - `t078-empty-decl-3.out`（改后）：完全恢复到原本的 5 项失败。
   证实剩下的 5 项确实早于 T-206，与 T-206 及本票均无因果关系。

---

## 6. 文案与事实一致性

- **票的验收条件对齐**：
  - 验收 1（修前真实入口复现）：有 `red-2.json` 证明。
  - 验收 2（修后相同操作交付直接被受理，无需多跑一回合）：有 `green-1.json`（回车后 6.8s 自动转为 submitted）证明。
  - 验收 3（身份核对不放宽）：有 `hooks-*.json` 变异矩阵及 7 个用例证明。
- **未做事项说明**：
  - Codex 真实入口未跑（仅有 Claude Code 真实入口，Codex 走单元测试）；
  - 放行时处理请求目录的替代方案未做（按用户选择执行）；
  - `answerQuestion` 在打断状态下仍阻断界面作答。
  上述内容在 RESULTS.md 中均如实记录。

---

## 问题列表

经全面代码与测试审计，**未发现 P1、P2 或 P3 级别缺陷**。

---

## 审查结论

**可合并**

---

## LIMITATIONS

1. **只读审查边界**：本审查未在当前环境下直接执行 `python3 test_t207_user_turn_delivery_e2e.py` 或 `node workbench/tests/test_t207_interrupted_turn_hooks.ts`，所有测试结果与变异结论均基于已有执行报告、落盘 JSON 摘要及源码逻辑推导。
2. **Codex 真实交互未行端到端实测**：虽然单元测试充分覆盖了 Codex 的 hook envelope 校验逻辑，但 Codex 原生进程在 Esc 打断后再接收用户回车的真实 Electron + xterm 端到端行为未在此次 e2e 脚本中运行（e2e 仅针对 Claude Code）。
3. **未查项**：`test_t078_pane_runtime.ts` 的 `interrupt_only_esc_not_reclaim` 失败及 `test_native_final_read.ts` 在基线上的历史失败，核对确属早于本票的历史现象，未作进一步根因展开调查。