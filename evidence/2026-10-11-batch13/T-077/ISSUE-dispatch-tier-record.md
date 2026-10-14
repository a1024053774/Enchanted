# 合流时核对 dispatch_intent 的速度请求标签

本分支固定候选 2e2291ac 的 `workbench/src/gates/core.ts:1367` 附近，claim 的 dispatch_intent 仍写 `requested_service_tier: "fast"`；生产 Panes 当前 argv 已显式传 default，launch 记录为 default，用户也已决定所有 Codex 会话 default。

这是速度切换后的记录字段未同步，可能误导后续事件/指标读回。当前受控尾注证明不检查或修改该字段，不应借此扩大测试期望或改产品；请执行主控在与 T-076-2 合流时核对并保留双方意图，必要时由对应责任切片处理。建议让该事件记录与实际启动请求一致。

本次只报告，非阻塞；尾注拒收/集成证明继续按原范围准备。
