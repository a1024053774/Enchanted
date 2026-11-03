---
id: T-244
title: 开发态后台每次启动都重新解包 hc，仍在运行的 core 之后起不了新窗格
type: build
status: open
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

2026-11-03 T-243 分诊中发现（[分诊记录](../../evidence/2026-11-03-batch31/T-243/RESULTS.md)）：

- `test_t123_project_identity_e2e.py` 在后台重启后新开终端失败：`shell_start` 报 `no holder: holder build 16777231:281651282:… differs from core build 16777231:281650132:…`。
- 开发态（未打包）下，`hcBinary` 每次后台启动都调用 `installHc`，用 `tar -xzf` 重新解包到 `state/hc/bin`。文件被替换成新 inode，mtime 和大小不变（探针：`evidence/2026-11-03-batch31/T-243/hc-reinstall-inode.json`）。
- core 按设计在后台重启后继续运行；它之后按路径起的 holder 来自新文件，构建号（dev:inode:mtime:size）与 core 不同，被拒绝。
- 打包版用 `hc/herdr-core` 固定文件，不受影响。

## Acceptance

- [x] 红态：修改前 `test_t123_project_identity_e2e.py` 在真实入口失败于上述错误。
- [x] 修后同一测试通过；把修复撤回（反事实）时又失败。
- [x] 版本固定值改变时仍会安装新版本，不沿用旧二进制。
- [ ] 独立审查无未处理的阻塞意见。

## Resolution

2026-11-03 进展（INCOMPLETE，未关闭）：`hcBinary` 解包后写 `state/hc/bin/release.json`（固定值加文件大小与 mtime），相同就沿用，不再重新解包；重装前先删标记。t123 修前两次失败、修后 PASS、撤回修复又失败；探针覆盖固定值改变、截断、标记损坏。复审未了结两项：两个后台同时首次启动同一数据目录仍可能都解包（已知限制，修改前每次启动都会发生）；固定值改变只有探针证据。交用户决定是否接受。证据：[T-244 RESULTS.md](../../evidence/2026-11-03-batch31/T-244/RESULTS.md)。
