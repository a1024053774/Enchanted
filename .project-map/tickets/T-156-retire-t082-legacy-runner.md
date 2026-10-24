---
id: T-156
title: 旧 t082 runner 与 quality host bootstrap 测试：按裁定 C 删除不再有价值的，唯一守护者退回决定
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

来源：T-152 worker 上报 `20261023T190056Z-worker:b23-t152-issue-001`；构思主控答复 `20261023T204622Z-ideation-answer-001`：“t082 旧 runner 与 test_t078_quality_host_bootstrap 的导入:按用户裁定 C(删除不再有价值的)你可自建缺陷级票处理并在 report 列出。”用户裁定 C 原文见 `20261023T181318Z` 引用：“C 删除不再有价值的”。

对象：`workbench/tests/run_t082_boundary.py`（T-082 受控 tracer 与 4 个启动策略变异的旧 runner）与导入它的 `workbench/tests/test_t078_quality_host_bootstrap.py`。

1. 在当前 main 上实际运行两者，保存结果（通过、失败或无法启动都如实记录）。
2. 逐项列出它们检查的内容，对照当前守护者（T-152 迁移后的 `test_t082_review_boundary_e2e.py` 与其 runner、其他现行测试）：已被覆盖或针对已删除契约的，记为可删；当前无人守护的有效检查，记为唯一守护者。
3. 全部可删的文件：删除，并在 `workbench/tests/HISTORICAL.md` 记录删除及覆盖依据（被哪个测试的哪条检查覆盖）。含唯一守护者检查的文件：不删、不改，停下交执行主控，由构思主控决定。
4. 删除不得让任何现行测试的导入断掉（`git grep` 核对并实际导入或运行受影响的测试）。

## Acceptance

- [ ] 两个文件在当前 main 的运行结果保存在证据目录。
- [ ] 逐项覆盖对照表，每条“已覆盖”指到具体测试与检查名。
- [ ] 可删文件已删除、HISTORICAL.md 已记录；唯一守护者未动并已上报。
- [ ] 删除后受影响测试导入或运行通过，证据保存。

## 不做

不改产品代码；不迁移（迁移需用户另行裁定）；不动其他历史测试。

## Resolution

2026-10-23 执行主控阶段记录（票保持 open，NEEDS-DECISION）：当前 main `8933ee0f4` 实跑——`run_t082_boundary.py` exit 1、INCOMPLETE（正常 tracer 七条通过，第一个旧变异锚点已不存在）；`test_t078_quality_host_bootstrap.py` exit 0、PASS。覆盖对照 `evidence/2026-10-23-batch24/T-156/COVERAGE.md`：bootstrap 第 71～100 行是 `QualityCase.start_host → quality_chain_host.ts` 隔离 operator 凭据创建、state/kind/0600 与清理的唯一直接守护者，且它导入旧 runner 的 `run_case`，两个文件都未删、HISTORICAL.md 未改（合并 `0f413d74c`，仅证据）。上报 `20261023T223604Z-worker:b24-t156-issue-001`。原始现场按 T-088 归档外置盘（`*.archive.json`）。

2026-10-24 构思主控答复 `20261024T005556Z-ideation-answer-002`：用户逐字选择“迁移后删 (Recommended)”——把凭据检查挪进现行测试，再删旧 runner 与 bootstrap 测试，覆盖不丢；迁移的变异/红态证据照常。执行主控据此开第二个 attempt（卡 T-156-2），原“不迁移”限制由该授权解除。

