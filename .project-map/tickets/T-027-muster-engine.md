---
id: T-027
title: Muster 引擎以独立命名空间运行
type: build
status: open
blocked_by: [T-026]
claimed_by:
supersedes:
---

## What to build

把 Herdr 0.9.3（`c4653a4`）的引擎硬分叉进本仓库，改成 Muster 的命名空间。完成后，用户可以在独立会话中启动 `muster` 后台服务：建项目和任务、分 pane、在 pane 里跑 shell 和 Codex，看到 agent 状态，并通过 `muster` 读写 pane。整个过程中，已安装的 Herdr 照常工作、互不干扰。

引擎不再访问 herdr.dev，保留 Herdr 的许可与来源说明。命名空间、网络和来源要求见 [spec](../specs/workbench-m1-2026-10-06.md) 的"命名空间""网络""代码位置"。

## Acceptance

- [ ] 能从源码构建出 `muster`；构建输出和缓存都在外置盘上，外置盘未挂载时构建报错。
- [ ] `muster` 能在独立命名会话中启动后台服务，并建出项目、任务和 pane；pane 中的 shell 可读可写；客户端断开后，服务和 pane 仍在。
- [ ] 在 muster pane 中启动 Codex，状态识别正确（working、idle），会话 ID 经 Muster 自己的集成 hook 上报。
- [ ] 已安装的 Herdr 与 Muster 同时运行，双方的 socket、配置和 hook 互不影响，并留有记录。
- [ ] 源码和运行时都不再访问 herdr.dev，网络访问检查留有记录。
- [ ] 保留 Herdr 的 LICENSE，并附来源说明（上游地址与 `c4653a4`）；引擎自带测试中与本切片相关的部分通过，失败项逐条记录。

## Resolution

未执行。
