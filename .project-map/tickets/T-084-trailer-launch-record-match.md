---
id: T-084
title: 缺陷：提交尾注 Launch/Tool/Model/Effort 未与本 attempt 启动记录核对
type: build
status: closed
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

- [x] 红态在先：在当前 `main` 上经门禁真实入口提交一个 Launch（及另各一个 Tool、Model、Effort）与启动记录不符的候选，保存被放行的原始输出与命令。
- [x] 修复后同一入口对四种不符各自拒收为 `trailer_identity_mismatch`；与记录一致的正例与 spec 允许的 Model `unknown` 正例仍通过；完全无尾注仍按现契约记一次人工介入（6a 不变）。
- [x] 变异：在一次性副本里逐项去掉新加的 Launch/Tool/Model/Effort 比较，对应拒收案变为放行。
- [x] 期望值来自用户决定与启动记录本身，不读实现输出；不调用真实模型；`project_map.py status` 0 problems。

## 说明

- 2026-10-15 用户决定修订（answer `20261015T043855Z-ideation-answer-001`，逐字）："尾注这关直接拒收 (Recommended)"，选项原文："没有启动记录就无法核对，按你上次定的\"必须与启动记录一致\"直接打回，不让它走到审查。这条路径本来也集成不了，提前拒掉更干净；用到这条路径的旧测试要跟着改。"执行主控定拒收码 `trailer_launch_record_missing`（事件写明缺启动记录）。带 A2A 尾注但 attempt 无 delivery 的交付在尾注检查拒收；完全无尾注仍按 6a 记一次人工介入。先在当前候选取放行红态再修；README 第 91 行同步；用到 claim-only 路径的旧测试按新契约更新，不留旧行为开关。

- 来源：T-081 第 6e 项，用户决定（answer `20261015T030558Z-ideation-answer-001`，逐字）："补：必须与启动记录一致 (Recommended)"，选项原文："Launch 必须等于本 attempt 的启动记录号，Tool/Model/Effort 必须与那条记录一致（spec 允许 Model 写 unknown 的情形保留），不一致就打回。执行主控另开小票修，T-081 加对应的拒收案例。对应你说过的\"每一次代码提交都应该能追溯到\"。"
- 执行主控按 T-004 边界自建（`ready_by: executor`）。
- 写入范围：`workbench/src/gates/core.ts` 的尾注核对（必要时类型定义）与本票测试、证据。与 T-081 错开：T-081 的 6e 拒收案在本票合入后另加，不同时写同一文件；与 T-078 错开：T-078 的 core.ts 写入只限转交/调用者身份，不碰 `checkTrailers`。

## Resolution

**2026-10-15：执行主控验收 PASS，关闭。** 合入 main `c8d4e5d6`（变基后实现 `45aa68ef`、`e9c8aa47`；审查冻结候选 `9ddf446e`，变基前后 workbench/acceptance/scripts diff 为 0）。`checkTrailers`：受管 submit 有 `attempt.delivery` 时，Launch/Tool/Model/Effort 与启动记录逐项比对（仅 Model 允许字面量 unknown），不一致 `trailer_identity_mismatch`；带 A2A 尾注但无 delivery 时 `trailer_launch_record_missing`（事件 reason 缺启动记录）；完全无尾注仍记一次人工介入。证据 `evidence/2026-10-15-batch15/T-084/`：red/red-03 放行复现，green-04 全过，mutants-02/03/04 全 DETECTED；受影响旧测试按新契约更新。独立审查 01 NO_GO（测试不够格、无记录分支）→ 返工 → 审查 02 PASS。worker 为用户指定的 Grok 会话（无 A2A 启动记录，提交由执行主控代做、无 worker 尾注；打分因无启动记录不适用）。范围外发现：`test_daemon_recovery_e2e.py` 在基线 fb5dd288 上 5/5 失败，本票修到 4/5，剩余 `test_daemon_verify_interruption_and_operation_lock`（重启后 daemon 无审查配置）另开 T-085。
