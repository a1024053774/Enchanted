---
id: T-027
title: Muster 引擎以独立命名空间运行
type: build
status: open
blocked_by: [T-026]
claimed_by: Codex worker wF:pS
supersedes:
---

## What to build

把 Herdr 0.9.3（`c4653a4`）的引擎硬分叉进本仓库，改成 Muster 的命名空间。完成后，用户可以在独立会话中启动 `muster` 后台服务：建项目和任务、分 pane、在 pane 里跑 shell 和 Codex，看到 agent 状态，并通过 `muster` 读写 pane。整个过程中，已安装的 Herdr 照常工作、互不干扰。

引擎不再访问 herdr.dev，保留 Herdr 的许可与来源说明。命名空间、网络和来源要求见 [spec](../specs/workbench-m1-2026-10-06.md) 的"命名空间""网络""代码位置"。

## Acceptance

- [x] 能从源码构建出 `muster`；构建输出和缓存都在外置盘上，外置盘未挂载时构建报错。
- [ ] `muster` 能在独立命名会话中启动后台服务，并建出项目、任务和 pane；pane 中的 shell 可读可写；客户端断开后，服务和 pane 仍在。
- [ ] 在 muster pane 中启动 Codex，状态识别正确（working、idle），会话 ID 经 Muster 自己的集成 hook 上报。
- [ ] 已安装的 Herdr 与 Muster 同时运行，双方的 socket、配置和 hook 互不影响，并留有记录。
- [ ] 源码和运行时都不再访问 herdr.dev，网络访问检查留有记录。
- [x] 保留 Herdr 的 LICENSE，并附来源说明（上游地址与 `c4653a4`）；引擎自带测试中与本切片相关的部分通过，失败项逐条记录。

## Resolution

执行中：INCOMPLETE。worker 为 Codex `wF:pS`，主控为 Claude Code `wF:pM`。固定源码已导入 `muster/engine/`，独立命名空间与禁用在线 transport 已实现；构建、缺盘反例和相关自带测试通过。完整 3470 项列表中 3459 通过、11 为原有 ignored 项，50 个进程均退出 0。

run-03 的真实 shell、endpoint、Codex working/settled、Muster hook 会话 ID 和 Herdr 共存检查通过；随后修复了冻结 wire 的机械改名，因此该 PASS 不替新候选背书。最终候选等待真实复验及独立只读审查；此前限定“下一次”的四 hook 批准已用于 run-03，私有 home 已删除。证据、失败和反事实见 [T-027 报告](../../evidence/2026-10-06-m1-batch2/T-027/RESULTS.md)。

未修改根治理文件。根 README 因新增实现 stale，按任务书交主控收尾；不把这项未知写成 PASS。
