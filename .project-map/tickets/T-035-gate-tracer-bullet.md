---
id: T-035
title: 门禁 tracer bullet：一次受管任务的正常路径
type: build
status: closed
blocked_by: [T-034]
claimed_by: Codex worker T-035（主控 Claude Code wF:pM）
supersedes:
---

## What to build

用户（或主控 agent）在 Synara 里为一个项目新建受管任务：门禁冻结任务输入与独立 oracle，经 Synara 派出一个 Codex worker 会话（worktree 环境，起点为集成头）；worker 改好代码、本地提交后，用 `a2a_submit` 工具显式交付；门禁在独立 worktree 中运行 oracle，通过后以 CAS 写入集成引用，回收 worker 会话；任务窗口上显示 accepted。本切片只走正常路径；第一步核实 Synara 是否已有 thread 分组、turn 完成信号与内部创建 thread 的接入点。设计见 [spec](../specs/synara-m1-2026-10-07.md) 的"层级模型""门禁""界面"。

## Acceptance

- [x] 门禁核心位于独立 package，状态变更只经该核心；对上游文件的改动有清单。
- [x] 在隔离数据目录中，真实 Codex worker 会话完成分页夹具并经 `a2a_submit` 交付；thread 结束或空闲本身不推进状态。
- [x] 独立 oracle 在新 worktree 中运行通过，集成引用经 CAS 更新并能独立读回；worker 会话被回收。
- [x] 任务窗口显示该任务的门禁状态变化（截图或录屏存档）。
- [x] 反例：未调用 `a2a_submit`、或提交身份不符时，任务不会进入验收或集成。

## Resolution

PASS（2026-10-07），仅限上述五项。保持 status=open，待主控关闭与更新地图。

fork 冻结提交 `7cb0ac0a3d5232e90ab2db1fb7eb9ee696d1af73`，分支 `a2a`，未 push。准确冻结产物的新任务 `pagination-frozen` 经真实 Codex app-server 显式交付；独立 oracle 在 detached worktree 12/12 通过，CAS 集成读回与 worker 停止/归档均已核对。新原生 completed/idle 不交付反例仍 claimed，错 session 被拒绝。四阶段及回收后桌面截图、17项独立 CLI/Git 核对、fresh-context 只读审查 PASS 与清理记录见 [完整交付报告](../../evidence/2026-10-07-synara-batch1/T-035/RESULTS.md) 和 [独立审查](../../evidence/2026-10-07-synara-batch1/T-035/acceptance-review.md)。

原运行产物缺少最终工具注册行，未沿用其通过结论；差异与原现场保留，并对准确产物重新取得闭环证据。全仓 typecheck/lint 通过，test 与 fmt 仍存在报告中列明的失败；没有把单例复核通过写成全仓通过。完整 M1（恢复、竞争、编排、完整 CLI、多 agent 层级与切换）仍 INCOMPLETE。

**主控关闭（2026-10-07）。** 主控核对：fork `7cb0ac0` 中 `SYNARA_GATEWAY_TOOL_NAME_SET`（`apps/server/src/agentGateway/computerToolPermission.ts` 约 246 行）只决定 Synara 网关工具能否跳过 provider 自己的交互式权限确认（`autoApproveSynaraTools`），调用授权由服务端会话令牌决定；worker 以 full-access（approvalPolicy `never`）运行，不会出现该确认，因此旧产物缺少 `a2a_submit` 一行不影响调用，不构成绕过门禁的路径。门禁对 attempt 身份的校验在门禁核心中，与此集合无关。准确冻结产物已重跑并通过。全仓 `run test` 的 1 个失败（`ProviderCommandReactor.test.ts:7200`，相对基线无 diff、单例通过）与 `.grok/` 格式问题不属于本 ticket，记入地图雾区。
