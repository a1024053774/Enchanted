# T-107 复验结果（多 worker 之后）

- **测试**：`workbench/tests/test_t107_live_sidebar_e2e.py`，提交 `03dff08c1`（与之后的 `cd8037ba4` 相比只差旧测试脚本的一处修正）。被测代码与 T-136 候选 1（`01e0effd7`）相同。
- **结论**：**INCOMPLETE**。多 worker 与审查员的层级、运行中 / 空闲 / 已结束 / 未知、分支领先与落后、点击聚焦都已在真实入口复验；七种状态与“构思主控 → 执行主控”层级仍有缺口，其中三条要用户定方向（见下文）。

## 新的端到端（`e2e/commands.sh`）

运行在干净分离 worktree 里进行。夹具包括：
- 两个项目：demo 领先上游 1 个提交，other 落后 1 个；
- demo 里两个经角色申请批准的项目终端主控（构思、执行）；
- 执行主控同时派出的两个真实 Claude Code worker（模型是本地脚本化接口），T-1 在跑一条长命令，T-2 已交付；
- T-2 的审查员。

期望来自 ticket 与 git 本身。

| 检查 | green |
| --- | --- |
| `workers_under_executor`：两个 worker 挂在执行主控下，第 1 层 | PASS |
| `two_workers_at_once_running_and_idle`：同一时刻 T-1 是运行中、T-2 是空闲 | PASS |
| `terminal_controllers_unknown_not_upgraded`：两个项目终端主控显示未知 | PASS |
| `branch_counts_match_git`：两个项目的分支、领先、落后与 `git rev-list --left-right --count` 一致（demo 领先 1，other 落后 1） | PASS |
| `click_focuses_worker` | PASS |
| `reviewer_under_executor`：审查员挂在执行主控下，第 1 层 | PASS |
| `reclaimed_reviewer_ended`：审查员回收后显示已结束 | PASS |

| 运行 | 结果 | 失败于 |
| --- | --- | --- |
| green | PASS，7 项 | — |
| red-before-t131（`--revision 03b2d66a3`） | 失败 | 第二个派发被拒：`single_worker_slice` |
| mutant-terminal-shown-idle（项目终端主控显示成空闲） | 失败 | `terminal_controllers_unknown_not_upgraded` |
| mutant-parent-launch-ignored（不用启动记录里的父 launch） | 失败 | `workers_under_executor` |

摸底运行 `probe-01` 原样保留（那时 demo 还没有领先的提交）。夹具已归档，见 `fixtures.archive.json`；截图在夹具的 `out/` 里。

## 2026-10-19 的侧栏运行，在当前代码上重跑

`run_t107_sidebar.py` 用保存的启动事实经真实恢复路径重放，覆盖“未恢复”、历史窗格聚焦与侧栏只读。它在当前代码上跑不通了，两处都是测试脚本过时，不是产品回归：

1. **`t107-sidebar-rerun`**：脚本在 vm 上下文里加载后台，没给 `setInterval`；后台的定时器（额度、归档、复盘）需要它。已在 `cd8037ba4` 补上。
2. **`t107-sidebar-rerun-02`**：脚本期望“同一目录出现另一个 Codex 会话的记录时，收集器拒绝（`ambiguous_native_session`）”。T-127 之后，Codex worker 用用户真实的 `~/.codex`，那里本来就有别的会话，收集器只读本会话自己的 rollout 文件，另一个会话的文件根本到不了这个检查。这条断言已经不对，没有改它。

所以“未恢复”和历史窗格这两项，本轮没有在当前代码上重新证明。

## 缺口

- **构思主控 → 执行主控**：两个主控都是项目终端（T-119～T-121 的角色申请）时，库里没有保存两者的关系，侧栏把执行主控放进“未归属”。要显示这一层，需要在某处记下关系（例如批准执行主控的申请时选择它的构思主控），属于设计改动。
- **等待主控回答**：T-124 之后，worker 和审查员没有 AskUserQuestion，问题一律走 `issue` 进问题面板，所以这个状态不会再出现。可选做法：
  - 把“有未答复的问题上报”显示成等待主控回答；
  - 或者从状态集合里去掉这一项。
- **等待用户回答**：只有后台启动的主控（`controller_start`，T-108、T-110 验证过）会产生；用户现在用的项目终端主控没有结构化回合信号，一直显示未知。
- **分支一行**：ticket 要求项目行两行显示“项目名 / 分支与领先提交数”，当前只在项目行的提示（title）里有，界面上看不到。
- 系统通知已由 T-110 改成应用内通知，不在本轮。

## 2026-10-22 补充：侧栏回放在当前代码上重跑（rerun-03～07）

worktree 在每次修改后切到对应提交；命令同上，摘要名依次是 `t107-sidebar-rerun-03`～`07`。`exits.txt` 里全是 1，都原样保留。

| 运行 | 失败于 | 原因与处理 |
| --- | --- | --- |
| 03（`f270720db`） | 只读探针加载后台失败 | harness 用合成模块替换 `panes.ts`，缺 T-133 之后后台引入的 `claudeSubmittedText`、`codexQuestionReply`。改为透传真实模块的全部导出 |
| 04 | `filename` 模式：写入问题后仍是“运行中” | 种下的启动记录没有 `created_at`，日志也不在日期目录。T-127 之后收集器按启动日读 `sessions/年/月/日`，所以一个文件都没读到，前几个模式其实也没读到文件就过了。补上启动时间与日期目录（`c616449c9`）。此前在 `f270720db` 里把“同目录另一会话被拒绝”当作过时删掉，是误判，已恢复：文件真进了收集器后，拒绝照样发生 |
| 05 | 选中项目后等不到 5 个历史窗格 | 工作区页之后，选中项目不会自己打开窗格；分支行格式也已按 T-107 #5 改成 `main · ↑1 ↓0`。按现在的界面改期望 |
| 06 | 同一等待里的 `task-0` | 任务标题位置现在显示仓库路径 |
| 07（到 `run_t107_sidebar.py` 最后一次修改的提交） | 点击会话后等聚焦 | 见下 |

07 已经通过的检查：
- 修前红态；
- 真实后台的根会话与辅助会话隔离，未消费日志下全部表与 trace 零写入；
- 侧栏 IPC 不改任何表与 trace；
- 项目与会话层级，以及三种历史状态：5 个会话“未恢复”、监视器“未知”、一个 worker“已结束”。

07 在点击逐个聚焦时停下：
- 点了 agent-0 之后，任务视图里 5 个历史窗格都打开了，全部只读，恢复原因逐字正确；
- 但键盘焦点不在任何窗格里（`document.activeElement` 不在 `section.pane` 内）。
- 应用在点击会话时会请求 `terminal.focus()`。这是产品回归，还是检查器或窗口焦点的问题，没有查明。

结论：“未恢复”已在当前代码与真实 Electron 上证明；历史窗格的点击聚焦仍未证明，**INCOMPLETE**。
