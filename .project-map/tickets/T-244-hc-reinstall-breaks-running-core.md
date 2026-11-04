---
id: T-244
title: 开发态后台每次启动都重新解包 hc，仍在运行的 core 之后起不了新窗格
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: no
ready_by:
ready_rev:
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
- [x] 独立审查无未处理的阻塞意见。（复审无阻塞；并发首次安装只有代码判断）

## Resolution

2026-11-03 关闭（PASS）：复审无阻塞；并发首次安装仍只有代码判断，丢失的 EEXIST 摘要无法恢复，均已在 RESULTS 写明。

2026-11-03 第二次进展（INCOMPLETE，待复审）：第一版（`state/hc/bin/release.json` 标记，相同就沿用）挡不住“固定值变了、旧 core 还在跑”，改为第二版：每个固定值装进自己的目录 `state/hc/herdr-core-<版本>-<sha8>/`，临时目录解包后一次 rename 到位，已装好的文件从不改写；并发首次安装时后到的用先到的那份。新测试 `test_t244_pin_change_e2e.py` 端到端改变固定值：修前（`20f1d8581`）失败于 `no holder`，修后 PASS（core 仍用第一份、inode 不变，新固定值装在自己的目录）；t123、t212 回归 PASS。第一版复审的“没有端到端改固定值”由此补上；并发首次安装只有代码判断，没有运行证据。第三轮审查的非阻塞“目录在但缺文件时返回不存在的路径”已复现并修（改为报错）。

2026-11-03 第一次进展：查明原因——开发态每次后台启动都重新解包到同一路径，换了 inode，运行中的 core 之后起的 holder 构建号对不上。

证据：[T-244 RESULTS.md](../../evidence/2026-11-03-batch31/T-244/RESULTS.md)。
