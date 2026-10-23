---
id: T-153
title: 迁移 run_worker_delivery.py 到现行契约（交付回执只处理一次）
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

对象：`workbench/tests/run_worker_delivery.py`。过时：原生 turn_context 要求网络关闭、固定旧 CLI 版本（T-118 不限版本）、verify 后不经独立审查/评分直接 integrate 的早期流程。保留：真实 Stop 批次只处理一遍、重复交付回放、门禁回执只注入一次且仅产生无工具收据回合、实际 turn_context→delivery→尾注。

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

- 迁移 `workbench/tests/run_worker_delivery.py`（候选 `6fbef7525`，合并 `a714a59aa`）：网络期望按 T-141、CLI 版本按 T-118 记实际 `--version`、流程改为 verify→新审查→review_reclaimed→带 score 集成、删除已删 `pane_release`、任务身份按 T-123；Stop 批次只处理一次、重复交付回放、回执只注入一次且收据回合无工具、turn_context→delivery→尾注全部保留。
- 真实 Codex（gpt-6.1-sol high，/tmp 隔离 CODEX_HOME，授权 01～04 逐轮记录）共 4 轮、累计 15 个真实回合：01 启动前 unknown_task（0 回合）；02、03 红态有效，绿态被真实 reviewer 以夹具 oracle 不足判需修复；worker 做 151 个变异系统扫查（`MUTATION-SWEEP-04.json`）补强夹具 oracle；04 红态 `repeat-feedback` NO_GO 于 STOP-BATCH-ONE-NOTICE，绿态 PASS，relay-cli/relay-core/hook-turn-facts PASS。
- 独立审查 agy PASS，一条 P3（RESULTS 开头状态停在 04 之前，已补记）。范围外上报：`native-cli-orchestration-2026-10-10.md` §5 仍写旧 socket 与关网络（inbox `20261023T193353Z-worker:b23-t153-issue-001`）。
