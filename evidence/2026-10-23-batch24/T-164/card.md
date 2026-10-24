# 任务卡 T-164-1（T-155 重跑：走到集成，含一个应用内 Codex worker）

先读 `.project-map/tickets/T-164-real-user-dogfood-rerun.md`、`findings/2026-10-23-real-user-dogfood.md`（上轮 F01～F07、M01～M04）、`evidence/2026-10-23-batch24/T-155/card.md`（沿用的方式与隔离）、`.project-map/inbox/20261024T061431Z-ideation-answer-001.md`。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-164-1 |
| 来源 | T-164 ready_rev 1；额度决定：用户 2026-10-24 逐字“B 现在开跑,应用内只用 1 个 Codex worker”（构思主控 answer 20261024T061431Z-001） |
| 目标 | 以真实用户身份用 Computer Use 走一轮 Enchanted 多 agent 流程，**走到审查通过并经门禁集成**；应用内恰好 1 个 worker 用 Codex，其余用 `claude-haiku-5-5`。逐条复验上轮 F01～F07、M01～M04，写新报告。只报告，不修。 |
| 非目标 | 改产品；为省额度删减场景；换非 Codex 的外层测试员；把模型自报当验收。 |
| 修改边界 | 允许：`findings/2026-10-24-real-user-dogfood-rerun.md`（新报告）、`findings/README.md`（只加一行索引）、`evidence/2026-10-23-batch24/T-164/**`（文本证据、小截图）。禁止：`workbench/**`、其他测试、`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、本目录的 `app_lifecycle.py`/`START-APP.sh`/`STOP-APP.sh`（执行主控已写好）。 |
| 任务类型 | 调研 |
| 复杂度 | L |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 本卡提交所在的 main |
| 唯一写入者 | Herdr agent `b24-t164`，worktree `/Users/luckye/Documents/Code/a2a-wt-t164`，分支 `exec/t164` |

## 启动（执行主控在沙箱外做）

`bash evidence/2026-10-23-batch24/T-164/START-APP.sh` 新建 `/private/tmp/t164-dogfood-*` 实例：独立 state、user-data、一次性仓库 `demo-repo`（同 T-155 的食材清单），以及只给应用内 Codex worker 用的隔离 `codex-home`（只含 auth.json 副本、对 demo-repo 的信任、git add/commit 两条规则）。启动后我把实例路径和 PID 发给你。需要重开时说 `REOPEN`，由我停界面再启动。你不要运行这些脚本，也不要读 `codex-home/auth.json`。

## 怎么测（与 T-155 相同，补三点）

- 只用 Computer Use 操作你被告知的那个隔离 Electron 窗口；事后可只读查日志/数据库解释现象，并在报告里标明。系统设置、隐私授权、登录密码、付款、发消息发布、用户自己的应用或数据、删除文件——停下报我。
- 场景同 T-155：项目终端里自己输入 `claude --model claude-haiku-5-5` 启动主控 → 申请执行主控并在界面批准 → 提出需要拆成 2～3 个任务的需求（同 T-155 PLAN：分类库存说明、零库存补货单、更新使用说明）→ 主控派 worker（含并行；**其中 1 个选 Codex**，其余 haiku）→ 看流程页、侧栏、终端 → 回答上报 → 审查 → **集成** → 看记录、Reflect、指标。难的情形同 T-155：并行、一次打回、在 worker 窗格中途打字（复验 F01）、切换与滚动、REOPEN、任务视图里开分屏普通终端（T-159）。
- 预算：应用内 Claude 真实回合合计不超过 60，逐场记录；你的状态栏显示 Codex 周额度 ≤3% 时立即停止新的操作，写下已走到哪一步和现场位置，交付 INCOMPLETE。提示词精简，没有新事实时不长轮询（M04）。

## 产出

1. `findings/2026-10-24-real-user-dogfood-rerun.md`：上轮 F01～F07、M01～M04 逐条“已消失 / 仍在 / 未能复验（原因）”，附步骤与截图路径；新发现按上轮格式（现象、复现、截图、为什么不合理、严重程度、类别、建议）；最后“Herdr 对照”小结（开 agent、看谁在干什么、切换、盯进度、回复：已达到 / 未达到 / 部分，并写检查了什么）。
2. `RESULTS.md`：版本、实例路径、每步截图索引、真实回合统计（Claude 与 Codex 分列）、是否走到集成及集成提交、未完成步骤及原因、额度停点（若触发）。
3. `findings/README.md` 一行索引。

只能为 `git add`/`git commit` 申请提权；其他沙箱外动作交我。`git add --sparse` 提交，完成说 `DELIVERED <提交号>`。语义拿不准、要用户判断的，停下报我。
