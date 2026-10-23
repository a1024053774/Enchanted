---
id: T-148
title: T-141 合入后过时的测试夹具：审查员 argv 与模拟 Codex 的启动屏
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

缺陷级（执行主控自建，T-004 范围内）。合并后回归 05（main edd8a7cad，`evidence/2026-10-23-batch23/merge-1/run-20261023T170406Z/NOTE.md`）中两项失败，根因都是测试夹具仍按 T-141 之前的启动契约写，产品行为符合用户裁定：

1. `workbench/tests/test_t146_reviewer_hooks.mjs`：手写的 Claude 审查员 argv 仍带 `--strict-mcp-config`、沙箱无 network、PreToolUse 无 MCP 权限钩子，门禁按 T-141 契约报 `review_launch_boundary`。
2. `workbench/tests/test_t145_mouse_reports_e2e.py` 的原生 receiver `workbench/tests/t145_mouse_receiver.c`：模拟 Codex 启动时打印“Open restricted”；T-141 起 a2a 不再替 worker 选择（用户裁定“不自动选”），receiver 停在启动屏，测试超时“受管 receiver 就绪并收到派发”。

把这两个夹具改到 T-141 后的契约（已信任 worker 的正常启动、审查员新 argv 形状），并清点其他仍按旧契约写的夹具（如 `legacy_quality_driver.py`、`run_t112_native.py`、`t112_reviewer_record.mjs` 中“daemon 替 worker 选 Open restricted”的说法），能跑的跑、过时的改，结果列表写进 RESULTS。

## Acceptance

- [x] main 上 `test_t146_reviewer_hooks.mjs` 与 `test_t145_mouse_reports_e2e.py` 全绿；T-145 的红态（起点前的 T-145 修复还原）与原有变异仍被抓住。
- [x] 断言、检查名、超时不变；只改夹具与注释。
- [x] 其他旧契约夹具的清点结果写进 RESULTS。

## 不做

不改产品代码；不放宽任何检查。

## Resolution

2026-10-23 关闭，PASS。

- 改动：`2d6e8e359`，合并 `b21fcf930`。`test_t146_reviewer_hooks.mjs` 的审查员 argv 改为由产品的 `Panes.createPane` 在发起 PTY 前捕获生成；`t145_mouse_receiver.c` 改为模拟已信任 Codex 发出 native 就绪包（保留 bracketed paste）；`legacy_quality_driver.py`、`run_t112_native.py`、`t112_reviewer_record.mjs` 只更新注释。断言、检查名、超时与变异列表未改。
- 根因更正：回归 05 的 NOTE 原把 T-145 归因为“不再替 worker 选 Open restricted”，实际是旧 receiver 从不发 native 就绪包；NOTE 已追加更正。
- 验收（执行主控沙箱外 `outside01-ZyHE9fBK`）：T-146 审查员钩子绿与其变异、T-145 绿、还原修复的红态与两个变异、T-127、T-141 绿与三项契约全部符合预期。
- 独立审查：agy gemini-3.8-flash-high，PASS。三条 P3：审查员 argv 取自产品有“实现自证”风险，已由 `test_t141_reviewer_contract.mjs` 与 8 个变异独立覆盖；receiver 保留 bracketed paste；历史旧契约断言只清点上报。
- 合并后回归 06（b21fcf930）：31 项全部通过。
- 清点出仍按 T-141 前契约写断言的历史测试（`test_t112_execution.mjs`、`diagnose_t112_reviewer.py`、`test_quality_tracer_e2e.py`、`test_t082_review_boundary_e2e.py`、`run_pane_lifecycle.py`、`run_worker_delivery.py`、`test_t122_claude_worker_e2e.py`、`run_t112_native.py`、`t112_reviewer_record.mjs` 的检查名、`controlled_quality_pty.ts`）见 inbox 20261023T172046Z。改这些断言要用户决定，未处理。
