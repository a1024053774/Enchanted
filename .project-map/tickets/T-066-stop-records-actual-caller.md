---
id: T-066
title: 紧急停止的核心记录写实际调用者，不再一律记成构思主控
type: build
status: superseded
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: ideation
ready_rev: 1
---

## What to build

[T-064](T-064-role-permission-settings.md) 按执行主控决定 02 接受了一个局限：`a2a_stop` 以 ideation 地址调用核心，用户在设置页授予 stop 的其他角色，它们发起的停止在核心记录里也记成 ideation；核心事件 `emergency_interrupt_requested`（fork `49cae984f` 的 `packages/a2a-gates/src/core.ts:1701`）只存 stop_id、被中断的目标 thread 和调用地址，没有调用者 thread/turn（上报 `20261010T084028Z-worker:t064-issue-001`）。

追加式记录的用处就是看得出谁做了什么，这个局限让停止记录不可信。用户同意改（逐字："你建议改的一处我同意"）。

改成：核心记录写实际调用者的角色地址，以及调用者的 thread 与 turn（取自网关凭据，不取自参数）；被中断的目标 thread 照旧单独一栏。

## Acceptance

- [ ] 红态在先：在 `49cae984f` 上，一个被用户授予 stop 的非构思主控角色（例如执行主控）调用 `a2a_stop`，核心记录的地址为 ideation、无调用者 thread；保存输出与重放命令。
- [ ] 修复后同一场景：核心记录的地址为实际角色，带调用者 thread、turn；目标 thread 不变。构思主控自己的 stop 记录不变。
- [ ] 身份取自凭据：参数里伪造调用者 thread 或角色被忽略（反例）。
- [ ] stop 的放行条件（`stop` 条目超过 2 分钟无 `ack`）不变，既有 stop 用例照常通过；只中断、不做别的。
- [ ] 历史记录不改写：旧事件按原样保留，读取端对缺调用者字段的旧事件如实显示"未记录"，不补猜。
- [ ] 既有套件、typecheck、lint 通过；对上游文件的改动列清单（预计无上游文件）。

## 说明

- 失败方式清单（处理方式写进 RESULTS）：调用者凭据已失效；同一目标被两个角色先后 stop；stop 与 `ack` 交叠；旧库缺新列。
- 授权来源：用户 2026-10-10 同意构思主控的建议（逐字："你建议改的一处我同意"）；`ready_by: ideation`，`ready_rev: 1`。

## Resolution

PAUSED（主控挂起，等方向结论）（2026-10-10，⟦主控 #28⟧）。已停止本次隔离服务端与 UI 探针，不再修改 fork，不启动独立审查。ticket 保持 open，Acceptance 未勾选，待主控后续决定；最终关闭仍由主控负责。

暂停前已有 fork 提交 `ddb765956cae4a4d0b87b875970601068567ed93`，保留原位，未丢弃或改写历史。按主控命令对本票 11 个路径执行 stash（排除他人的 `.grok/`），结果为 `No local changes to save`，没有创建 stash：当时仅 `.grok/` 未跟踪，代码已经提交，不能通过 stash 保存已提交内容。此候选未完成界面验收与独立审查，不作为 PASS 或 fork 交付。

基线红态、候选相关检查、真实 MCP 与旧库证据、所有失败、暂停现场见 [RESULTS](../../evidence/2026-10-09-batch11/T-066/RESULTS.md)。决定 01 的接入批准已挂起，后续等方向结论。

**作废（2026-10-10）**：方向改为原生 CLI 编排（[T-069](T-069-third-stage-direction.md)），本票不再推进；fork 上未推送的 `ddb765956` 保留不推，新载体上随 [spec](../specs/native-cli-orchestration-2026-10-10.md) 第 12 节 S4 重做。现场与证据保留。
