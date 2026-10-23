# 任务卡 T-146-4（合并回归：交回角色的主控）

先读 `evidence/2026-10-23-batch23/COMMON.md`、`.project-map/tickets/T-146-stale-running-state.md`、裁定 `.project-map/inbox/20261023T125315Z-ideation-answer-001.md`（问题 3：B）。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-146-4（T-146 第四个 attempt） |
| 来源 | T-146 ready_rev 1；起因：T-146-3（7f204cb35，合并 6af6e3028）后 `test_t133_t107_terminal_controller_e2e.py` 失败“超时：身份已放弃”（单独重跑同样失败；合并前两轮回归均通过）。 |
| 目标 | 区分两种“角色结束”：终端关闭或 CLI 退出 → 侧栏保留主控身份、标“已结束”（B，T-146-3 已做，保持）；用户交回角色而终端仍在运行 → 不再作为主控列出，该终端按普通终端显示其真实状态（T-133/T-107 合同：`sidebar_snapshot` 中不再有该 launch 的主控条目）。Reflect 与流程同源一致。 |
| 非目标 | 改 B；改 T-133/T-107 或其他验收文件；流程页标题与归属（T-144 在做）。 |
| 修改边界 | 允许：`workbench/src/sidebar.ts`、`workbench/src/reflect.ts`（只限与此相同的判定）、`workbench/tests/**` 新文件、`workbench/README.md` 对应句、`evidence/2026-10-23-batch23/T-146-a4/**`。禁止：`workbench/src/flow.ts`、`workbench/app/FlowPage.tsx`（T-144 在改；若必须改，上报）、`workbench/src/gates/**`、`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、验收文件。 |
| 验收文件（oracle_paths） | `workbench/tests/test_t133_t107_terminal_controller_e2e.py`、`workbench/tests/test_t146_session_state_e2e.py`、`workbench/tests/test_t146_ended_projection.mjs`、`workbench/tests/test_t111_flow.mjs`、`workbench/tests/test_t107_live_sidebar_e2e.py`、`workbench/tests/test_t139_t143_views_perf_e2e.py`、`workbench/tests/test_t137_reflect_e2e.py` |
| 红态命令 | `python3 workbench/tests/test_t133_t107_terminal_controller_e2e.py --summary <新路径>` 在起点 6af6e3028cbca2d1868e32eda85eeb932b91ef17 失败“超时：身份已放弃”。 |
| 任务类型 | 缺陷修复（合并回归） |
| 复杂度 | S |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 6af6e3028cbca2d1868e32eda85eeb932b91ef17（main，已含 T-146-3、T-145-2） |
| 唯一写入者 | Herdr agent `b23-t146d`，worktree `/Users/luckye/Documents/Code/a2a-wt-t146-a4`，分支 `exec/t146-a4` |

## 完成条件与交付

1. 失败证据：`/Users/luckye/Documents/Code/a2a/evidence/2026-10-23-batch23/merge-1/run-20261023T134713Z/` 的 t133-t107.json/log（并行）与 t133-t107-rerun-alone-01.json/log（单独），fixture `/private/tmp/t133t-aw6z7o9a`。根因：`sidebar.ts` 约 170–180 行对已确认的角色一律保留主控条目，`roleRequest.state === 'ended'` 时标已结束，不看终端是否仍在运行。
2. 按根因修：判定依据应是该终端（pane lifecycle）是否已结束，而不是角色是否结束；交回角色后主控条目不出现，终端以普通终端出现。不改验收文件，不加长超时。
3. 至少一个变异：交回角色后仍保留主控条目（即起点行为）被 T-133/T-107 抓住；关闭终端后主控变成普通终端（T-146-2 的方向）被 T-146 抓住。
4. RUN-OUTSIDE-01.sh：T-133/T-107 红（起点）绿、T-146 绿态与 ended_projection、t111、T-107、T-139/T-143、T-137；`git add --sparse` 提交证据，交付时说 DELIVERED <提交号>。
