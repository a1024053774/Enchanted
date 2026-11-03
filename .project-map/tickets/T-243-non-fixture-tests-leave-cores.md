---
id: T-243
title: 自己启动后台、不走 Fixture 的测试跑完不收私有 hc core
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

从 T-232 拆出（用户 2026-11-03：“做到新票里,然后继续修复”）。T-232 让 `scripted_claude.Fixture.stop` 停夹具的私有 core 并核对没有残留进程（`scripted_claude.stop_private_core`、`fixture_processes`）。`workbench/tests/` 里还有 46 个测试自己启动后台，不走 `Fixture`，也不停私有 core；后台现在启动终端时都会起私有 core，所以它们跑完可能留下 `herdr-core serve`、`hold` 及其中的 CLI。清单见 [T-232 的 Resolution](T-232-t216-tests-leave-fixture-cores.md)。其中大部分早于 hc 运行时（T-209）。

要做的：先查清哪些测试仍能运行；仍能运行的在结束时（通过或失败都一样）停私有 core 并核对没有残留；已经不能运行的，查清原因后列出，不在本票里修好它们。

## Acceptance

- [ ] 列出每个测试：仍能运行 / 已失效（附依据）。
- [x] 修前留红态：仍能运行的测试中至少一个跑完后列出夹具路径下的残留进程。
- [ ] 修后仍能运行的测试跑完（含一次故意失败），夹具路径下没有残留进程；用户自己的 core 不变。
- [ ] 独立审查无未处理的阻塞意见。

## Resolution

2026-11-03 进展（INCOMPLETE，未关闭）：分诊了 47 个测试，14 个修前留下 core；修后已运行的都不留 core，故意失败也不留，用户的 core 不变。改法：`scripted_claude.stop_fixture_core`，在各测试清理的 finally 里先停 core；修了 T-232 引入的 t104、t212 旧参数调用回退。复审在同一条不变式上又有反例，按规则改为写不变式并用 `invariant_search.py` 系统搜索后修完。未完成：26 个一次性批次脚本未运行、未判定；electron 测试“窗口未确认”路径按原设计保留后台与 core 给主控看现场，复审不同意，交用户决定；t124 另有插件市场克隆残留（T-245）。另发现 T-244。证据：[T-243 RESULTS.md](../../evidence/2026-11-03-batch31/T-243/RESULTS.md)。
