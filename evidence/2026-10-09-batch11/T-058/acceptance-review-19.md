STATUS: FAIL
TARGET: 冻结候选提交 `9f29f66b3c8566d6c6c945dc43e12b207e197404`

EVIDENCE:
- spec 第 5 节明确规定条目方向：`assign/revise/cancel` 为 ideation→executor，`report/needs-decision` 为 executor→ideation（`controller-split-user-input-2026-10-09.md:255-266`）。
- 冻结核对：`git rev-parse HEAD` 返回候选提交；审查期间 HEAD 未变化。
- 定向无模型探针经真实 `A2AGates.call`，executor caller 发送 `kind=assign,to=executor`，返回 `wake_undelivered`，但已生成 `from=executor,to=executor` 的条目。
- 现有定向测试仍通过：inbox 6/6、capabilities 2/2；既有 transport/real evidence 不覆盖该方向反例。

FINDINGS:
- [P1] `packages/a2a-gates/src/core.ts:1544`（追加于 `:1624`）— `inboxCall` 未按 spec 校验普通条目的发送者/接收者方向，executor 可写入非法 `assign` 条目；在追加前加入完整 kind-direction 校验。

COUNTEREXAMPLE:
- 输入：executor 凭据调用 `a2a_inbox_send({kind:"assign",to:"executor",body:"direction sentinel"})`。结果：条目被追加，未因方向非法拒绝；因此该反例未被候选拒绝。

LIMITATIONS:
- 未修改候选或外部状态；仅运行了定向无模型检查。发现的可达违约已足以阻止 PASS。

RULE:
- 在真实 MCP/HTTP/CLI 验收 oracle 中为每种 kind 增加不允许的 sender/recipient 组合，并断言请求在追加前失败、收件箱无新记录。
