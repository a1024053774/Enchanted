# 任务卡 T-146-3（按用户裁定 B）

先读 `evidence/2026-10-23-batch23/COMMON.md`，`.project-map/tickets/T-146-stale-running-state.md`，以及裁定 `.project-map/inbox/20261023T125315Z-ideation-answer-001.md`（问题 3）与原提问 `.project-map/inbox/20261023T101114Z-executor-needs-decision-001.md`。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-146-3（T-146 第三个 attempt） |
| 来源 | T-146 ready_rev 1；用户 2026-10-23 裁定 B：“B 侧栏和流程也列已结束”（经构思主控转述，inbox 20261023T125315Z-ideation-answer-001），并授权修改受保护的 `workbench/tests/test_t111_flow.mjs`。 |
| 目标 | 侧栏与流程页也列出已结束的会话并标“已结束”；Reflect、侧栏、流程三处同一会话同一状态、同一来源（T-146 已统一的来源，沿用）。关闭主控终端后，界面侧栏与后台 `sidebar_snapshot` 一致（合并后 main 上的失败，见下）。T-139 的视图规则（项目终端只在项目层出现）不回退。 |
| 非目标 | 流程页标题与归属（T-144）；记录页；门禁。已结束会话保留多久、要不要折叠，不在本票（如需要，上报）。 |
| 修改边界 | 允许：`workbench/src/sidebar.ts`、`workbench/src/flow.ts`、`workbench/src/reflect.ts`、`workbench/app/renderer.tsx` 与 `workbench/app/main.ts` 中侧栏与视图刷新相关部分、`workbench/app/FlowPage.tsx`、`workbench/app/ReflectPage.tsx`、相关 css、`workbench/README.md` 中对应段落、`workbench/tests/**` 新文件、`evidence/2026-10-23-batch23/T-146-a3/**`。受保护文件的授权改动：`workbench/tests/test_t111_flow.mjs` 中“已结束会话不列出”的断言改为“列出并标已结束”，其余断言、检查名、期望值不动；`workbench/tests/test_t146_*` 中与“侧栏/流程不列已结束”相关的期望按 B 改。每处改动在 RESULTS.md 逐条列出（文件、行、旧期望、新期望、依据）。禁止：`workbench/src/gates/**`、`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、其他验收文件。其他验收文件若与 B 冲突（例如 T-107 断言已结束会话从侧栏消失），不要改，上报。 |
| 验收文件（oracle_paths） | `workbench/tests/test_t139_t143_views_perf_e2e.py`、`workbench/tests/test_t140_extra_dirs_e2e.py`、`workbench/tests/test_t137_reflect_e2e.py`、`workbench/tests/test_t107_live_sidebar_e2e.py`、`workbench/tests/test_t145_mouse_reports_e2e.py`（以及上面授权范围以外的 test_t111、test_t146 部分） |
| 红态命令 | 新或改后的 e2e 加 `--revision bf932d49940104ec099023aa957d06fe95116e92`：已结束会话不出现在侧栏/流程，或关闭主控终端后界面与后台不一致。 |
| 任务类型 | 缺陷修复 + 展示规则变更 |
| 复杂度 | S |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | bf932d49940104ec099023aa957d06fe95116e92（main，已含 T-140、T-146-1、T-139/T-143、T-145） |
| 唯一写入者 | Herdr agent `b23-t146c`，worktree `/Users/luckye/Documents/Code/a2a-wt-t146-a3`，分支 `exec/t146-a3` |

## 背景（两个前 attempt）

- T-146-1（已合入）：三处同源；按当时暂行规则，侧栏与流程不列已结束会话。
- 合并后回归（`evidence/2026-10-23-batch23/merge-1/run-20261023T122101Z/` 的 t146-green.json 与 t146-green-rerun-alone-01.json）：关闭主控终端后，界面侧栏 30 秒内与 `sidebar_snapshot` 不一致。
- T-146-2（分支 exec/t146-a2，d9e5a3ecf，未合入）：查到根因是关闭主控后它的 shell 启动记录在 `sidebar.ts` 里被重新列为普通终端，于是把已结束的项目普通终端跳过。按 B 这个方向不对；参考它的根因分析（`git -C /Users/luckye/Documents/Code/a2a show d9e5a3ecf`），按 B 重新决定：已结束的主控终端在侧栏以什么身份、在哪一层列出，写明理由。

## 完成条件与交付

1. 真实 Electron e2e（可扩展 test_t146_session_state_e2e.py 的 B 部分，或新文件）：关闭主控终端、CLI 自然退出后，Reflect、侧栏、流程三处都列出该会话并显示“已结束”，与后台快照逐项一致；仍运行的显示运行中；截图入证据。
2. 红态在起点失败；至少一个变异（例如侧栏仍过滤已结束；或已结束的主控被列成普通终端）被抓住。
3. 回归：上面验收文件绿态；`test_t111_flow.mjs` 改后绿态、改前在候选上失败（证明改的就是这条规则）；`test_t091_pane_ipc.mjs` 与起点同样、不更差。
4. RESULTS.md 与 RUN-OUTSIDE-01.sh 按公共约定；提交证据用 `git add --sparse`。
