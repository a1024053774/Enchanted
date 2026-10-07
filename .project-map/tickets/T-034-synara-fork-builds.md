---
id: T-034
title: Synara fork 能构建运行
type: task
status: open
blocked_by: []
claimed_by: Codex s1-t034 (wF:pV)
supersedes:
---

## Question

在本机从 `~/Documents/Code/synara`（fork 的 `a2a` 分支，起点 v1.0.1-beta.2）安装依赖、构建并运行 Synara 的 dev server 与桌面版；Bun 全局缓存与 Electron 下载缓存放到外置盘，缺盘即报错；实测内置盘占用与耗时；做一次上游合并演练。设计见 [spec](../specs/synara-m1-2026-10-07.md) 的"fork 与上游""构建与缓存""隔离运行"。

完成条件：
- 安装、构建、dev server、桌面版各有一次成功运行的命令与输出，Synara 使用隔离的数据目录；
- 缓存位置经检查确实在外置盘；模拟缺盘时入口报错且不在内置盘生成缓存；
- 记录 `node_modules` 与其他内置盘新增占用、安装耗时、dev server 与桌面版启动耗时；
- 在临时分支上把 `upstream/main` 合并进 `a2a`，记录冲突与测试结果，不推送该临时分支。

## Resolution

INCOMPLETE（执行项已完成，待独立验收审查）。

[完整命令、测量、反例、失败和证据](../../evidence/2026-10-07-synara-batch1/T-034/RESULTS.md)。

Fork 生产提交 `0b1740fd4e385baf389095e5cfa16dd67adcd3b4`；临时合并分支 `a2a-merge-drill`，提交 `00a856f8beb96c1db065048a98cd81b6a9be9a9a`，无冲突，7 个 workspace 类型检查和 28 个 skills catalog 测试通过。两仓库未 push。
