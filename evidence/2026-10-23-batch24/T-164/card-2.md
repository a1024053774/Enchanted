# 任务卡 T-164-2（T-164 重跑第二轮：新 Codex 账号，含 T-167 真实 Codex 复验）

先读 `.project-map/tickets/T-164-real-user-dogfood-rerun.md`（含阶段记录）、`findings/2026-10-24-real-user-dogfood-rerun.md`（上一轮复验与 N01/N02）、`evidence/2026-10-23-batch24/T-164/card.md`（上一轮的方式与隔离，本卡只写不同处）、`.project-map/inbox/20261024T072734Z-ideation-answer-001.md`。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-164-2 |
| 来源 | 构思主控 answer 20261024T072734Z-001，用户 2026-10-24 逐字：“我还有其他 codex号,我已切换,但是这个有 5小时限制,所以不能用这个开发,用这个做需要 codex 的地方”；T-166～T-168 已修并经 agy 审查合入 |
| 目标 | 同上一轮：以真实用户身份用 Computer Use 走一轮多 agent 流程，**走到审查通过并经门禁集成**；应用内恰好 1 个 worker 用 Codex，其余 `claude-haiku-5-5`。复验：上一轮仍在或未复验的 F01、M02、F05、M01；上一轮新发现 N01（T-167）、N02（T-168）；F01 的工作中输入（T-166）。上一轮已消失的条目走到时顺带确认。写新报告。只报告，不修。 |
| T-167 真实 Codex 复验 | 应用内 Codex worker 每次收到门禁回执、用户答复或打回后，回合都应在几秒内开始；侧栏与窗格不应出现“回合未开始”；该 worker 及其审查员的模型始终是启动参数里的 `gpt-6.1-sol` high（看终端底部状态行；若看到换成别的模型，截图并记下时间）。若出现“回合未开始”，截图终端内容后按实情处理并记录，不要替 CLI 回答它的提示。 |
| 非目标 | 改产品；为省额度删减场景；把模型自报当验收。 |
| 修改边界 | 允许：`findings/2026-10-24-real-user-dogfood-rerun-2.md`（新报告）、`findings/README.md`（只加一行索引）、`evidence/2026-10-23-batch24/T-164/rerun-2/**`（文本证据、小截图）。禁止：`workbench/**`、其他测试、`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、`evidence/2026-10-23-batch24/T-164/` 下的脚本与上一轮文件。 |
| 任务类型 | 调研 |
| 复杂度 | L |
| 执行器 | Codex `gpt-6.1-sol`，`model_reasoning_effort="high"`，`service_tier="default"` |
| 起点 | 本卡提交所在的 main |
| 唯一写入者 | Herdr agent `b24-t164b`，worktree `/Users/luckye/Documents/Code/a2a-wt-t164b`，分支 `exec/t164b` |

## 额度（新号有 5 小时窗口）

- 开跑前执行主控已读新号 `/status` 余量并记入 `rerun-2/quota-start.md`；你开始时在自己的会话里也看一次 `/status`，把 5 小时窗口与周窗口的已用比例写进 RESULTS。
- 外层测试员（你）与应用内 Codex worker、其审查员共用这个号。你的状态栏或 `/status` 显示**任一窗口已用 ≥ 90%** 时立即停止新的操作，写下走到哪一步与现场位置，交付 INCOMPLETE。执行主控也在看会话日志，到线会叫停。
- 应用内 Claude 真实回合合计不超过 60，逐场记录。提示词精简，没有新事实时不长轮询（M04）。

## 启动与怎么测

与上一轮相同（`START-APP.sh` 新建 `/private/tmp/t164-dogfood-*` 实例，隔离 `codex-home` 只含当前账号 auth.json 副本、对 demo-repo 的信任、git add/commit 两条规则；由执行主控在沙箱外启动后把实例路径和 PID 发给你；需要重开说 `REOPEN`）。你不要运行这些脚本，也不要读 `codex-home/auth.json`。Computer Use 只操作被告知的隔离 Electron 窗口；系统设置、隐私授权、登录密码、付款、发消息发布、用户自己的应用或数据、删除文件——停下报我。场景、难的情形同上一轮；在 worker 窗格中途打字要在 worker **还在工作时**打（复验 T-166），也要在它交付批次时打一次（T-157）。

## 产出

1. `findings/2026-10-24-real-user-dogfood-rerun-2.md`：按上一轮格式，逐条“已消失 / 仍在 / 未能复验（原因）”，附步骤与截图路径；T-167 真实 Codex 复验单独一节（回执次数、每次从提交到回合开始的观察、模型是否始终不变）；新发现按原格式；最后“Herdr 对照”小结。
2. `evidence/2026-10-23-batch24/T-164/rerun-2/RESULTS.md`：版本、实例路径、截图索引、真实回合统计（Claude 与 Codex 分列）、额度起止读数、是否走到集成及集成提交、未完成步骤及原因。
3. `findings/README.md` 一行索引。

只能为 `git add`/`git commit` 申请提权；其他沙箱外动作交我。`git add --sparse` 提交，完成说 `DELIVERED <提交号>`。语义拿不准、要用户判断的，停下报我。
