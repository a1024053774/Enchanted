# 任务卡 T-164-3（T-164 重跑第三轮：Codex 类 worker 改用 zcode/GLM-5.3-Flash max）

先读 `.project-map/tickets/T-164-real-user-dogfood-rerun.md`（含两段阶段记录）、`findings/2026-10-24-real-user-dogfood-rerun-2.md`（上一轮报告与 N03、N04）、`evidence/2026-10-23-batch24/T-164/card-2.md`（上一轮的方式与隔离，本卡只写不同处）、`.project-map/inbox/20261024T100325Z-ideation-answer-001.md`。

| 字段 | 内容 |
| --- | --- |
| 编号 | T-164-3 |
| 来源 | 构思主控 answer 20261024T100325Z-001。用户 2026-10-24 逐字：“我给里面接了zcode/GLM-5.3-Flash max, 你用他先替代 6.1sol 吧,反正都在 codex 里面”；关于 worker 数量：“这个不做限制,谁说的要限制,为什么呢” |
| 目标 | 以真实用户身份用 Computer Use 走一轮多 agent 流程，**走到审查通过并经门禁集成**。应用内至少 1 个 worker 用 Codex CLI，模型 `zcode/GLM-5.3-Flash`、强度 `max`，其余 `claude-haiku-5-5`。Codex 类 worker 不限总数，被打回照常回收重派。复验：F01（含 T-169：worker **还在调用工具时**在窗格输入一次，交付后再输入一次）、M02、M03；上一轮新发现 N03（T-169）。上一轮已消失的条目走到时顺带确认。T-167 已验过，不必单独重复。写新报告。只报告，不修。 |
| 模型设置 | 像用户一样在 Enchanted 的设置里把 Codex 类 worker 的模型设为 `zcode/GLM-5.3-Flash`、强度 `max`（不开 Fast），或在和应用内主控聊天时让它这样选；审查员按产品规定跟 worker 同 CLI 同模型。核对启动记录里的完整 argv 与终端状态行里的实际模型，不把请求当实际。 |
| 并发 | 包括你自己在内，Codex 会话同时最多 3 个，所以应用内同时最多 2 个 Codex 会话（worker 加审查员）。 |
| 非目标 | 改产品；为省用量删场景；把模型自报当验收；把 GLM 与 6.1-sol 的 worker 表现直接比较。 |
| 修改边界 | 允许：`findings/2026-10-24-real-user-dogfood-rerun-3.md`（新报告）、`findings/README.md`（只加一行索引）、`evidence/2026-10-23-batch24/T-164/rerun-3/**`（文本证据、小截图；`glm-image-probe.md` 是执行主控写的，不要改）。禁止：`workbench/**`、其他测试、`.project-map/**`、`AGENTS.md`、`CONTEXT.md`、`evidence/2026-10-23-batch24/T-164/` 下的脚本与前两轮文件。 |
| 任务类型 | 调研 |
| 复杂度 | L |
| 执行器 | Codex `zcode/GLM-5.3-Flash`，`model_reasoning_effort="max"`，`service_tier="default"`（执行主控先用一次探针确认它能读截图，见 `rerun-3/glm-image-probe.md`） |
| 起点 | 本卡提交所在的 main |
| 唯一写入者 | Herdr agent `b24-t164c`，worktree `/Users/luckye/Documents/Code/a2a-wt-t164c`，分支 `exec/t164c` |

## 用量

- 开跑前执行主控在你的会话里读 `/status` 并记入 `rerun-3/quota-start.md`；你开始时自己看一次写进 RESULTS。GLM 经本机代理，`/status` 可能读不到它的额度，读不到就如实写“读不到”。
- 任何窗口显示已用 ≥ 90%、或出现额度用尽/限流的报错，立即停止新的操作，写下走到哪一步与现场位置，交付 INCOMPLETE。
- 应用内 Claude 真实回合合计不超过 60，逐场记录。截图只在需要证据时截，提示词精简，没有新事实不长轮询（M04）。

## 启动与怎么测

与上一轮相同（`START-APP.sh` 新建 `/private/tmp/t164-dogfood-*` 实例；隔离 `codex-home` 只含当前账号 auth.json 副本、从用户配置复制的 `openai_base_url` 一行、对 demo-repo 的信任与 git add/commit 两条规则；执行主控在沙箱外启动后发给你实例路径和 PID；要重开说 `REOPEN`）。你不要运行这些脚本，也不要读 `codex-home/auth.json`。Computer Use 只操作被告知的隔离 Electron 窗口。遇到系统设置、隐私授权、登录密码、付款、网络授权、GLM 或代理的登录弹窗、发消息发布、用户自己的应用或数据、删除文件，都停下报我。

## 产出

1. `findings/2026-10-24-real-user-dogfood-rerun-3.md`：按上一轮格式逐条写“已消失 / 仍在 / 未能复验（原因）”，附步骤与截图路径；开头写明本轮 Codex 类 worker 换成 GLM-5.3-Flash max，worker 表现与前两轮不可直接比较；新发现按原格式；最后写“Herdr 对照”小结。
2. `evidence/2026-10-23-batch24/T-164/rerun-3/RESULTS.md`：版本、实例路径、截图索引、真实回合统计（Claude 与 Codex 分列，Codex 写实际模型）、用量起止读数、是否走到集成及集成提交、未完成的步骤及原因。
3. `findings/README.md` 一行索引。

只能为 `git add`/`git commit` 申请提权；其他沙箱外动作交给我。用 `git add --sparse` 提交，完成后说 `DELIVERED <提交号>`。语义拿不准、需要用户判断的，停下报我。
