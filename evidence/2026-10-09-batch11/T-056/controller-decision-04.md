# T-056 执行主控决定 04（2026-10-09）

针对 RESULTS-04、问题 20261009T203240Z-worker:s11-t056-issue-001 / -002。缺陷级，在已批准范围内，执行主控自主安排。

1. **受管结构化答复的人工介入显示（issue-002）**：执行主控核对源码，`userInput.ts` 对 `thread.user-input.respond` 设 `target.message: null`，`humanIntervention.ts:33` 对 answer 要求非空 message 键，风险成立。请：
   - 在 dd 上用真实入口取红态：受管 attempt 内经 WS `dispatchCommand` 发结构化答复（真实 request 目标，可用受控 provider 状态，不需要真实模型），核对 SQLite 的 human_intervention，再交实际 web 解析器；
   - 最小修正：解析器按输入实际形态接受“无 message、有 request 的 answer”，继续拒绝消息形态答复缺身份；不发明 messageId，不吞格式错误；
   - 红绿保存，并补一个已知坏实现反例（例如把所有 answer 都放行的 mutant 被拒）。
2. **gap 分支补验（issue-001）**：在最终候选上用 fork 的 `a2a/scripts/bun`、正确 cwd、新隔离目录与完整版本收据，验证普通输入与 ingress 同时失效时业务继续、重启只补 gap、再次重启不重复且不派生人工介入。
3. 之后跑相关检查（server/web 相关测试、typecheck、lint、既有 35 项）。**不再启动独立审查**；执行主控自己审查本轮差异与证据后决定关闭。
