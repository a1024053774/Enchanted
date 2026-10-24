# 任务卡 T-164-4（T-164 第四轮：补验收第 1 条“含 Codex worker 走到集成”）

先读 `.project-map/tickets/T-164-real-user-dogfood-rerun.md`（含三段阶段记录）、`findings/2026-10-24-real-user-dogfood-rerun-3.md`（上一轮报告与 N05、N06）、`evidence/2026-10-23-batch24/T-164/card-3.md`（上一轮的方式与隔离，本卡只写不同处）。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-164-4 |
| 来源 | 构思主控 answer 20261024T135340Z-ideation-answer-001。用户 2026-10-24 逐字：“codex 的额度到 30% 后,你就用 claude 去做 computer use,我刚刚装了 lcu 的 mcp,codex 只用于需要的地方……用 sonnet 去做 computer use. 早点完成,不要把时间花在无意义的事情上”。T-170（N05）已修并经 agy 审查合入。GLM 上游封本机 IP（`rerun-4/glm-route-probe.md`），构思主控 answer 20261024T162332Z-ideation-answer-001 选 A：应用内 Codex 用 gpt-6.1-sol high（用户：“你用他先替代 6.1sol 吧”，GLM 只是临时替代） |
| 目标 | 以真实用户身份用 Computer Use 走一轮，让**一个 Codex CLI worker**（`gpt-6.1-sol`、`high`、不开 Fast）的任务**经独立审查通过并经门禁集成**到项目工作分支。审查员按产品规定与 worker 同 CLI 同模型。被打回照常修复或回收重派，不限次数。顺带：若 Codex 启动失败，按 revise→普通 reclaim→重派走一次并记录（复验 N05/T-170），不要人为制造失败。写新报告。只报告，不修。 |
| 范围 | 只做这一个 Codex 任务；不再派 Haiku worker（上一轮已覆盖混合 CLI）。应用内主控仍用用户自己的 Claude Code（`claude-haiku-5-5`）。 |
| 并发 | 应用内同时最多 2 个 Codex 会话（worker 加审查员）。 |
| 非目标 | 改产品；为省用量删场景；把模型自报当验收；复验与本目标无关的旧条目。 |
| 修改边界 | 允许：`findings/2026-10-24-real-user-dogfood-rerun-4.md`（新报告）、`findings/README.md`（只加一行索引）、`evidence/2026-10-23-batch24/T-164/rerun-4/**`（文本证据、小截图）。禁止：`workbench/**`、测试、`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、`evidence/2026-10-23-batch24/T-164/` 下的脚本与前三轮文件。 |
| 任务类型 | 调研 |
| 复杂度 | M |
| 执行器 | Claude Code `claude-sonnet-5-5`（执行主控起的子代理），Computer Use 经 lcu MCP |
| 起点 | 本卡提交所在的 main |
| 唯一写入者 | 本子代理，worktree `/Users/luckye/Documents/Code/a2a-wt-t164e`，分支 `exec/t164e` |

## Computer Use 边界（lcu）

- 只操作执行主控告诉你的那个隔离 Electron 窗口（Electron.app，renderer URL 在实例目录下；先核对）。不碰任何其他应用、窗口、浏览器、系统设置。
- lcu 的应用授权弹窗只能指向这个隔离 Electron；系统设置或隐私授权、登录与密码、付款、网络授权、GLM 或代理的登录弹窗、发消息或发布、用户自己的应用或数据、删除文件——一律停下，把原文写进最终回复交给执行主控，不要自己批准。
- 不读 `codex-home/auth.json`、`operator.json`；不连 socket、不调门禁 CLI、不改数据库；业务与门禁操作都经界面里的应用内主控完成。事后可只读实例记录与原生日志来解释现象。
- 读 AX 文本优先，只在需要证据时截图；提示词精简，没有新事实不长轮询；不在应用内主控工作时反复读屏。

## 预算

- 应用内 Claude 真实回合合计不超过 40；Codex 回合逐场记录实际模型（看终端状态行与启动 argv）；应用内 Codex 用 ChatGPT 账号额度，执行主控盯会话日志，5h 或周窗口任一已用 70% 即叫停，你保留现场交付 INCOMPLETE。
- Codex 出现额度用尽、限流、鉴权报错，立即停止新的操作，写下走到哪一步与现场位置，交付 INCOMPLETE。

## 启动

执行主控已在沙箱外用 `START-APP.sh` 新建实例并把实例路径、Electron PID 写在下面的“实例”一节。你不要运行生命周期脚本。需要重开窗口时停下，在最终回复里写 `REOPEN` 与原因。

## 产出

1. `findings/2026-10-24-real-user-dogfood-rerun-4.md`：开头写本轮目标与状态（PASS 只在 Codex 任务经门禁集成时才可写；否则 INCOMPLETE 并写原因）、Codex worker 为 gpt-6.1-sol high、外层测试员为 Claude Sonnet（lcu）；正文按上一轮格式写步骤、截图路径、新发现；最后“Herdr 对照”小结。
2. `evidence/2026-10-23-batch24/T-164/rerun-4/RESULTS.md`：版本、实例路径、截图索引、真实回合统计（Claude 与 Codex 分列、Codex 写实际模型）、集成提交与门禁事件、未完成步骤及原因。
3. `findings/README.md` 一行索引。

用 `git -C /Users/luckye/Documents/Code/a2a-wt-t164e add --sparse <路径>` 和 `git -C … commit` 提交（不要 `cd X; git`），完成后最终回复第一行写 `DELIVERED <完整提交号>` 与一句状态。语义拿不准、需要用户判断的，停下在最终回复里报给执行主控。
