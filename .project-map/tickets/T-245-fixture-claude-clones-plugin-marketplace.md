---
id: T-245
title: 夹具里的真实 Claude Code 在后台克隆官方插件市场，测试结束后留下 git/ssh 进程
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

2026-11-03 T-243 绿态中发现（[T-243 结果](../../evidence/2026-11-03-batch31/T-243/RESULTS.md)）：

- `test_t124_controller_e2e.py` 连续两次在清理时报出残留：`git … clone --depth 1 -- git@github.com:anthropics/claude-plugins-official.git <夹具>/home/.claude/plugins/marketplaces/…`，以及它下面的 `sh`、`ssh -o BatchMode=yes … git@github.com git-upload-pack`，父进程为 1。同一测试在修前的分诊里没有出现，与网络时序有关。
- 克隆由夹具 HOME 里的真实 Claude Code 发起。ssh 读的是账户主目录的 `~/.ssh`，不是夹具的 `HOME`，所以可能用的是用户真实的 ssh 身份。
- hc core 已停，不属于 T-243 的 core 残留。

要做的：查清 Claude Code 在什么条件下自动安装官方插件市场、有没有经启动参数或夹具环境关闭它的办法（不写用户的 `~/.claude`）；按结果修夹具，或说明为什么不能关并改清理方式。涉及用户 ssh 身份是否被测试使用，处理前交用户决定。

## Acceptance

- [x] 写明触发条件与依据。
- [x] 修后 `test_t124_controller_e2e.py` 结束时夹具路径下没有进程。
- [x] 独立审查无未处理的阻塞意见。（第三轮审查无阻塞）

## Resolution

2026-11-03 关闭（PASS）：第三轮审查无阻塞；非阻塞的边界已写明：证据只证明本机 Claude Code 2.1.317 与该夹具场景，不证明以后的版本仍认这些字段。

2026-11-03 进展（INCOMPLETE，待独立审查）：触发条件来自本机 Claude Code 2.1.317 的官方插件市场自动安装：HOME 下 `.claude.json` 没有已尝试/已拒绝的记录就下载，下载失败再用用户真实的 ssh 身份克隆。受管 worker 只读得到 HOME 的 `.claude.json`，所以夹具在那里写入 Claude 自己会写的 `policy_blocked` 三项（`MARKETPLACE_SKIPPED`），29 个测试与探针并入；`stop_fixture_core` 收尾时发现 `.claude/plugins/marketplaces` 就失败。t124：修前装上、修后 PASS 无残留、反事实又装上。

证据：[T-245 RESULTS.md](../../evidence/2026-11-03-batch31/T-245/RESULTS.md)。
