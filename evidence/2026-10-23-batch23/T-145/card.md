# 任务卡 T-145-1

先读 `evidence/2026-10-23-batch23/COMMON.md`（公共约定）和 `.project-map/tickets/T-145-records-mouse-false-intervention.md`（ticket 全文，用户原话在里面）。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-145-1 |
| 来源 | `.project-map/tickets/T-145-records-mouse-false-intervention.md`，ready_rev 1（提交 ebbae7bd0） |
| 目标 | 终端控制上报（SGR 鼠标 `CSI < … M/m`、焦点 `CSI I`/`CSI O`、设备状态等回复）不再记成用户输入、不算人工介入；仍原样送给 CLI。真实键入照旧记录。已有误记录保留，记录页可标注，不删。 |
| 非目标 | 对用户文字含义做分类（不做；这里只按终端协议序列格式区分我们自己终端产生的上报）；输入法（T-138）；视图（T-139）。 |
| 修改边界 | 允许：`workbench/src/daemon.ts` 中 window 输入记录（`recordInput` 一带）、`workbench/src/panes.ts` 中输入转发相关部分、`workbench/src/userInputRecords.ts`、`workbench/app/RecordsPage.tsx`、`workbench/app/records.css`、`workbench/tests/**` 新文件、`evidence/2026-10-23-batch23/T-145/**`。禁止：`workbench/app/renderer.tsx`、`workbench/app/main.ts`（别的 worker 在改；若判断必须在 renderer 侧区分，上报，不要自己改）、`workbench/src/gates/**` 的验收逻辑、`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、验收文件。 |
| 验收文件（oracle_paths） | `workbench/tests/test_t133_t134_records_metrics_e2e.py`、`workbench/tests/test_t091_pane_ipc.mjs` |
| 红态命令 | 新 e2e 加 `--revision f8aa846252ddd97008a5e506469ce30024aaacab`：只移动鼠标就新增人工介入。 |
| 任务类型 | 缺陷修复 |
| 修复对象 | 用户输入记录的窗格键入通道（`channel: "terminal-window"`） |
| 复杂度 | S |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | f8aa846252ddd97008a5e506469ce30024aaacab（main） |
| 唯一写入者 | Herdr agent `b23-t145`，worktree `/Users/luckye/Documents/Code/a2a-wt-t145`，分支 `exec/t145` |

## 完成条件与交付

1. 新 e2e（如 `workbench/tests/test_t145_mouse_reports_e2e.py`）：真实 Electron，受管 worker 窗格里跑一个开了鼠标模式的 CLI（真实 Claude Code `claude-haiku-5-5` 脚本化接口，或夹具里开 SGR 鼠标模式与焦点上报的程序，写明是哪种）。
   - 经 CDP 只移动鼠标、滚动、切焦点：记录页不新增人工介入，门禁 `human_intervention` 事件数不变。
   - 真正打字一次：新增一条。
   - 开着鼠标模式的 CLI 仍收到鼠标事件（夹具程序记下收到的原字节，比对）。
2. 红态在起点版本失败；至少一个变异（例如过滤也把序列从 PTY 吞掉 → “CLI 仍收到”失败；或不过滤 → “不新增”失败）。
3. 回归：`test_t133_t134_records_metrics_e2e.py` 绿态；`test_t091_pane_ipc.mjs` 在起点已失败，要求与起点同样、不更差。
4. RESULTS.md 与 RUN-OUTSIDE 脚本按公共约定。
