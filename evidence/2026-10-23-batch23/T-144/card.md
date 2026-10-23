# 任务卡 T-144-1

先读 `evidence/2026-10-23-batch23/COMMON.md`（公共约定）和 `.project-map/tickets/T-144-flow-page-fixes.md`（ticket 全文，用户原话在里面）。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-144-1 |
| 来源 | `.project-map/tickets/T-144-flow-page-fixes.md`，ready_rev 1（提交 ebbae7bd0） |
| 目标 | 流程页卡片标题改为角色与任务名（UUID 只放悬停提示）；执行主控按它派发了哪个任务的 worker 挂到那条泳道，确实无关联的才进“未归属”并说明原因；不同任务泳道互相独立；一个任务带 T-140 额外目录时泳道显示多个路径。 |
| 非目标 | 会话状态来源（T-146 已统一，沿用，不另算）；已结束会话是否列出（沿用 T-111 规则，已交构思主控另议）；Reflect 页；视图模型。 |
| 修改边界 | 允许：`workbench/src/flow.ts`、`workbench/src/flowStages.ts`、`workbench/app/FlowPage.tsx`、`workbench/app/flow.css`、`workbench/tests/**` 新文件、`workbench/README.md` 中流程页一段、`evidence/2026-10-23-batch23/T-144/**`。禁止：`workbench/src/gates/**`、`workbench/src/daemon.ts`（只读快照足够；若确需改，上报）、`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、验收文件。 |
| 验收文件（oracle_paths） | `workbench/tests/test_t146_session_state_e2e.py`、`workbench/tests/test_t137_reflect_e2e.py` |
| 红态命令 | 新 e2e 加 `--revision <起点>`：标题为 UUID、主控全在“未归属”。 |
| 任务类型 | 前端界面 |
| 复杂度 | S |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 见派发消息 |
| 唯一写入者 | Herdr agent `b23-t144`，worktree `/Users/luckye/Documents/Code/a2a-wt-t144`，分支 `exec/t144` |

## 完成条件与交付

1. 新 e2e（如 `workbench/tests/test_t144_flow_page_e2e.py`），真实后台 + 真实 Electron + 真实 Claude CLI（`claude-haiku-5-5`，脚本化接口）：夹具两个任务，各一个经角色申请的执行主控与它派的 worker，另有一个真无关的主控；其中一个任务所在项目带一个额外目录。
   - 流程页标题无 UUID（悬停提示里可有）；两个主控各在自己任务泳道；无关的主控在“未归属”且显示原因；带额外目录的泳道显示主目录与额外目录两个路径。截图入证据。
2. `test_t111_flow.mjs` 是 T-111 的合同测试：若新标题与归属规则与它的旧期望冲突，不要改它，上报并写进 RESULTS.md，由我裁定。
3. 红态 `--revision <起点>` 失败；至少两个变异（标题回到 UUID；主控按终端而非派发关系归属）被抓住。
4. 回归：T-146、T-137 的 e2e 绿态；`test_t111_flow.mjs` 结果写明。
5. RESULTS.md 与 RUN-OUTSIDE 脚本按公共约定。
