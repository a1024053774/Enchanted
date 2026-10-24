# 任务卡 T-165-1（排队输入那一轮的 Stop 早于转录登记）

先读 `evidence/2026-10-23-batch24/COMMON-FIX.md`、`.project-map/tickets/T-165-queued-input-stop-race.md`、`.project-map/tickets/T-157-stop-hook-user-input-submit.md` 的 Resolution、`evidence/2026-10-23-batch24/T-157/RESULTS.md`。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-165-1 |
| 来源 | T-165 ready_rev 1（ready_by executor，T-157 已批准范围内的缺陷级残余） |
| 目标 | 按 ticket：Stop 与原生转录登记的先后不决定结果；Stop 先到时也能匹配该轮并回到空闲；门禁核对不放松，不误配无关 Stop，不加重试/超时兜底。 |
| 修改边界 | 允许：`workbench/src/panes.ts`；`workbench/tests/test_t157_stop_input_e2e.py` 与 `workbench/tests/scripted_claude.py` 中为确定时序所需的夹具改动（不放宽断言）；新增只属于本票的测试 `workbench/tests/test_t165_*`；`evidence/2026-10-23-batch24/T-165/**`。其他产品文件需要改时先上报。禁止：`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、`workbench/app/renderer.tsx`（T-161 在改）。 |
| 任务类型 | 缺陷修复 |
| 复杂度 | M |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 本卡提交所在的 main |
| 唯一写入者 | Herdr agent `b24-t165`，worktree `/Users/luckye/Documents/Code/a2a-wt-t165`，分支 `exec/t165` |

现场证据：`/private/tmp/t157-stop-input-63d2qaht`（state/state.sqlite3 orchestration_events seq 109～125）。真实供应商模型回合 0（用脚本化 Messages）。沙箱外运行写 `RUN-OUTSIDE-0N.sh` 交执行主控；只有 git add/commit 可申请提权。
