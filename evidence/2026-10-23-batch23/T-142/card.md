# 任务卡 T-142-1

先读 `evidence/2026-10-23-batch23/COMMON.md`（公共约定）和 `.project-map/tickets/T-142-controller-terminal-open.md`（ticket 全文，用户原话在里面）。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-142-1 |
| 来源 | `.project-map/tickets/T-142-controller-terminal-open.md`，ready_rev 1（提交 ebbae7bd0） |
| 目标 | 经角色申请批准的主控能 `a2a call terminal_open`（参数 `cwd`，须在项目主目录或 T-140 的额外目录之内），在界面里开一个该项目的普通终端并返回终端标识；只对本项目已批准的主控开放，沿用 `role_command_not_scoped` 的范围规则；`a2a help` 与插件 SKILL.md 补上用法。 |
| 非目标 | 为每个 harness 加启动参数适配（用户裁定“按建议来”）；改变用户 ⌘T 开终端的行为；T-141 的权限放宽；流程页。 |
| 修改边界 | 允许：`workbench/src/daemon.ts`（主控命令范围与 `terminal_open` 处理）、`workbench/src/panes.ts` 中 shell 启动相关部分、`workbench/src/terminalCli.ts`、`workbench/app/main.ts` 与 `workbench/app/renderer.tsx` 中“后台通知界面出现新终端”的最小接线、`workbench/terminal/**`（`a2a help`、插件 SKILL.md）、`workbench/README.md`、`workbench/tests/**` 新文件、`evidence/2026-10-23-batch23/T-142/**`。禁止：`workbench/src/gates/**`、`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、验收文件。 |
| 验收文件（oracle_paths） | `workbench/tests/test_t121_role_request_e2e.py`、`workbench/tests/test_t124_controller_e2e.py`、`workbench/tests/test_t139_t143_views_perf_e2e.py` |
| 红态命令 | 新 e2e 加 `--revision c113e71203bd37e151241b6ce44bd4bf773e356f`：`terminal_open` 被拒为 `role_command_not_scoped`。 |
| 任务类型 | 后端逻辑 |
| 复杂度 | S |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | c113e71203bd37e151241b6ce44bd4bf773e356f（main，已含 T-140、T-139/T-143、T-145、T-146-3、T-144） |
| 唯一写入者 | Herdr agent `b23-t142`，worktree `/Users/luckye/Documents/Code/a2a-wt-t142`，分支 `exec/t142` |

## 完成条件与交付

1. 新 e2e（如 `workbench/tests/test_t142_terminal_open_e2e.py`），真实后台 + 真实 Electron + 真实 Claude CLI（`claude-haiku-5-5`，脚本化接口）：项目终端里的 CLI 经 `a2a request` 申请执行主控，经界面批准后 `a2a call terminal_open --cwd <项目主目录>`：界面出现新终端，cwd 正确（在新终端里读 `pwd`），返回的终端标识与界面一致。再用额外目录作 cwd 开一次。
2. 反例各一条：cwd 越界（项目主目录与额外目录之外）被拒；未批准的会话被拒；其他项目已批准的主控对本项目被拒。
3. 新开的终端是项目普通终端，在 T-139 的视图里只出现在项目层，不混进任务视图。
4. 红态 `--revision c113e71203bd37e151241b6ce44bd4bf773e356f` 失败；至少一个变异（例如不校验 cwd 范围）被抓住。
5. 回归：T-121、T-124、T-139/T-143 的 e2e 绿态；`test_t091_pane_ipc.mjs` 与起点同样、不更差。注意起点上 `test_t133_t107_terminal_controller_e2e.py` 已知失败（T-146-4 在修，只改 sidebar.ts），不计入你的候选。
6. RESULTS.md 与 RUN-OUTSIDE 脚本按公共约定。
