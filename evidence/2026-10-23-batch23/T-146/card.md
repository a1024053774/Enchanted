# 任务卡 T-146-1

先读 `evidence/2026-10-23-batch23/COMMON.md`（公共约定）和 `.project-map/tickets/T-146-stale-running-state.md`（ticket 全文，用户原话在里面）。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-146-1 |
| 来源 | `.project-map/tickets/T-146-stale-running-state.md`，ready_rev 1（提交 ebbae7bd0） |
| 目标 | Reflect 页、侧栏、流程页对同一会话显示同一个状态，取自同一处；终端关闭或 CLI 退出后为已结束，仍在运行的为运行中。 |
| 非目标 | 流程页的标题、泳道归属（T-144）；视图模型（T-139）；不在 Reflect 里另算一套状态。 |
| 修改边界 | 允许：`workbench/src/reflect.ts`、`workbench/src/sidebar.ts`、`workbench/src/flow.ts`（只限状态来源）、`workbench/src/stateConsistency.ts`、`workbench/src/roleRequests.ts`（只限结束状态）、`workbench/app/ReflectPage.tsx`、`workbench/tests/**` 新文件、`evidence/2026-10-23-batch23/T-146/**`。禁止：`workbench/app/renderer.tsx`、`workbench/app/main.ts`（另一个 worker 在改）、`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、验收文件。若必须改禁止的文件，上报，不要自己改。 |
| 验收文件（oracle_paths） | `workbench/tests/test_t137_reflect_e2e.py`、`workbench/tests/test_t111_flow.mjs` |
| 红态命令 | 新 e2e 加 `--revision ebbae7bd0`：关终端后 Reflect 仍显示运行中而侧栏已结束。 |
| 任务类型 | 缺陷修复 |
| 修复对象 | T-137（Reflect 页）的状态计算，提交 fbf68c404 一带 |
| 复杂度 | S |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | ebbae7bd09cee3a8220b948029f9033dc2906c90（main） |
| 唯一写入者 | Herdr agent `b23-t146`，worktree `/Users/luckye/Documents/Code/a2a-wt-t146`，分支 `exec/t146` |

## 完成条件与交付

1. 先在真实 Electron 里复现（ticket 要求）：经角色申请的执行主控终端派一个 worker，worker 结束、关掉主控终端后，读侧栏、Reflect、流程三处状态。修前 Reflect 显示运行中而侧栏已结束 = 红态，入证据。
2. 新 e2e（如 `workbench/tests/test_t146_session_state_e2e.py`）：关闭终端 / CLI 退出后三处都显示已结束；另一个仍在运行的会话三处都显示运行中。真实 Claude 用 `claude-haiku-5-5`（脚本化接口）。
3. 红态 `--revision ebbae7bd0` 失败；至少一个变异（例如 Reflect 改回“非 ended 即 running”）失败。
4. 回归：`test_t137_reflect_e2e.py`、`test_t111_flow.mjs` 绿态。
5. RESULTS.md 与 RUN-OUTSIDE 脚本按公共约定。
