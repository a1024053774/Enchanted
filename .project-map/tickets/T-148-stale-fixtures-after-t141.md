---
id: T-148
title: T-141 合入后过时的测试夹具：审查员 argv 与模拟 Codex 的启动屏
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

缺陷级（执行主控自建，T-004 范围内）。合并后回归 05（main edd8a7cad，`evidence/2026-10-23-batch23/merge-1/run-20261023T170406Z/NOTE.md`）中两项失败，根因都是测试夹具仍按 T-141 之前的启动契约写，产品行为符合用户裁定：

1. `workbench/tests/test_t146_reviewer_hooks.mjs`：手写的 Claude 审查员 argv 仍带 `--strict-mcp-config`、沙箱无 network、PreToolUse 无 MCP 权限钩子，门禁按 T-141 契约报 `review_launch_boundary`。
2. `workbench/tests/test_t145_mouse_reports_e2e.py` 的原生 receiver `workbench/tests/t145_mouse_receiver.c`：模拟 Codex 启动时打印“Open restricted”；T-141 起 a2a 不再替 worker 选择（用户裁定“不自动选”），receiver 停在启动屏，测试超时“受管 receiver 就绪并收到派发”。

把这两个夹具改到 T-141 后的契约（已信任 worker 的正常启动、审查员新 argv 形状），并清点其他仍按旧契约写的夹具（如 `legacy_quality_driver.py`、`run_t112_native.py`、`t112_reviewer_record.mjs` 中“daemon 替 worker 选 Open restricted”的说法），能跑的跑、过时的改，结果列表写进 RESULTS。

## Acceptance

- [ ] main 上 `test_t146_reviewer_hooks.mjs` 与 `test_t145_mouse_reports_e2e.py` 全绿；T-145 的红态（起点前的 T-145 修复还原）与原有变异仍被抓住。
- [ ] 断言、检查名、超时不变；只改夹具与注释。
- [ ] 其他旧契约夹具的清点结果写进 RESULTS。

## 不做

不改产品代码；不放宽任何检查。

## Resolution
