---
id: T-008
title: 受管任务自动推进与有界结束
type: build
status: closed
blocked_by: [T-007]
claimed_by:
supersedes:
---

## What to build

把已验证的分派、观察、显式提交、独立验收、集成与回收连成程序负责的一个受管运行入口，
让 controller 不必记住并逐条调用操作手册。沿用现有门禁和数据来源，不新增第二套任务状态。
调用方显式指定等待期限；到期、被撤销、验收失败或外部副作用未知时保留诊断并结束，
不以终端 done 代替交付，不自动重发模型任务。只处理该 run 启动的 attempt，不能接管后续替换者。
首个目标仍为单机 Codex/Herdr；[冻结运行契约](../specs/supervised-run-2026-10-06.md) 已依据 T-007 定义。

## Acceptance

- [x] 一条真实运行命令完成分派到独立验收和集成，模型仅负责实现和显式 submit。
- [x] 无 submit、撤销或期限耗尽不产生成功状态；每次失败保留可复现证据。
- [x] 原 attempt 被替换后，旧 run 不能验收、集成或关闭新 worker。
- [x] 正常结束与可核对失败及时回收自己的 pane；未知身份不猜测关闭。
- [x] 真实 Herdr/Codex 入口、反事实与独立审查通过，旧门禁没有回归。

## Resolution

PASS，2026-10-06。固定候选 907672e1d362c99f5b2173d40f58af47423241c0。
编排18/18、原门禁8/8、恢复9/9；真实run完成，并独立读回12项oracle。
真实辅助进程误拒绝已修复；反事实及固定候选独立审查通过。
完整命令、失败与分层证据见 [RESULTS.md](../../evidence/2026-10-06-run-01/RESULTS.md)。
