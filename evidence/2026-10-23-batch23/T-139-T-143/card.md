# 任务卡 T-139-1 / T-143-1（同一批验证）

先读 `evidence/2026-10-23-batch23/COMMON.md`（公共约定），以及 `.project-map/tickets/T-139-view-model-split-screen.md`、`.project-map/tickets/T-143-terminal-performance.md`（ticket 全文，用户原话在里面）。

用户 2026-10-23：“T-139 和 T-143同一批验证”。两张票由你一个 worker 在同一分支上先后做，分两组提交（先 T-139，再 T-143），用同一夹具、同一次真实 Electron 运行验证，互不回退。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-139-1、T-143-1 |
| 来源 | 两张 ticket，ready_rev 1（提交 ebbae7bd0） |
| 目标 | T-139：项目视图在同一屏分屏列出任务；点进任务只分屏显示该任务的 agent；点单个 agent 只显示它自己；项目普通终端只在它自己的视图里出现。T-143：先量后改，终端滚动帧率与切换窗格耗时有前后数字，改善项保留、没改善的不留。 |
| 非目标 | 换终端实现；输入法（T-138）；鼠标/焦点上报记录（T-145）；流程页（T-144）；Reflect 状态（T-146）；项目额外目录（T-140，另一个 worker 正在改项目行菜单）。 |
| 修改边界 | 允许：`workbench/app/main.ts`（prepareSelection 与视图、输出推送相关部分）、`workbench/app/preload.ts`、`workbench/app/renderer.tsx`（视图与终端部分；项目行菜单那一处由 T-140 的 worker 在改，你不要动它）、`workbench/app/terminalOutput.mjs`、`workbench/app/*.css`、`workbench/src/sidebar.ts`、`workbench/src/transport.ts`、`workbench/src/daemon.ts` 中输出读取/推送相关部分、`workbench/tests/**` 新文件、`workbench/README.md`、`evidence/2026-10-23-batch23/T-139-T-143/**`。禁止：`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、验收文件。 |
| 验收文件（oracle_paths） | `workbench/tests/test_t091_pane_ipc.mjs`、`workbench/tests/test_t107_live_sidebar_e2e.py`、`workbench/tests/test_t133_t107_terminal_controller_e2e.py` |
| 红态命令 | 新 e2e 加 `--revision ebbae7bd0`：任务视图里出现项目普通终端。 |
| 任务类型 | 前端界面 + 缺陷修复（性能） |
| 复杂度 | L |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | ebbae7bd09cee3a8220b948029f9033dc2906c90（main） |
| 唯一写入者 | Herdr agent `b23-t139`，worktree `/Users/luckye/Documents/Code/a2a-wt-t139-t143`，分支 `exec/t139-t143` |

## 完成条件与交付

1. 一个 e2e（如 `workbench/tests/test_t139_t143_views_perf_e2e.py`），一次真实 Electron 运行覆盖两张票：
   - 夹具：项目有两个任务 A、B，各有一个 worker（真实 Claude CLI，`claude-haiku-5-5`，脚本化接口）；一个项目终端经角色申请成为主控。
   - T-139：项目视图列出两个任务（每个任务一格）；进 A 只见 A 的 agent，不含项目终端；点 worker 只见 worker；点项目终端主控只见它自己。每一步截图入证据（png）。切换不重复创建输入凭据，只读（ended）窗格收不到输入，窗格布局持久化仍成立。
   - T-143：同一夹具同一命令，量滚动帧率（例如在窗格里输出大量行后经 CDP 滚动并采帧）与切换窗格耗时，基线（`--revision ebbae7bd0`）与改后各一份数字入证据。逐项试 ticket 列的四项（screenReaderMode 默认关、WebGL 渲染、输出推送或缩短轮询、切换时不销毁已连接窗格或只回放最近一屏），每项前后数字写进 RESULTS.md，没改善的撤掉。新依赖（如 `@xterm/addon-webgl`）若需要，先确认 `workbench/node_modules` 里已有；没有就上报，不要自己装。
   - 切换后输出不丢、不重复（偏移核对），焦点与输入仍正确。
2. 红态：`--revision ebbae7bd0` 在 T-139 的检查上失败。至少两个变异：任务视图又带上项目终端；切换后重复回放（输出重复）。
3. 回归：`test_t091_pane_ipc.mjs`、`test_t107_live_sidebar_e2e.py`、`test_t133_t107_terminal_controller_e2e.py` 绿态。
4. RESULTS.md 分 T-139、T-143 两节写，RUN-OUTSIDE 脚本按公共约定。
