---
id: T-150
title: 迁移 test_t091_pane_ipc.mjs 到现行契约（跨窗与凭据边界）
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

来源：用户 2026-10-23 在构思主控 session（Claude 62cb7357，pane wG:p1）的选择题里逐字选“C 先迁守护安全边界的 4 个 (Recommended)”，构思主控转达见 `.project-map/inbox/20261023T185657Z-ideation-answer-001.md`（授权：把 4 个文件的过时断言改到现行契约、保留有效检查；这是对修改这些受保护验收文件的授权；每个迁移须在现行代码上取得红态与绿态）。

对象：`workbench/tests/test_t091_pane_ipc.mjs`。过时：旧“默认显示当前 worker”、全局 handler/bridge 名单（缺 archive-usage 等）、旧 project/task/pane 选择模型（T-139 已改）。保留：跨窗 key、iframe、未知窗口拒收；拒绝错误凭据签发；窗口关闭与身份请求竞争中的迟到凭据撤销；空布局持久化。

T-149 的调查见 `evidence/2026-10-23-batch23/T-149/DISPOSITION.md`（本文件一行），索引 `workbench/tests/HISTORICAL.md`。

## Acceptance

- [ ] 过时断言逐条改到现行契约（依据现行规格/ticket/产品代码，写出来源），仍有效的检查全部保留，不删检查来换绿。
- [ ] 在当前 main 上绿态通过。
- [ ] 红态：至少一个已知坏实现或变异被抓住，且落在保留的有效检查上（不能只靠被改的断言）。
- [ ] 改动逐条写入 RESULTS（原断言、新断言、依据）。

## 不做

不改产品代码；不为迎合测试改产品；不碰其他测试；不改 `workbench/tests/HISTORICAL.md`（由 T-154 统一更新）。

## Resolution
