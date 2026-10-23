---
id: T-154
title: 6 个过时测试整份标历史，HISTORICAL.md 更新为最终处置
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

来源：同 T-150（用户逐字选“C 先迁守护安全边界的 4 个 (Recommended)”，转达 `.project-map/inbox/20261023T185657Z-ideation-answer-001.md`）：其余 6 个（`test_t112_execution.mjs`、`test_quality_tracer_e2e.py`、`run_pane_lifecycle.py`、`test_t122_claude_worker_e2e.py`、`run_t112_native.py`、`test_t108_questions.mjs`）整份标历史，写明“当前无人守护这些检查”，不删、不迁。

`workbench/tests/HISTORICAL.md` 由本票唯一写入：把 6 个移入历史节（对应 revision 与无人守护的检查清单），4 个迁移文件改为“已迁移到现行契约（T-150～T-153）”。

## Acceptance

- [ ] 6 个文件头一行“历史测试：只针对 <revision>，当前 main 不跑；当前无人守护：<检查摘要>”，不改代码。revision 有证据（该测试最后一次通过的版本）。
- [ ] HISTORICAL.md 列出 6 个的未守护检查；4 个标已迁移并指向票号。
- [ ] 文件头注释不破坏 shebang/模块解析；依赖它们的离线测试仍能导入。

## 不做

不删、不迁、不改断言；不碰 T-150～T-153 的文件。

## Resolution
