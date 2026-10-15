---
id: T-084
title: 缺陷：提交尾注 Launch/Tool/Model/Effort 未与本 attempt 启动记录核对
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

`workbench/src/gates/core.ts` 的 `checkTrailers`（约第 1975–2000 行）对 9 条 A2A 尾注只核对 Task、Attempt、Session、Role 的取值；Launch、Tool、Model、Effort 只要求非空，伪造值会被放行（T-081 run 中已观察到）。

按用户决定补规则：Launch 必须等于本 attempt 的启动记录号；Tool、Model、Effort 必须与该启动记录一致；spec 允许 Model 写 `unknown` 的情形保留。不一致时拒收，拒收码 `trailer_identity_mismatch`（沿用现有码，不新增平行码）。启动记录取门禁已持有的本 attempt 运行身份；若门禁当前拿不到 Tool/Model/Effort 的记录值，先报告实际缺口并停下，不从尾注自身或其他提交推断。

## Acceptance

- [ ] 红态在先：在当前 `main` 上经门禁真实入口提交一个 Launch（及另各一个 Tool、Model、Effort）与启动记录不符的候选，保存被放行的原始输出与命令。
- [ ] 修复后同一入口对四种不符各自拒收为 `trailer_identity_mismatch`；与记录一致的正例与 spec 允许的 Model `unknown` 正例仍通过；完全无尾注仍按现契约记一次人工介入（6a 不变）。
- [ ] 变异：在一次性副本里逐项去掉新加的 Launch/Tool/Model/Effort 比较，对应拒收案变为放行。
- [ ] 期望值来自用户决定与启动记录本身，不读实现输出；不调用真实模型；`project_map.py status` 0 problems。

## 说明

- 来源：T-081 第 6e 项，用户决定（answer `20261015T030558Z-ideation-answer-001`，逐字）："补：必须与启动记录一致 (Recommended)"，选项原文："Launch 必须等于本 attempt 的启动记录号，Tool/Model/Effort 必须与那条记录一致（spec 允许 Model 写 unknown 的情形保留），不一致就打回。执行主控另开小票修，T-081 加对应的拒收案例。对应你说过的\"每一次代码提交都应该能追溯到\"。"
- 执行主控按 T-004 边界自建（`ready_by: executor`）。
- 写入范围：`workbench/src/gates/core.ts` 的尾注核对（必要时类型定义）与本票测试、证据。与 T-081 错开：T-081 的 6e 拒收案在本票合入后另加，不同时写同一文件；与 T-078 错开：T-078 的 core.ts 写入只限转交/调用者身份，不碰 `checkTrailers`。
