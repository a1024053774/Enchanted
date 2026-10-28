# T-205 门禁拒绝只显示代码（2026-10-27）

状态：PASS。agy（`gemini-3.8-flash-high`）独立审查结论“可合并”，见 `review-2.md`；一条 P3 观察：`relay_receipts` 里每条回执内嵌的 `result` 是门禁原始结果，不带 `explanation`，说明只在 `summary` 里（界面读 `summary`，不影响展示）。

第一次审查（同一份候选）在终端画面上结论也是“可合并”、无问题，但 agy 没把那条回复写进对话库，原始报告没能保存；所以重跑一次，保存为 `review-2.md`，不另放 review-1。

## 覆盖的拒绝码

依据：真实使用的后台记录（用户工作台与第 2 轮试用的 `rejected` 事件：`invalid_task_card`、`oracle_failed`、`repair_submission_required`、`command_unavailable`、`controller_required`、`invalid_path`、`stale_turn`、`oracle_not_found`），加上主控派发、交付、验收、集成主路径上会遇到的码。每条的原因和下一步都对照了 `core.ts` 里抛出它的条件。

`invalid_task_card`、`task_exists`、`unknown_task`、`project_not_opened`、`controller_required`、`executor_required`、`oracle_not_found`、`path_overlap`、`command_unavailable`、`run_blocked`、`worker_working`、`stale_turn`、`stale_attempt`、`stale_session`、`stale_fence`、`stale_thread`、`stale_spec`、`not_submitted`、`repair_submission_required`、`quality_rejection_limit`、`oracle_failed`、`not_verified`、`out_of_card_unjudged`、`score_required`、`already_accepted`、`task_closed`。

没收：`invalid_path`（门禁里有多处来源，一句话说不准）、`oracle_modified`、`needs_reconciliation`、`identity_conflict`（含义随场景变，写错比不写更糟）。表里没有的码不加说明，照旧只有代码。

## 做法

- `workbench/src/gates/refusals.ts`：一张表，每个码一句原因、一句下一步。
- `workbench/src/daemon.ts`：套接字上每个拒绝回执加 `explanation`（`reason`、`next`）。`a2a`、MCP 原样打印后台回执，界面也读同一份，所以三者一致。`error`、`details` 不变。
- `workbench/src/gates/taskHistory.ts`：任务页时间线的“门禁拒绝”在代码后面接原因和下一步；回执带 `missing` 时写出缺的文件。
- `workbench/src/gateReceipts.ts`：worker 窗格的回执摘要（也是记录页“门禁回执”的摘要）有说明时写“原因”“下一步”两行，代替原来的“要改什么由门禁或主控另行说明”。
- 主控技能 `SKILL.md` 与 README 各补一句。

## 测试

`workbench/tests/test_t205_refusal_explanations_e2e.py`：真实后台与门禁，主控终端里的真实 zsh 和真实 `a2a` 命令，worker 是真实 Claude Code（模型换成本地脚本化接口）。

1. 主控 `a2a call dispatch` 一张验收文件不在 Git 里的卡，得到 `oracle_not_found`。
2. 另一张卡派给 worker；worker 交付后，在它的窗格里输入“请再交付一次当前提交”，新回合补交，得到 `stale_turn`。

所有检查都跑完后再判定，修前版本能把三处的现状一次留下。

| 运行 | 被测 | 结果 |
| --- | --- | --- |
| `red-1.json` | 修前（工作树），检查遇错即停 | 失败于 `a2a_reply_explains`（回执只有代码） |
| `red-2.json` | 修前（工作树），收集全部检查 | 6 项失败：a2a 回执、两处时间线、缺文件名、worker 回执、下一步 |
| `red-3.json` | `--revision a3ae46cf2` | 同 red-2 的 6 项失败 |
| `green-1.json` | 修后 | 9 项通过 |
| `mutant-reply-without-explanation.json` | 后台回执不加说明 | 失败：a2a 回执、时间线与回执一致 |
| `mutant-history-without-explanation.json` | 时间线不加说明 | 失败：两处时间线 |
| `mutant-receipt-without-explanation.json` | worker 回执不加说明 | 失败：worker 回执、下一步、时间线与回执一致 |

修前 worker 窗格实际收到的回执（red-2），与试用一致：

```
交付：门禁没有受理（stale_turn）
下一步：结束本回合；要改什么由门禁或主控另行说明。
```

修后（green-1）：

```
交付：门禁没有受理（stale_turn）
原因：这个 attempt 已经交付过；交付被打回（验收或审查判“需修复”）之前，不能再交。
下一步：worker 结束本回合。要补改：主控改卡后按“card_save 存新卡 → revise → reclaim 旧 attempt → dispatch”重派。
```

复现（在 `workbench/tests` 下）：`python3 test_t205_refusal_explanations_e2e.py --summary <新路径> [--revision a3ae46cf2 | --mutant <名>]`

## 没做

- MCP 没有单独跑：`terminalMcp.ts` 把后台回执原样转成 JSON 文本，与 `a2a` 读同一个回执；本测试只走了 `a2a`。
- 时间线检查读的是 `task_history`（界面任务页原样显示其中的 `detail`），没有在窗口里截图核对。
