---
id: T-026
title: 把构建缓存与工具链放到外置盘
type: task
status: closed
blocked_by: []
claimed_by: Codex T-026 (native session 01a111fe-6eb7-7723-9a9d-0b446191b3c7)
supersedes:
---

## Question

按 T-020，把 a2a 与 Enchanted 的构建输出和缓存放到 `/Volumes/WD-Elements`：

- 定下 `CARGO_TARGET_DIR`、`CARGO_HOME`、Zig 缓存与 npm 缓存的配置方式；
- 外置盘未挂载时构建必须报错，不回退到内置盘；
- 实测机械盘上的首次编译与增量编译耗时，以及多个 worker 同时编译时的争用；
- 引擎编译需要的 Zig 工具链一并处理（本机尚未安装）。

## Resolution

**PASS（2026-10-06）。** 主控 Claude Code（`wF:pM`），worker 仅实施本 ticket。完整中文结论、命令、环境、版本与限制见 [RESULTS.md](../../evidence/2026-10-06-m1-batch1/T-026/RESULTS.md)，独立只读审查为 [PASS](../../evidence/2026-10-06-m1-batch1/T-026/acceptance-review.md)。

- `scripts/build` 先检查真实外置挂载点，缺盘与普通内置盘目录均退出 2，不生成 target；已知坏的直接 Cargo 过程退出 0 并生成内置盘 target，被同一 oracle 拒绝。最终环境污染、目录穿越、符号链接逃逸、target 覆盖和随机子程序参数检查均通过。
- 本项目 `CARGO_HOME` 完整放在外置盘，共享 registry/git；target、Zig local cache 与 tmp 按 `MUSTER_BUILD_SLOT` 分目录，Zig global cache 共享。npm 缓存为外置盘路径。保留既有 Rust 1.96.1 安装；官方 Zig 0.16.0 macOS arm64 包已安装于外置盘并读回精确版本。
- `.upstream/herdr@c4653a4f10502601ac110b12b2c45a5f7134082b` 只读归档到外置盘副本后编译：主冷态 real 162.06 s，改单文件后增量 49.69 s，并发 52.26 / 48.79 s，全部退出 0。一方明确等待同 target 的 build directory 锁；多 worker/worktree 应各用固定 slot，共享下载和 Zig 全局缓存。磁盘采样峰值、结束占用、最大 RSS 与内置盘可用空间前后值均在报告和逐次 JSON 中，不宣称吞吐改善。
- 初轮受直接 `zig build --help` 干扰，原日志与新建缓存均保留，另做空缓存的主冷态测量。初版误拒绝子程序 `--config` 的红态和修复后绿态都保留；冷态入口快照与最终入口的版本边界见报告。未修改或重启现用 Herdr server。
- 重现缺盘：`python3 -B evidence/2026-10-06-m1-batch1/T-026/check_missing_volume.py --entry "$PWD/scripts/build" --output "$PWD/evidence/2026-10-06-m1-batch1/T-026/recheck-missing-artifacts"`；输出目录必须未存在。完整编译与并发命令见报告，原始目录与完整夹具归档保留。
- README 与 AGENTS 已更新构建入口，地图登记 README 对 `scripts/build` 的覆盖。闭环检查发现已关闭的 T-024 缺索引；主控同期补入索引后移除本 worker 新增的重复行，保留主控版本。T-024 交接/审查 INCOMPLETE 的原结论不变。
- Enchanted 保持冻结，未来并入后复用同一挂载门禁与外置盘缓存方案；本次不改其仓库或用户级配置。
- Deep modules：一个 Cargo 参数入口封装挂载门禁和构建环境；Ubiquitous language 沿用现有项目、引擎、worker。没有新增协作门禁、重试、兼容或双路径。

结束项目状态、文档编码与提交清单证据保存在本次证据目录；本 ticket 的本地交付提交包含最终入口和完整证据，完整提交号由终端 `T-026 DONE` 收据给出，不 push。
