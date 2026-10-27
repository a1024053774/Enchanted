# T-192 独立审查（只读）

你是独立审查员。只读审查，不改仓库文件；报告只写到 `/private/tmp/t192-review/REPORT.md`。用中文。

仓库：`/Users/luckye/Documents/Code/a2a`（主 checkout 是 sparse，只读不要 checkout/切分支）。改动全文：`/private/tmp/t192-review/change.diff`（未提交的工作区改动 + 两个新文件）。

票：`/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-192-task-page-gate-history.md`。问题来源：`findings/2026-10-27-two-real-uses.md` 的 U07、U08。

改动要点：
1. 门禁新命令 `task_history`（只读，`src/gates/taskHistory.ts` 把事件整理成步骤、最近审查、打分、集成提交与尾注、关闭）。
2. 门禁新命令 `close`（必须写理由；只允许 ready 且无 current_attempt、无 integration_intent；关闭后 dispatch/claim 拒 `task_closed`）。
3. 界面：没有当前 attempt 的任务不再放空的默认窗格（`app/main.ts`），整页显示 `app/TaskRecord.tsx`；有窗格时记录收在底部。
4. 状态名补 abandoned/upgraded/closed；主控 SKILL.md 加 close 说明。

请重点查：
- 正确性：`close` 的前置条件是否有漏洞（并发、操作锁、run 自动运行中关闭、attempt 已终结 abandoned 的任务等）；`closed` 状态会不会让其他代码路径（runs、resumeRuns、sidebar、metrics、reclaim、integrate、revise/revoke）出错或卡住。
- `main.ts` 去掉默认空窗格后：之后派发新 worker 时任务页能否看到；`launches=[]` 时后续代码（layout、restoreArrangement、pane 保存）是否安全；`options.launch` 判断是否改变了原有拒绝语义。
- `taskHistory` 的事件字段假设是否与 `src/gates/core.ts` 实际写入一致；过滤 verify 拒绝是否会藏掉有用信息。
- 证据：`evidence/2026-10-27-batch28/T-192/`（red-*.json、green-*.json、history_check.ts 与 mutant 结果、ui/ 截图）是否足以支持“已回收的票不再是空页”“关闭后显示已关闭”。
- 设计：有没有多余的兼容分支、吞异常、平行 API。

每条问题写：位置（文件:行）、失败场景（具体输入/状态 → 错误结果）、严重程度。最后给结论：`可合并` 或 `需修复`。不要把没查的写成已查。
