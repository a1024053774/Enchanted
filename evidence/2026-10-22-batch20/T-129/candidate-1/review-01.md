# 独立代码审查报告：T-129 候选 1（提交 `b3bd8aa84` 与 README 补充 `03965053`）

- **审查对象**：
  - 提交 [`b3bd8aa84`](file:///private/tmp/claude-501/-Users-luckye-Documents-Code-a2a/193bb4d9-d8a5-4f5f-9e0a-4a1f8bbc5df3/scratchpad/agy-t129-eN54/full.diff)（父提交 `400db6611`）
  - 文档补充 [`03965053`](file:///Users/luckye/Documents/Code/a2a/workbench/README.md#L395)
- **代码改动**：只涉及 `workbench/`（[`daemon.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L558)、[`test_t122_claude_worker_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t122_claude_worker_e2e.py#L58-L130)、[`README.md`](file:///Users/luckye/Documents/Code/a2a/workbench/README.md#L395)）
- **核对证据**：
  - 结果报告：[`evidence/2026-10-22-batch20/T-129/candidate-1/RESULTS.md`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-129/candidate-1/RESULTS.md)
  - 端到端证据：[`e2e/commands.sh`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-129/candidate-1/e2e/commands.sh)、[`e2e/exits.txt`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-129/candidate-1/e2e/exits.txt)、各 JSON 摘要与报错日志
  - 真实运行：[`evidence/2026-10-22-batch20/T-129/real/`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-129/real/)、[`ui-driver.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-129/real/real-01/ui-driver.json)、[`readback.json`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-129/real/real-01/readback.json)
- **审查模式**：只读独立审查，未执行任何修改、未运行任何 shell 命令或文件写入。

---

## 重点核查结果

### 1. 修复的正确性与完整性

#### 1.1 两条失败路径是否完整
在 [`workbench/src/daemon.ts`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L550-L618) 的 `signal` 处理流程中，Claude reviewer 原有两条异常分支：
1. **协议解析失败路径**（[`daemon.ts#L558`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L558)）：当 `reviewRequest(stop.last_assistant_message)` 抛出 `QualityProtocolError`（最终消息非 JSON 或缺少必需字段）时，原实现只传入 `{ ...identity, native_session: stop.session_id }`，现补入 `prompt_id: stop.prompt_id`。
2. **门禁校验拒收路径**（[`daemon.ts#L613`](file:///Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts#L613)）：当 `review_submit` 格式合规但被门禁规则拒绝（`!receipt.result.ok`）时，原实现同样遗漏 `prompt_id`，现补入 `prompt_id: stop.prompt_id`。

经全库检索，`workbench/src/daemon.ts` 内部向 [`panes.caller`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L1596) 获取调用者身份的调用点恰好只有 3 处（L558 协议失败分支、L574 正常中继分支、L613 门禁拒收分支）。修复后，三处传入的身份参数形态完全一致，**不存在其他以缺少字段身份调用 `panes.caller` 或 `gates.failReviewProtocol` 的遗漏点**。

#### 1.2 对 Codex reviewer 的影响
**无不良影响，完全兼容。**
在 [`workbench/src/panes.ts#L1628-L1646`](file:///Users/luckye/Documents/Code/a2a/workbench/src/panes.ts#L1628-L1646) 中，`caller` 方法对 `Claude Code` 与 `Codex` 进行了明确分支：
- 若为 `Claude Code`，核对 `identity.prompt_id` 并将其作为 `turn`（未传即触发 `native_identity_required`）；
- 若为 `Codex`，执行 `this.scan(pane)` 扫描原生日志获取 `pane.turn`，只核对 `pane.turn` 与 `identity.native_session === pane.native`，不读取也不强制要求 `identity.prompt_id`。

因此，向 `panes.caller` 传入额外的 `prompt_id` 对 Codex reviewer 完全透明无副作用。证据中的回归测试 `t124-restart-verified`（Codex worker + reviewer）与 `t127-green`（Codex user home）均 0 退出通过，印证了对 Codex 的无破坏性。

#### 1.3 任务状态（`paused`、审查 `unknown`）是否满足“回到可重审状态”的要求
根据门禁既有设计契约（详见 [`findings/ticket-gates-graph-2026-10-16.zh-CN.md`](file:///Users/luckye/Documents/Code/a2a/findings/ticket-gates-graph-2026-10-16.zh-CN.md#L279) 节点 E68 与 R2 异常态，以及 [`workbench/src/gates/core.ts#L2496-L2515`](file:///Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts#L2496-L2515)）：
- 审查结论格式破坏协议或被门禁拒收不属于正常的业务打回（不计入同一 attempt 的 3 次修复上限，不触发 `rejectDelivery`），必须将 `review.state` 置为 `unknown`、`task.state` 置为 `paused`，追加持久化事件 `review_protocol_failed` 并挂载阻塞型 `qualityIssue`。
- **与修前对比**：修前版本因 `panes.caller` 抛出 `native_identity_required`，导致 `failReviewProtocol` 根本未被执行，任务死锁在 `reviewing` 直至超时；修复后任务成功退出 `reviewing` 死锁，转入受管暂停态（`paused`）。
- **重审机制边界**：门禁设计要求操作严格保证可追溯性。任务处于 `paused` 且审查处于 `unknown` 时，门禁不提供就地直接无感重跑单次审查的隐式旁路（`verify` 明确校验 `task.state === 'submitted'`，见 `core.ts:3788`）。主控或用户可通过处理该 `qualityIssue` 并执行 `reclaim` / `revoke` / `revise`，或者由受管 `run` 的恢复机制发起新 attempt 重新进入审查流程。这完全符合门禁状态机合同。

---

### 2. 测试独立性与坏实现区分能力

1. **测试设计独立性**：
   [`workbench/tests/test_t122_claude_worker_e2e.py`](file:///Users/luckye/Documents/Code/a2a/workbench/tests/test_t122_claude_worker_e2e.py#L83-L130) 在真实后台与 node-pty 环境下执行，通过脚本化 Messages 端点注入两类输入：
   - `--review-result malformed`：注入自然语言文本 `审查完毕，可以合并。`（触发路径 1：`QualityProtocolError`）；
   - `--review-result rejected`：注入格式合法但 `candidate_commit` 为 40 个 `0` 的失配数据（触发路径 2：门禁 `review_candidate_mismatch` 拒收）。
2. **坏实现区分能力（反例与变异）**：
   测试中构造了两个最小变异体：
   - `protocol-failure-unbound`：仅去除路径 1 的 `prompt_id`；
   - `rejection-unbound`：仅去除路径 2 的 `prompt_id`。
   在 [`e2e/commands.sh`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-129/candidate-1/e2e/commands.sh) 的验证中：
   - 修前父版本 `400db6611` 在两类场景下均失败（`AssertionError: stop_transfer_failed: [{'error': 'Error: native_identity_required', 'state': 'unknown'}]`）；
   - 两个变异体各自在对应的场景下精准失败（退出码 1）；
   - 只有完整修复的绿态版本能通过全部 16 项检查并退出 0。证明测试并非“答案抄实现”，能有效辨识单边遗漏或未修复的坏实现。
3. **期望值来源**：
   断言期望值来自门禁底层 `failReviewProtocol` 契约（事件含 `{error: 'review_json'}` 或 `{receipt_ok: false}`，状态为 `paused` 与 `unknown`），源于既有规范定义，来源独立。

---

### 3. RESULTS.md 真实性与证据比对

经逐项对照原始证据与日志：
1. **测试数据一致性**：
   - `e2e/exits.txt` 中各测试项退出码与表内一致；
   - `green-malformed.json` 与 `green-rejected.json` 真实包含全部 16 项检查通过断言；
   - 3 项回归运行项数（23、26、19）与证据文件无偏差。
2. **真实运行支持情况**：
   - 真实运行脚本 [`real/t129run.sh`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-129/real/t129run.sh) 与驱动 [`real/t129drive.mjs`](file:///Users/luckye/Documents/Code/a2a/evidence/2026-10-22-batch20/T-129/real/t129drive.mjs) 真实驱动了 Claude Sonnet 5.5（medium）走完主控申请、批准、派发 worker、交付、审查与集成全流程；
   - `RESULTS.md` 表述非常克制客观：明确指出了**真实运行走的是正常路径**（Sonnet 5.5 返回了合规的 review JSON 报告，审查通过并合入 main），失败路径的判定依据来自脚本化端到端矩阵，未夸大宣称真实模型触发了该失败路径；
   - 客观记录了 worker 提交尾注中 `A2A-Model` / `A2A-Effort` 为 `unknown` 的已知非回归问题；
   - 夹具与截图归档清单符合 T-088 策略。

---

### 4. 审查发现清单

经对 diff、实现代码及测试用例的深入代码审查：

**无发现（No Findings）**。
- 没有发现任何阻断性或功能性缺陷（P0 / P1）；
- 没有发现设计劣化或边缘漏洞（P2）；
- 没有发现遗留代码或风格问题（P3）。代码修复位于根因层，为最小必要变更，符合简洁性与高内聚原则。

---

## 总体审查结论

**PASS**
