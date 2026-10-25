# T-179 结果：worker 窗格里的门禁回执改成几行中文摘要，完整内容在记录页

## 状态：PASS

## 依据

ticket T-179（ready_rev 1），来源 `findings/2026-10-25-lcu-real-use.md` 的 L06；用户 2026-10-24 原话：“然后你再用 lcu 测试一下软件看看能不能发现其他问题”。

## 根因

后台在 worker 回合结束、门禁处理完它的请求后，把回执经 `feedbackText` 发回窗格，内容是“本回合的异步请求处理结果如下……”加上整个回执的 `JSON.stringify`（包括整张任务卡、任务记录的全部字段）。完整回执本来就存在门禁库 `relay_results`，界面上却没有地方能看。

## 改动

- `src/gateReceipts.ts`（新）：`receiptLines(command, result)` 把一条回执写成三四行：命令与是否受理；任务、门禁状态、候选提交短号；下一步。状态中文名表 `gateStateNames` 从 `app/renderer.tsx` 挪到这里，渲染层与后台共用一份。
- `src/daemon.ts`：发给 worker 的回执改为摘要，开头说明完整内容在记录页的“门禁回执”；发给主控的回执保持原样（主控要读字段，本票不动）。新增只读命令 `relay_receipts`：按项目列出 `relay_requests` 与 `relay_results`，每条带摘要与完整结果。门禁语义与回执写库不变。
- `app/main.ts`、`app/preload.ts`：`a2a:receipts` 接口。
- `app/RecordsPage.tsx`、`app/records.css`：记录页在“用户输入记录”下新增“门禁回执”一节，每条显示时间、任务、会话角色和摘要，“完整回执”展开后显示完整 JSON。用户输入记录照旧只记用户亲手的输入。

## 验收（真实 Electron，真实后台、门禁、终端主控，真实 Claude Code worker 与审查员；模型是本地脚本化接口，不耗额度）

`workbench/tests/test_t179_receipt_summary_e2e.py`。场景：worker 写文件、提交、submit，门禁把回执发回 worker；主控照常 verify、审查、integrate；然后打开记录页。

| 运行 | 结果 |
| --- | --- |
| 修前 main（`red-main-01`） | 6 项失败：worker 收到整段 JSON（含 `card_snapshot_id` 等），窗格原始输出里 `card_snapshot_id` 出现 2 次；没有状态、短号与下一步摘要；记录页没有门禁回执 |
| 修后 `green-02`、`green-03` | 两次 PASS 10/10 |
| 变异 `no-commit`（摘要不带候选提交） | 被拒：`worker_receipt_has_state_commit_next` |
| 变异 `no-full-text`（记录页不给完整内容） | 被拒：`records_page_full_receipt_matches_store` |
| 回归 `test_t133_t134_records_metrics_e2e.py` | PASS |

`green-02` 中 worker 实际收到的回执：

```
门禁回执（完整内容在记录页的“门禁回执”里）。请仅确认收到并结束；不调用工具、不改文件、不新增请求。
交付：门禁已受理
任务 T-1 · 已交付 · 候选提交 5647c06ef549
下一步：等主控验收；本回合不用再做什么。
```

窗格原始输出中 `card_snapshot_id`、`integration_ref`、`user_input_observer` 出现 0 次。之后 verify、审查、integrate 照常完成（`accepted`）。记录页展开“完整回执”后，内容含完整候选提交号与 `card_snapshot_id`，与门禁库一致。

截图：`shots/green-02-01-records-receipt.jpg`（记录页的门禁回执，第二条已展开）。`green-02` 之后把 `review_submit` 的命令名改成中文“提交审查结论”，又跑了 `green-03`（PASS）。

## setup-error（保留，不算结论）

- `setup-error-01/green-01-integrate-before-review-reclaimed`：第一次 green 中，测试在审查会话回收完之前就发了 integrate，门禁回 `operation_busy`。这是测试时序问题：修前 main 的同一步通过，是因为当时回收恰好先完成。测试改为等到 `review_reclaimed` 事件再 integrate。
- `setup-error-01/regression-ts-01-needs-driver-args`：`tests/test_t078_startup_pending.ts`、`tests/test_conflict_panes.ts` 需要旧驱动传入参数，直接运行在参数检查处退出，没有走到回执代码。未计入回归。

## 没做 / 未验证

- 没有用真实模型跑；回执文字发给真实 Claude 后，模型是否按“仅确认收到并结束”执行，本票没有新增证据。现有行为与修前相同：仍是同一句约束。
- 主控收到的回执没有改。

## 独立审查

agy（gemini-3.8-flash-high，只读）审查候选 909344c60：`T-179 REVIEW PASS`，无 P0～P2。一项 P3：一回合里 worker 发了多条请求时，几条摘要之间没有空行；受管 worker 一回合通常只 submit 一次，本票不改。审查员第一次输出时漏了末行结论，执行主控追问后补出（报告正文不变）。全文 `review-agy-01.md`，启动参数 `review-agy-01-argv.txt`。
