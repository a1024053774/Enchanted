---
id: T-152
title: 迁移 test_t082_review_boundary_e2e.py 到现行契约（审查副本边界）
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

来源：用户 2026-10-23 在构思主控 session（Claude 62cb7357，pane wG:p1）的选择题里逐字选“C 先迁守护安全边界的 4 个 (Recommended)”，构思主控转达见 `.project-map/inbox/20261023T185657Z-ideation-answer-001.md`（授权：把 4 个文件的过时断言改到现行契约、保留有效检查；这是对修改这些受保护验收文件的授权；每个迁移须在现行代码上取得红态与绿态）。

对象：`workbench/tests/test_t082_review_boundary_e2e.py`（及只被它用的 `run_t082_boundary.py` 等，如有）。过时：审查员关网络参数（T-141 已放开）。保留：审查副本建立/清理、共享 refs 变化作废、review_requirements.workspace 绑定、结束核对完成前拒绝集成（含 held socket 正负对照）、脏结束作废。

T-149 的调查见 `evidence/2026-10-23-batch23/T-149/DISPOSITION.md`（本文件一行），索引 `workbench/tests/HISTORICAL.md`。

## Acceptance

- [x] 过时断言逐条改到现行契约（依据现行规格/ticket/产品代码，写出来源），仍有效的检查全部保留，不删检查来换绿。
- [x] 在当前 main 上绿态通过。
- [x] 红态：至少一个已知坏实现或变异被抓住，且落在保留的有效检查上（不能只靠被改的断言）。
- [x] 改动逐条写入 RESULTS（原断言、新断言、依据）。

## 不做

不改产品代码；不为迎合测试改产品；不碰其他测试；不改 `workbench/tests/HISTORICAL.md`（由 T-154 统一更新）。

## Resolution

2026-10-23 关闭，PASS。

- 迁移 `workbench/tests/test_t082_review_boundary_e2e.py`（候选 `ba8745b93`，合并 `866cc08bc`）：审查员 argv 网络断言按 T-141 改写；审查副本生命周期、共享 refs 作废、`review_requirements.workspace` 绑定、结束核对前拒绝集成（held socket 正负对照）、脏结束作废全部保留。
- 共享基类按旧流程写，未改共享文件与产品：本文件内覆盖放行（native ready，已删 `pane_release` 不再调用）、`stop_turn`/`send_review`/held-socket 的现行 Stop 信封（cwd、transcript_path 取自本夹具 workspace 与该 launch 日志）；专用 `t152_review_host.ts`（提交后给 PTY 输出、native ready）、`t152_real_review_submit.json`、本票 runner。流程走查 `FLOW-AUDIT.md`。累计改动明显大于最初两条网络断言。
- 沙箱外 5 轮（01～03 夹具层层不符；04 单正例通过、读回脚本缺陷；05 全套）：05 共 13 项 PASS——4 个保留检查变异分别命中 T082-COPY-REMOVED、REVIEW-END-BEFORE-INTEGRATE、REVIEW-REQUIREMENTS-WORKSPACE、REVIEW-REFS-INVALIDATE；4 个非法启动被拒；绿态 7 场、T-090 3 例、T-141 PASS。0 模型回合（受控 PTY）。
- 独立审查 agy PASS，无发现。范围外上报：`run_t082_boundary.py` 与共享 `controlled_quality_pty.ts` 仍为历史契约（inbox `20261023T190056Z-worker:b23-t152-issue-001`）。
