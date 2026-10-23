---
id: T-149
title: 过时历史测试：删除不再有价值的，其余标为只针对历史版本
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

来源：用户 2026-10-23 在构思主控 session（Claude 62cb7357，pane wG:p1）的选择题里逐字选“C 删除不再有价值的”，构思主控转达见 `.project-map/inbox/20261023T181318Z-ideation-answer-001.md`（授权范围：确认不再有价值的删除；其余按 B 标为只针对对应历史 revision、不在当前 main 上跑；仍是现行契约唯一守护者的不删，写 needs-decision）。

对象（13 个）：`test_t112_execution.mjs`、`diagnose_t112_reviewer.py`、`test_quality_tracer_e2e.py`、`test_t082_review_boundary_e2e.py`、`run_pane_lifecycle.py`、`run_worker_delivery.py`、`test_t122_claude_worker_e2e.py`、`run_t112_native.py`、`t112_reviewer_record.mjs`、`controlled_quality_pty.ts`、`test_t091_pane_ipc.mjs`、`test_t078_claude_signals.ts`、`test_t108_questions.mjs`（都在 `workbench/tests/`）。

判据：该测试守护的契约已被现行且在 main 上通过的测试覆盖，或契约已废弃——删；契约仍有效但测试只按旧版本写——标历史（写明对应 revision，当前 main 上不跑）；仍是现行契约唯一守护者——不删，交用户（needs-decision）。

## Acceptance

- [x] 13 个文件逐个有处置（删 / 标历史 / 待决）与理由，理由引用覆盖它的现行测试或说明契约已废弃。
- [x] 删除后没有悬空引用（其他测试、脚本、README、回归脚本 import 或调用被删文件的都处理掉或列出）。
- [x] 标历史的文件有统一、可查的标记，当前 main 上不会被回归入口误跑。
- [x] 合并回归在 main 上全绿。

## 不做

不改产品代码；不改现行测试的断言；不为迎合旧断言改产品。

## Resolution

2026-10-23 关闭，PASS（按用户裁定 C 的判据执行完毕；其中 10 个文件交用户决定，见下）。

- 处置（worker b23-t149 调查，执行主控确认 PLAN `8eda61b96`）：删 0、标历史 3、待决 10。逐文件理由与现行覆盖见 `evidence/2026-10-23-batch23/T-149/DISPOSITION.md`，索引 `workbench/tests/HISTORICAL.md`。
- 标历史（文件头一行注释，不改代码）：`diagnose_t112_reviewer.py`、`t112_reviewer_record.mjs`（5f19062f5，T-112）、`controlled_quality_pty.ts`（5f7f9816e，T-082）。三者仍被其他测试或 host 导入，直接删会让依赖方找不到模块。
- 待决（未动，needs-decision 交用户）：`test_t112_execution.mjs`、`test_quality_tracer_e2e.py`、`test_t082_review_boundary_e2e.py`、`run_pane_lifecycle.py`、`run_worker_delivery.py`、`test_t122_claude_worker_e2e.py`、`run_t112_native.py`、`test_t091_pane_ipc.mjs`、`test_t078_claude_signals.ts`、`test_t108_questions.mjs`：各含现行测试未覆盖的有效检查。
- 候选 `1b017f8ef`，合并 `0bd1a8ba4`。独立审查 agy gemini-3.8-flash-high PASS（抽查 5 个待决与 3 个标历史均同意；两条 P3 为证据路径标注）。合并后回归 08：32 项全部通过。

