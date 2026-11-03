# T-244 结果（2026-11-03）

结论：**INCOMPLETE**。修复已落地并有红态、绿态与反事实；复审仍有两项未了结（并发首次启动、没有改真实固定值的端到端运行），按规则不再开新一轮审查，交用户决定是否接受为已知限制。

## 原因

开发态（未打包）下，`hcBinary` 每次后台启动都调用 `installHc`，用 `tar -xzf` 把 hc 重新解包到 `state/hc/bin`。文件换成新 inode，mtime 与大小不变（`hc-reinstall-inode.json`：281673966 → 281673971）。core 在后台重启后继续运行，它之后按路径起的 holder 来自新文件，构建号（dev:inode:mtime:size）与 core 不同，于是新开终端失败：`no holder: holder build … differs from core build …`。打包版用固定的已签名文件，不受影响。

## 改动

`workbench/src/hcDistribution.mjs` 的 `hcBinary`：解包后在 `state/hc/bin/release.json` 写入固定值（版本、URL、SHA-256）；下次启动时，若 `herdr-core` 存在且 `release.json` 与当前固定值相同，直接用已有文件，不再解包。重新解包前先删除 `release.json`，解包成功后才写回，所以中途中断的解包下次会重做。标记里还记下解包后文件的大小和 mtime，复用前核对，文件被截断或替换就重新安装（只读文件元数据，不计算校验值）。`installHc` 不变，打包脚本 `app/package.mjs` 的输出也不变。

## 证据

| 文件 | 内容 |
| --- | --- |
| `../T-243/runs/test_t123_project_identity_e2e/triage.json`、`../T-243/runs-green/test_t123_project_identity_e2e/summary.json` | 修前（父版本的产品代码）两次失败于同一 `no holder` 错误 |
| `green-t123.json`、`green-t123.log` | 修后同一测试 PASS，core 已停 |
| `reverted-t123.json`、`reverted-t123.log` | 反事实：修后把 `hcDistribution.mjs` 临时换回 HEAD 版本，同一测试又失败于 `no holder`；之后恢复修复 |
| `../T-243/runs-green-3/test_t123_project_identity_e2e/` | 最终代码再跑一次：PASS，无残留 |
| `pin-probe-2.json` | 最终代码：同一固定值保留原文件；固定值改变、文件被截断、标记损坏三种情况都重新安装 |
| `pin-probe.json` | 同一固定值再次调用：inode 不变；把 `release.json` 改成别的版本：重新安装，inode 改变 |

## 命令

```bash
ENCHANTED_HC_CACHE_DIR=/Users/luckye/Documents/Code/hc-cache python3 workbench/tests/test_t123_project_identity_e2e.py --summary <新文件>.json
```

## 审查

`../review-2/REPORT.md`：

- 第 4 条“中断的重装会留下与固定值相符的旧标记”：成立，已改为重装前先删标记。“二进制之后被截断或替换”与“两个后台同时首次启动同一数据目录”：修改前的代码同样没有防护（修改前每次都重新解包，并发时同样会互相覆盖），不在本票范围，未改。
- 第 5 条“缺少修后反事实”：成立，已补 `reverted-t123.json`。`pin-probe.json` 只改了标记文件，没有端到端地改变固定值。

复审 `../review-2/REREVIEW.md`：第 4 条“文件之后被截断或替换仍沿用”驳回不成立——修改前每次都重新解包，会自愈。已加大小与 mtime 核对（`pin-probe-2.json`）。不变式：core 使用数据目录期间，它启动所用的二进制文件身份不变；文件被改过就重装。“两个后台同时首次启动同一数据目录”仍可能都解包：`hcBinary` 在后台的 endpoint 与 pid 文件排他之前运行。修改前同样存在且每次启动都会发生，现在只剩首次；作为已知限制写在代码注释里，未改。第 5 条：固定值改变仍只有探针（改标记文件），没有改真实固定值的端到端运行。
