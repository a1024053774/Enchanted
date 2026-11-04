---
id: T-243
title: 自己启动后台、不走 Fixture 的测试跑完不收私有 hc core
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

从 T-232 拆出（用户 2026-11-03：“做到新票里,然后继续修复”）。T-232 让 `scripted_claude.Fixture.stop` 停夹具的私有 core 并核对没有残留进程（`scripted_claude.stop_private_core`、`fixture_processes`）。`workbench/tests/` 里还有 46 个测试自己启动后台，不走 `Fixture`，也不停私有 core；后台现在启动终端时都会起私有 core，所以它们跑完可能留下 `herdr-core serve`、`hold` 及其中的 CLI。清单见 [T-232 的 Resolution](T-232-t216-tests-leave-fixture-cores.md)。其中大部分早于 hc 运行时（T-209）。

要做的：先查清哪些测试仍能运行；仍能运行的在结束时（通过或失败都一样）停私有 core 并核对没有残留；已经不能运行的，查清原因后列出，不在本票里修好它们。

## Acceptance

- [x] 列出每个测试：仍能运行 / 已失效（附依据）。
- [x] 修前留红态：仍能运行的测试中至少一个跑完后列出夹具路径下的残留进程。
- [x] 修后仍能运行的测试跑完（含一次故意失败），夹具路径下没有残留进程；用户自己的 core 不变。
- [x] 独立审查无未处理的阻塞意见。（复审无阻塞；t078_input_entry 的清理段只有代码判断）

## Resolution

2026-11-03 关闭（PASS）：复审确认第 1、2 条的清理结构已修正，无阻塞；非阻塞：`test_t078_input_entry.py` 在夹具准备阶段就失败，新清理段没有运行证据，只做了编译检查（RESULTS 已写明）。

2026-11-03 第二次进展（INCOMPLETE，第三轮审查 NO_GO 的第 1、2 条已修，待复审）：26 个批次脚本已分诊——已失效（T-123 以前的裸任务名、要求外置盘、读已删除的旧证据；其中 2 个只是推断）、要用户授权的真实模型回合（未运行），或是工具；能直接起来的 4 个运行后都在门禁检查前失败。不修它们。Electron 退出未确认的路径按用户同意（“按这个顺序修,后两项我同意.”）改为先记现场（进程组、`sample` 栈）再结束，然后照常停后台与 core：修前故意失败留 6 个进程，修后 0 个；正常路径回归 PASS；现场采集或 `sample` 失败时也照常停后台与 core（第三轮审查后补）。T-244、T-245 已另修。

2026-11-03 第一次进展：分诊 47 个测试，14 个修前留下 core；`scripted_claude.stop_fixture_core` 放进各测试清理的 finally；修了 T-232 引入的 t104、t212 旧参数回退；复审后写不变式并用 `invariant_search.py` 系统搜索后修完。

证据：[T-243 RESULTS.md](../../evidence/2026-11-03-batch31/T-243/RESULTS.md)。
