STATUS: FAIL
TARGET: /Users/luckye/Documents/Code/synara at cb9deaea46245c04561778202cdb72b907d2dd6e

本文件保存决定 02 授权的第二次 fresh-context 只读审查结论；以下为审查消息的中文转录。审查 agent：`/root/t056_final_review`，acceptance-auditor。

EVIDENCE:
- 候选保持冻结；fork 只有不属于本票的 `.grok/` 未跟踪文件；代码 diff 检查通过。
- `resume-red-30` 退出 1，`final-resume-32` 退出 0；两次 reconcile 请求分别成功和被业务 CAS 拒绝，各记一条输入。
- 核对 `boundaries-resume-33`、`source-loss-14`、`scope-recovery-20`、`checkpoint-23`、`migration-14`、`extras-16` 的来源、去重、gap、恢复和迁移证据。
- `native-authoritative-replay-34` 由当前候选读取真实 Codex 0.162.0 的权威事件。
- 只读隔离现场有 19 条 user_inputs、2 条 human_intervention、checkpoint 74。

FINDINGS:
- [P1] `apps/server/src/a2a/userInput.ts:21`：`thread.message.edit-and-resend` 和 `thread.checkpoint.revert` 未进入 `userCommandInput` 的枚举，default 直接返回；真实 WS 入口没有记录。`apps/server/src/a2a/orchestration.ts:114` 的恢复事件集合也漏掉对应事件。spec 第 3 节要求在派发入口记录重试等非消息输入。建议补命令枚举、恢复分类和去重证据。

COUNTEREXAMPLE:
- 从真实 WS 发送合同有效的 `thread.message.edit-and-resend`，外部文本为“重试 Ω”。合同会产生 `thread.message-edit-resend-requested`，但当前入口不记录输入；若 provider 失败，不能依赖后续用户消息补齐。`coverage-matrix-03.py:136` 的矩阵未包含它。

LIMITATIONS:
- 主矩阵禁用 provider，结构化回答和审批用哨兵 request ID；真实外部边界证据为 Codex 异步问答及权威事件重放。
- 未审查生产环境、ticket 关闭或视觉外观。
- 该 FAIL 属于 cb9 冻结候选，后续修正不能继承为新候选的审查结论。
