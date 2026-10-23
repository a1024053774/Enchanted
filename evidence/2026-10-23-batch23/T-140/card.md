# 任务卡 T-140-1

先读 `evidence/2026-10-23-batch23/COMMON.md`（公共约定）和 `.project-map/tickets/T-140-project-extra-directories.md`（ticket 全文，用户原话在里面）。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-140-1 |
| 来源 | `.project-map/tickets/T-140-project-extra-directories.md`，ready_rev 1（提交 ebbae7bd0） |
| 目标 | 项目可以登记额外目录；受管 worker/reviewer/monitor 启动时这些目录可写（Claude `--add-dir` + 沙箱 `filesystem.allowWrite`，Codex 可写根目录）；移除后新启动的会话写不进去；界面“编辑项目”可增删，保存为追加式事件。 |
| 非目标 | 额外目录的独立门禁、Git worktree 隔离、只读模式；网络、MCP、Codex 配置放宽（那是 T-141）；`terminal_open`（T-142）；流程页（T-144）；用户项目终端的行为不变。 |
| 修改边界 | 允许：`workbench/src/**`、`workbench/app/main.ts`、`workbench/app/preload.ts`、新文件 `workbench/app/ProjectSettings.tsx`（或同类新组件）、`workbench/app/renderer.tsx` 中项目行菜单一处（加“编辑项目”入口与挂载对话框，其余区域不动——视图与终端部分由 T-139/T-143 的 worker 同时在改）、`workbench/app/*.css`、`workbench/tests/**` 新文件、`workbench/roles/**` 中关于额外目录的说明、`workbench/README.md`、`evidence/2026-10-23-batch23/T-140/**`。禁止：`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、验收文件。 |
| 完成条件 | 见下节。 |
| 验收文件（oracle_paths） | `workbench/tests/test_t137_reflect_e2e.py`、`workbench/tests/test_t131_parallel_workers_e2e.py`、`workbench/tests/test_t127_codex_home_e2e.py` |
| 红态命令 | 新 e2e 加 `--revision ebbae7bd0`：worker 写外部目录被拒。 |
| 任务类型 | 后端逻辑 + 前端界面 |
| 复杂度 | M |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"`；完整 argv 见 `records/launches.jsonl` 本卡 launch |
| 起点 | ebbae7bd09cee3a8220b948029f9033dc2906c90（main） |
| 唯一写入者 | Herdr agent `b23-t140`，worktree `/Users/luckye/Documents/Code/a2a-wt-t140`，分支 `exec/t140` |

## 完成条件与交付

1. 新 e2e（如 `workbench/tests/test_t140_extra_dirs_e2e.py`）：真实后台 + 真实 Electron。夹具项目加外部目录 X（夹具内创建），另有未添加的目录 Y。
   - 真实 Claude worker（`claude-haiku-5-5`，脚本化接口）在 X 创建文件成功，写 Y 失败。
   - 真实 Codex worker 同样一次：X 成功、Y 失败。Codex 侧真实入口的做法参照 `test_t127_codex_home_e2e.py`；若需要真实模型回合，用户已定 Codex 用 `gpt-6.1-sol`；如该测试只能用隔离 CODEX_HOME 或假接口，按 AGENTS.md“真实 Codex 验收”的规则做，并在 RESULTS.md 写清用的是哪种。
   - 在界面“编辑项目”里移除 X（经 CDP 操作真实对话框），之后新启动的 worker 写 X 失败。
   - 保存是追加式事件：移除后旧的添加事件仍在。
   - 启动记录的完整 argv 里能看到额外目录参数。
2. 红态：`--revision ebbae7bd0` 失败（worker 写 X 被拒，或没有“编辑项目”）。至少一个变异：例如只加 `--add-dir` 不加 `allowWrite`、移除后仍带上旧目录。
3. 界面与角色卡写明：额外目录里的改动不进门禁的审查与集成；worker 交付说明要列出改了哪些额外目录（worker 角色说明在 `workbench/roles/**` 里找对应文件）。
4. 回归：T-131、T-137 的 e2e 绿态。
5. RESULTS.md 与 RUN-OUTSIDE 脚本按公共约定。
