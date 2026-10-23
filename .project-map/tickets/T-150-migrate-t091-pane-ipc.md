---
id: T-150
title: 迁移 test_t091_pane_ipc.mjs 到现行契约（跨窗与凭据边界）
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

对象：`workbench/tests/test_t091_pane_ipc.mjs`。过时：旧“默认显示当前 worker”、全局 handler/bridge 名单（缺 archive-usage 等）、旧 project/task/pane 选择模型（T-139 已改）。保留：跨窗 key、iframe、未知窗口拒收；拒绝错误凭据签发；窗口关闭与身份请求竞争中的迟到凭据撤销；空布局持久化。

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

- 迁移 `workbench/tests/test_t091_pane_ipc.mjs`（候选 `4aefa2b3a`，合并 `c0adb43a7`）：189 行断言逐行分类（`evidence/2026-10-23-batch23/T-150/ASSERTIONS.md`），过时的默认 worker 视图、旧 IPC/bridge 名单、旧选择模型按 T-119、T-139、T-132～T-140 改写；跨窗 key、iframe、未知窗口拒收，错误凭据签发拒绝，关窗竞争迟到凭据撤销，空布局持久化全部保留并扩到全部现行接口。唯一删除：“无 task 不能建终端”旧分支（T-119 已允许），改为正例。
- 红绿态（L1：真实 TS main/preload 在 VM 中运行）：绿态与 `--revision` 绿态 exit 0；9 个变异（no_key、single_pane、close、empty_layout、window_key、notification、history_credentials、late_identity、iframe）各 exit 1 且落在指定业务断言；T-139、T-110 回归 PASS。执行主控复跑 `local-01-Q6Rvd1` 一致。
- 独立审查 agy PASS，无发现。合并后回归 09：t091 首次因执行主控脚本漏 `--experimental-vm-modules` 失败，修正后同版本重跑 PASS（`merge-1/run-20261023T203736Z/NOTE.md`）。
