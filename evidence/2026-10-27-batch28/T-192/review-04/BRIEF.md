# T-192 独立审查第 4 轮（只读）

你是新的独立审查员。只读审查，不改仓库文件，不操作 /private/tmp/t190 下正在运行的后台或应用；报告只写到 `/private/tmp/t192-review4/REPORT.md`。用中文。

仓库 `/Users/luckye/Documents/Code/a2a`（主 checkout 是 sparse，不要 checkout 或切分支）。候选改动全文：`/private/tmp/t192-review4/change.diff`（未提交改动加两个新文件）。

票：`.project-map/tickets/T-192-task-page-gate-history.md`；来源 `findings/2026-10-27-two-real-uses.md` U07、U08。

前三轮报告在 `evidence/2026-10-27-batch28/T-192/review-01..03/REPORT.md`，处理与复验在同目录 `RESULTS.md` 各轮小节。第 3 轮提 N1～N4：
- N1：`taskHistory.ts` 的 verify 拒绝折叠改为按 attempt 记最近一次验收的打回错误码或合并冲突，同码的第一个 verify 拒绝折叠，用过即清，新交付或新验收清除。
- N2：`docs/index.html` 第 3 步措辞。
- N3：`TaskRecord` 按钮按 busy 禁用。
- N4：保留截断回执，新增 `green4-*` 完整回执、真实回收后的 `ui/11`、`ui/12`。

请：
1. 逐项核对 N1～N4 是否真的修好（能重放的自己重放；`node evidence/2026-10-27-batch28/T-192/history_check.ts` 与 `bash mutants.sh`（在该目录下运行；它会改写 history-check-*.json，请先把这些文件复制到 /private/tmp/t192-review4/ 下再跑，或改在副本目录运行）。
2. 查新的折叠规则有没有误折叠或漏折叠：按 `workbench/src/gates/core.ts` 里写 delivery_rejected、verification_conflict、rejected 的真实路径推演（例如冲突后 worker 被替换、打回后重复 verify、冲突反馈失败写 conflict_rework_unknown 的路径）。
3. 核对 green4 回执与 RESULTS 的叙述一致，证据是否支持 T-192 两条验收：已回收的票点进去不是空页、显示门禁全程；关闭后任务格显示“已关闭”。
4. 抽查 F1～F6、R1～R5 没有被本轮改回。

每条问题写：位置（文件:行）、失败场景（具体输入/状态 → 错误结果）、严重程度。最后给结论：`可合并` 或 `需修复`。不要把没查的写成已查。
