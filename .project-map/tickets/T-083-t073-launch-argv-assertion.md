---
id: T-083
title: 缺陷：T-073 启动/尾注测试仍断言 service_tier="fast" 且无 --no-daemon
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

`acceptance/test_herdr_traceability_e2e.py` 的 `Contract.assert_trailers`（约第 117 行）断言启动 argv 含 `-c service_tier="fast"`、完整列表里没有 `--no-daemon`。当前 `scripts/launch-worker` 按用户决定始终传 `--no-daemon` 与 `-c service_tier="default"`（`--service-tier fast` 仅显式可选）。测试期望过期，运行整套 T-073 启动/尾注测试会拒绝当前正确的启动策略。

只改该测试的期望，使之与当前启动器一致；不改启动参数去迎合旧断言。

## Acceptance

- [x] 红态在先：在当前 `main` 上运行受影响的 T-073 启动/尾注测试，保存因旧期望（fast、无 --no-daemon）失败的原始输出与命令。
- [x] 改期望后同一命令通过；期望值来自用户原话与 `scripts/launch-worker` 的固定 argv，而不是读取实现输出。
- [x] 变异：把 `scripts/launch-worker` 的 tier 改回 fast 或去掉 `--no-daemon`（仅在一次性副本里），改后的测试按业务断言失败。
- [x] 不调用真实模型；`project_map.py status` 0 problems。

## 说明

- 来源：T-080 worker 范围外上报 issue `20261014T173521Z-worker:s14-t080-issue-001`；构思主控 2026-10-14 确认属已批准范围内的测试过期缺陷，由执行主控按 T-004 边界自建（`ready_by: executor`）。
- 依据：用户 2026-10-13 原话（逐字）"以后只用 gpt6.1sol xhigh,不用 astra 了，那个消耗额度太快了，也不用 fast。"，以及速度覆盖决定 B（answer `20261013T142903Z-ideation-answer-001`，每会话显式 `service_tier="default"`）。
- 写入范围只限 `acceptance/test_herdr_traceability_e2e.py` 与本票证据；与 T-081 的 acceptance 写入错开（T-081 不改此文件）。

## Resolution

**2026-10-14：执行主控验收 PASS，关闭。** 合入 main `e2ff2fa9`。只改 `acceptance/test_herdr_traceability_e2e.py:117` 两处期望（加 `--no-daemon`、`service_tier="fast"`→`"default"`）。红态 3 failures（main 原期望）→ 绿态 7/7；launch-worker 副本改回 fast 或去掉 --no-daemon 的两个变异体各 3 failures，均在 argv 相等断言。独立审查 PASS、0 发现。证据 `evidence/2026-10-14-batch14/T-083/`。来源 issue 20261014T173521Z 已关闭；worker 另报的 intent/任务卡模板仍写 Fast（issue 20261014T190348Z）已转构思主控。
