# T-164-4 RESULTS

状态：PASS（卡内目标：一个 Codex CLI worker 的任务经独立审查通过并经门禁集成到项目工作分支）。范围仅此，未重验与目标无关的旧条目。

## 版本与实例

- 产品基线 aacc1bb81（执行主控提供）；实例 `/private/tmp/t164-dogfood-dc_5rakx`，demo 仓库 `.../demo-repo`，状态目录 `.../state`，Electron PID 96695（可执行文件为 a2a/workbench 下的 Electron.app，窗口 renderer URL 指向本实例 dist，已核对），daemon PID 96694。
- 外层测试员：Claude Sonnet（lcu MCP）。没有读 `auth.json`、`operator.json`，没有连 socket、调用门禁或改库；事后只读 `state.sqlite3`、本实例原生日志与 demo-repo。
- 应用内主控：Claude Code 2.1.310 `claude-haiku-5-5`（命令 `claude --model claude-haiku-5-5`，用户手启；首次出现“信任此目录”，仅对本实例 demo-repo 选 Yes）。

## 经过（时间为本地 12:2x-12:46，事件时间 UTC 16:3x-16:46）

1. 在应用内打开 demo-repo 项目（打开面板里用 Cmd+Shift+G 输入路径；路径栏有自动补全，第一次输入被截断，重打后正确，仅 demo-repo 一个同名目录存在）。
2. 项目终端启动 Claude Code；C1 请它经 a2a request 申请 executor；窗格顶栏出现“申请成为执行主控”，我点“批准”；主控确认角色 approved（图 01、02）。
3. C2 交任务：T-1，Codex worker 新建 shopping.md，只列库存为 0 的食材，worker 与审查员均 gpt-6.1-sol high、不开 Fast，主控写机械检查，审查不过就修订或重派。主控首次保存卡被拒（oracle_paths 为空，事件 #1、#2），自行修正后保存、派发 attempt a1（图 03）。
4. C3 回答主控关于空行/标题的提问（不允许，严格格式）。a1 worker 在 16:32:59 交付。
5. C4“界面显示已交付，请继续”：主控 verify 失败 `oracle_failed`——卡里把完成条件写成主仓库绝对路径，而 worker 交付在 worktree 里（主控自己的卡错误，候选内容正确）。主控按流程 card_save v2、`revise`、reclaim a1、dispatch a2（事件 #88-#127，图 04）。reclaim 一次成功，无 identity_conflict；a2 正常启动并提交（N05/T-170 的失败路径本轮没有触发，只复验了正常路径）。
6. C5 a2 交付后：verify 通过（自检 9/9，正式检查 ACCEPT），门禁开独立审查会话（Codex，T-1-a2-review-1），结论“可合并”，无 findings，5 个变异检查全拒（图 07）。
7. C6：主控打分（3/3）并 integrate，main 17464e6 → 7ce91a8，任务 accepted，PASS（图 08）。

## 集成与门禁事件

- 集成提交 `7ce91a867078651a7f3f8eb87c7d96281fd97293`（demo-repo 的 main，尾注 A2A-Task demo-repo+T-1、A2A-Attempt 4cf99901-9b16-418f-89f9-b82a09c3ae0b、A2A-Role worker、A2A-Tool codex-cli 0.164.0、A2A-Model gpt-6.1-sol、A2A-Effort high）。shopping.md 两行：`- 香蕉（水果）`、`- 面条（主食）`，与 pantry.json 零库存一致（我另外人工对照过）。
- 关键事件序号（state.sqlite3 events）：#3 card_saved；#15 created；#27 claimed；#43 submitted（a1）；#86 delivery_rejected / #87 rejected；#89 card_saved v2；#90 revoked；#93 reclaimed；#125-#127 claimed/dispatched（a2）；#142 submitted；#180 verification_result；#201 review_requested；#207 review_started；#208 review_result；#242 review_reclaimed；#247 integration_intent；#281 integrated；#282 score_recorded。
- 没有出现人工介入事件（我没有在 worker 窗格输入）。

## 真实回合统计

| 角色 | 回合 | 来源与实际模型 |
| --- | --- | --- |
| Claude 应用内主控 | 6（用户消息 6 条：申请角色、交任务、答复、继续 x3） | 原生日志 `072dd61f-…jsonl`，全部 assistant 消息模型 `claude-haiku-5-5`；未超 40 上限 |
| Codex worker a1 | 4 | `codex-home/sessions/...01a16ec1...jsonl`，turn_context 4，模型 gpt-6.1-sol，effort high |
| Codex worker a2 | 2 | `...01a16ec4...jsonl`，turn_context 2，gpt-6.1-sol high |
| Codex 审查员 | 1 | `...01a16ecb...jsonl`，turn_context 1，gpt-6.1-sol high |

启动 argv（launch_records）：三个 Codex 会话均含 `-m gpt-6.1-sol -c model_reasoning_effort="high" -c service_tier="default"`（未开 Fast），审查员在 untrusted 的 review-copy 里运行。a1、a2 同时最多一个 Codex worker，随后 a2 与审查员不重叠，并发未超 2。

## 未完成或需要注意

- 额度：本轮未见 Claude 或 Codex 额度、限流、鉴权报错；Claude 状态行 5h 窗口开跑时 51%，结束时 1%（窗口重置），7d 83%。Codex 额度由执行主控监看。
- 问题页最后显示 2 个问题：a1 attempt 上 worker 报的“blocking”（验收路径指向主仓库）在主控已 revise 并重派后仍保持“等你决定”，没有自动关闭，我没有关闭它（卡里不要求，也属于主控/用户的关闭范围）。见图 05 和报告 N01。
- 本轮没有测 N05 的启动失败路径（没有失败），没有测 F01 的人工介入。

## 截图索引（均在本目录）

01-role-request-pending、02-role-approved、03-T-1-dispatched、04-verify-fail-revise-reclaim-redispatch、05-issues-worker-path-blocking、06-worker-a2-submitted-gpt61sol-high、07-verify-pass-review-running、08-integrated-pass（.jpg）。
