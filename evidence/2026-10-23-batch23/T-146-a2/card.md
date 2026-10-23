# 任务卡 T-146-2（合并缺陷修复）

先读 `evidence/2026-10-23-batch23/COMMON.md`，以及 `.project-map/tickets/T-146-stale-running-state.md`、`.project-map/tickets/T-139-view-model-split-screen.md`。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-146-2（T-146 第二个 attempt） |
| 来源 | T-146 ready_rev 1；起因：T-140、T-146、T-139/T-143 合入 main（cb24b5fc9）后的回归 |
| 目标 | 合并后的 main 上 `test_t146_session_state_e2e.py` 绿态重新通过：关闭主控终端后，界面侧栏的会话集合与状态和后台 `sidebar_snapshot` 一致（T-146 的“同一来源”）；同时 T-139 的视图规则（项目终端只在它自己的视图出现）不回退。 |
| 非目标 | 改 T-146 或 T-139 的验收语义；已结束会话是否列出（已交构思主控另议，暂行规则：侧栏与流程不列已结束会话、任何页不显示“运行中”）。 |
| 修改边界 | 允许：`workbench/app/renderer.tsx` 与 `workbench/app/main.ts` 中侧栏与视图刷新相关部分、`workbench/src/sidebar.ts`、`workbench/src/reflect.ts`、`workbench/src/flow.ts`、`workbench/tests/**` 新文件、`evidence/2026-10-23-batch23/T-146-a2/**`。禁止：`workbench/src/gates/**`、`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、验收文件。 |
| 修复对象 | 合并提交 cb24b5fc9（exec/t146 与 exec/t139-t143 的交互） |
| 验收文件（oracle_paths） | `workbench/tests/test_t146_session_state_e2e.py`、`workbench/tests/test_t139_t143_views_perf_e2e.py`、`workbench/tests/test_t140_extra_dirs_e2e.py`、`workbench/tests/test_t137_reflect_e2e.py`、`workbench/tests/test_t107_live_sidebar_e2e.py` |
| 红态命令 | `python3 workbench/tests/test_t146_session_state_e2e.py --summary <新路径>` 在起点 cb24b5fc9 失败于“超时：侧栏轮询已刷新”（执行主控已复现两次）。 |
| 任务类型 | 缺陷修复 |
| 复杂度 | S |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | cb24b5fc98（main） |
| 唯一写入者 | Herdr agent `b23-t146b`，worktree `/Users/luckye/Documents/Code/a2a-wt-t146-a2`，分支 `exec/t146-a2` |

## 完成条件与交付

1. 失败证据（执行主控在沙箱外复现）：`evidence/2026-10-23-batch23/merge-1/run-20261023T122101Z/t146-green.json`（与 T-139 等并行跑）和 `t146-green-rerun-alone-01.json`（单独跑）。两次前两步观察（01-before-close、02-after-cli-exit）界面与后台一致，失败在之后关闭主控终端的那一步：等界面侧栏 `[data-agent-launch]` 集合与 `sidebar_snapshot` 一致，30 秒超时。fixture 保留在 `/private/tmp/t146-k40ls35i`。主 checkout 是稀疏的，这些文件在 `/Users/luckye/Documents/Code/a2a/evidence/...` 下可直接读。
2. 先查根因（例如 T-139 改了侧栏或项目终端的刷新/保留逻辑，终端关闭后界面仍留着该节点或不再刷新），按根因修；不放宽测试、不加长超时。
3. 不改上面列的验收文件。修完写 RUN-OUTSIDE-01.sh，跑 T-146 绿态、红态（起点 cb24b5fc9）、T-139/T-143 candidate、T-140 绿态、T-137、T-107，提交后告诉我。
