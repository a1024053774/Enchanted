---
id: T-034
title: Synara fork 能构建运行
type: task
status: closed
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

**PASS（2026-10-07）。** 主控补入地图索引后关闭；主控抽查：缺盘时入口真实退出码 2，演练合并 `00a856f8` 不在 `a2a` 分支，无残留进程。原收尾说明：实现与行为验收为 PASS，独立只读审查对冻结候选与证据给出 PASS。关闭 ticket 时 `project_map.py status` 报 closed decision 缺少 MAP 索引；任务书禁止 worker 改 MAP，因此暂留 open，主控补索引后关闭。确切错误、命令与最小收尾步骤见 [controller-handoff.md](../../evidence/2026-10-07-synara-batch1/T-034/controller-handoff.md)。

[完整命令、测量、反例、失败和证据](../../evidence/2026-10-07-synara-batch1/T-034/RESULTS.md)。

Fork 生产提交 `0b1740fd4e385baf389095e5cfa16dd67adcd3b4`；临时合并分支 `a2a-merge-drill`，提交 `00a856f8beb96c1db065048a98cd81b6a9be9a9a`，无冲突，7 个 workspace 类型检查和 28 个 skills catalog 测试通过。两仓库未 push。

- 经 `a2a/scripts/bun` 完成 `setup-node`、`install --frozen-lockfile`、`run build`、`run dev:server`、`run dev:web`、`run start:desktop`；命令、输出及退出码见报告与各 JSON/log。
- 首次安装 2434.25 秒；首次后端 HTTP 200 为 2.51 秒，网页 HTTP 200 为 19.21 秒；干净桌面暖启动到原生 AX 确认的观测上界 6.37 秒，截图已保存。冷启动精确时延未核对，超时及无效重启保留，不计作通过时延。
- checkout 新增约 3.36 GiB，其中 node_modules 约 2.76 GiB、其他约 0.60 GiB；外置盘缓存/工具链/运行数据约 2.90 GiB。原始前后 df/du 保留，全机差额不归因给本任务。
- 缺盘/非外置卷 15 项在 Bun 启动前拒绝，目录未变化；忽略指定卷的坏版本被同一哨兵条件抓住。Node 24.13.1 官方包已核对官方 SHASUMS256，全局 Node 仍为 v26.5.0。
- 独立审查：[acceptance-review.md](../../evidence/2026-10-07-synara-batch1/T-034/acceptance-review.md)，冻结 a2a 证据提交 `2d01c8ceb5eab77e10d2bfe2478b9fd62f127838`。进程已关闭，生产分支未包含演练合并；未跟踪 `.grok/settings.json` 保留而不提交。未运行全仓测试或 provider turn，结论不延伸到后续门禁或发布。
