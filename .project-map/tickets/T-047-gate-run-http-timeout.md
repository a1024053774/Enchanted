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

- [x] 用真实工作台复现超时并保存证据，查明来源。
- [x] 修复后一次超过 10 分钟的 run（可用受控夹具）主控能拿到最终回执；events 输出能被严格 JSON 解析。

## Resolution

2026-10-09：**PASS，待主控关闭**。保持 `status: open`。

- 真实工作台失败来源为任务书提供的 T-046 原始材料；本次遵循任务书禁触正式工作台的限制，在自建隔离服务上经真实 gate CLI、HTTP 路由和门禁核心重新复现。默认客户端 360.335 秒超时，缩短 Bun 客户端空闲期限后 8.195 秒超时，两次服务端均继续完成，确认根因为 Bun fetch 客户端空闲计时。
- fork 候选 `5aaf90ac1406250a037593448725730973849102`（基线 `09fc57f8a67ea2a1ed70397c04e49e9bb4849a5b`）仅对 run 设置 `timeout: false`，保留原门禁提交等待、阶段期限、锁及 attempt 绑定语义，更新工作台说明。
- 受控夹具在 610 秒后显式 submit，CLI 于 611.583 秒收到最终成功回执；独立 oracle、真实 Git 集成引用读回、原 attempt 回收及严格 JSON 解析通过。run_deadline、run_blocked、run_busy 反例符合冻结契约。
- T-046 指定的 events 原件严格 JSON 解析已通过；本次含 NUL、SOH、ESC、tab、CR、LF 的原始 events 亦通过。未证实序列化缺陷，未增加修补路径。
- 格式、lint、相关类型检查和 Vitest 通过；冻结候选一次独立 behavioral-acceptance-review 返回 PASS、无发现。只验证本地 HTTP 门禁和受控原生线程边界，没有调用模型、构建桌面或重启正式工作台。已停本任务创建的 7 个服务并保留完整夹具归档。
- 完整命令、红绿态、反例、源码版本、审查及限制见 [中文报告](../../evidence/2026-10-09-batch7/T-047/RESULTS.md)。
