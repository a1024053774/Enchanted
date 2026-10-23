# T-137 候选 2 结果

- **候选**：代码 `fbf68c404`；测试与夹具到 `f602d95b1`。
- **起因**：独立审查 01（`../candidate-1/review-01.md`）结论 INCOMPLETE，缺两条测试证据，另有三条 P3。
- **结论**：**PASS**。复审 02（`review-02.md`）PASS，只剩 1 条 P3：同一毫秒交接没有构造夹具，已知。

## 审查 01 的处理

| 发现 | 处理 | 证据 |
| --- | --- | --- |
| P2：“未归属”没有覆盖 | 场景加 T-3，由桌面操作员派出、没有主控 | 新检查 `session_without_controller_unassigned`：T-3 的 worker 在“未归属”区，且只有它 |
| P2：“已有设置不改写”没有证据 | 场景最后重启后台 | 新检查 `saved_schedule_survives_restart`：开启状态与执行者（模型、强度）都保留。新变异 `defaults-overwrite-saved`（每次启动都写出厂默认）失败在这一项 |
| P3：同一毫秒交接时归到已结束的角色 | 改为取最后一个符合的角色（`findLast`） | 只有代码：同一毫秒的边界没有构造 |
| P3：监视器没有覆盖 | 场景里 E2 给 T-2 挂一个监视器 | 并入 `sessions_under_the_role_held_when_they_started`：监视器在 E2 下、第二层 |
| P3：`version` 不在 effect 依赖里 | 不成立：依赖是 `[project, version]`（`RetrospectiveSections.tsx` 第 34 行），原页面同样 | — |

- **夹具**：`tests/scripted_claude.py` 的启动配置加了监视器角色卡，供 `attach` 使用。

## 端到端（`e2e/commands.sh`）

| 运行 | 结果 | 失败于 |
| --- | --- | --- |
| green | PASS，10 项 | — |
| red-parent（`--revision c24d58955`） | 失败 | `schedule_off_by_default` |
| mutant-schedule-on-by-default | 失败 | `schedule_off_by_default` |
| mutant-defaults-overwrite-saved | 失败 | `saved_schedule_survives_restart` |
| mutant-ended-not-listed | 失败 | 会话树不到 8 行 |
| mutant-role-by-terminal-only | 失败 | `sessions_under_the_role_held_when_they_started` |
| mutant-score-on-attempt | 失败 | `score_on_scored_worker_only` |
| t136-green | PASS，13 项 | — |

- **摸底运行**：`probe-01` 至 `04` 原样保留。
  - `01`：夹具没有监视器配置。
  - `02`：重启时旧后台还没退出，这次没留下摘要。
  - `03`：重启时操作员凭据文件已存在。
  - `04`：通过。
- **夹具**：已归档，见 `e2e/fixtures.archive.json`。
