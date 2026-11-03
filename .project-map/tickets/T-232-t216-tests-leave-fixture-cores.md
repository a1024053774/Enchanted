---
id: T-232
title: 测试夹具跑完不收私有 hc core（scripted_claude.Fixture.stop 只停后台）
type: build
status: closed
blocked_by: []
claimed_by:
supersedes:
ready: yes
ready_by: executor
ready_rev: 1
---

## What to build

T-230 回归时的范围外发现（[结果记录](../../evidence/2026-10-31-batch29/T-230/RESULTS.md)）：`workbench/tests/test_t216_issue_push_e2e.py --gui` 和 `workbench/tests/test_t216_round2_e2e.py --case routing-online` 都报 PASS，但跑完后各自夹具里的私有 `herdr-core serve`、`hold` 仍在，前者还留下一个 Claude Code 进程和它的 MCP 子进程。这些进程的父进程都是 1。主控在归档前手工结束了它们。

T-229 回归时看清了根因：几乎每个基于 `workbench/tests/scripted_claude.py` 的 `Fixture` 的测试跑完都留下夹具的私有 `herdr-core serve`、`hold`。原因是 `Fixture.stop` 只停后台（`daemon_stop`），私有 core 按设计比后台活得久，没人停它。T-229 那一轮跑完时残留二十多对，另有更早留下的 t078、t126 夹具 core；主控都已手工结束。

要做的：`Fixture.stop`（不走 `Fixture` 的同类测试于 2026-11-03 按用户决定移到 T-243）在结束时，通过或失败都一样，停掉夹具的私有 core 和其中的 CLI，并核对没有残留；做法沿用 `test_t212_shell_hc_e2e.stop_private_core`。

## Acceptance

- [x] 修前留红态：跑完后列出夹具路径下的残留进程。
- [x] 修后用 `Fixture` 的测试跑完（含一次故意失败），夹具路径下没有残留进程；用户自己的 core 不变。
- [x] 独立审查（GPT 只读，新开干净会话）无未处理的阻塞意见。

## Resolution

2026-11-03 关闭，**PASS**（按缩小后的范围）（[结果](../../evidence/2026-11-03-batch31/T-232/RESULTS.md)）。

- 完成：`Fixture.stop` 无论通过或失败都停夹具私有 core，并核对夹具进程（argv 或环境含夹具路径）为空；`stop_private_core` 移到 `scripted_claude.py` 只留一份；`Fixture.env` 传入 `ENCHANTED_HC_CACHE_DIR`（复制的源码每次下载 hc 会超过 10 秒启动期限）。故意失败与正常 GUI 运行后都没有残留，用户 core 不变。审查对这部分无阻塞。
- 范围：复审指出原票面包括不走 `Fixture` 的测试。用户 2026-11-03 在主控会话中决定：“做到新票里,然后继续修复”，这部分移到 T-243。当时的清单（自己 `daemon_start`、无 `Fixture(`、无停 core 调用）共 46 个：`daemon_acceptance_adapter.py`、`run_*.py`（14 个）、`t078_*.py`（3 个）、`test_daemon_recovery_e2e.py`、`test_electron_e2e.py`、`test_orchestrator_e2e.py`、`test_offline_trace_e2e.py`、`test_t078_*`（3）、`test_t081_*`（2）、`test_t096_*`（6）、`test_t118`、`test_t121`～`test_t127`（6）、`test_t131`、`test_t156`、`test_t193`、`test_t195`、`test_t198`、`test_t230`、`test_t237`、`test_t239`。其中大部分早于 hc 运行时，先要查清哪些仍在用。
