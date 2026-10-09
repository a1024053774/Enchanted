---
id: T-047
title: 门禁 CLI 经 HTTP 调用 run 时提前超时
type: build
status: open
blocked_by: []
claimed_by: Codex T-047 worker
supersedes:
---

## What to build

T-046 中 `./a2a/scripts/gate` 的 run 请求在约 6 分钟时报 `TimeoutError: The operation timed out`（`evidence/2026-10-09-batch6/T-046/run-stderr.txt`），而服务端 run 继续并完成（run_finished completed）。`packages/a2a-gates/src/cli.ts:43` 的 fetch 未设超时，疑为 Bun fetch 或服务端 HTTP 的默认空闲超时。主控因此拿不到 run 的最终回执，只能轮询 events。查明超时来源，让主控可靠拿到 run 结果（例如显式超时与 wait_seconds 对齐，或 run 立即返回 run_id、由 status/events 查询结果），不改门禁契约语义。另：events 输出含未转义的控制字符，标准 JSON 解析会拒绝，一并查明。

## Acceptance

- [ ] 用真实工作台复现超时并保存证据，查明来源。
- [ ] 修复后一次超过 10 分钟的 run（可用受控夹具）主控能拿到最终回执；events 输出能被严格 JSON 解析。

## Resolution
