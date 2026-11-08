# 审查 01（Codex gpt-6.1-sol high，只读，codex exec，2026-11-07）

命令：`codex exec -m gpt-6.1-sol -c model_reasoning_effort=high -c check_for_update_on_startup=false -s read-only -C <worktree> "$(cat prompt-01.md)" < /dev/null`。原始输出约 580 KB（含读文件回显），只留结论原文如下；原始日志未进仓库。

STATUS: **FAIL**  
SUMMARY: 3 项已确认问题；另有未证实风险和验收缺口。  
TARGET: `ab912013bc556c9f2cc2bdb705955c6fa489d826`，基线 `94abc1347`。以下行号均指该提交；审查期间出现的未提交文档修改不计入候选。

FINDINGS:

1. **[P2] 符号链接可越过实际目录边界。**  
   [questions.ts:53](/Users/luckye/Documents/Code/a2a-wt/t251/workbench/src/questions.ts:53) 只用 `relative()` 做词法判断，没有核对真实路径。只读探针使用已有链接：
   - 批准目录：`/private/var/select`
   - cwd：`/private/var/select/developer_dir`
   - 实际目标：`/Applications/Xcode.app/Contents/Developer`

   session、prompt 等字段正确时，父版本拒绝，候选接受。因此，启动目录内指向外部或兄弟目录的链接仍可能通过公共钩子、SessionEnd 和 compact 的同一检查。应补上真实目录边界核对及向外链接反例。

2. **[P2] 系统问题错误宣称窗格已经空闲、可以回收。**  
   [core.ts:819](/Users/luckye/Documents/Code/a2a-wt/t251/workbench/src/gates/core.ts:819) 无条件写入这句话，但 [panes.ts:2449](/Users/luckye/Documents/Code/a2a-wt/t251/workbench/src/panes.ts:2449) 会保留排队输入及 interrupted 的 busy 状态。  
   已复现：不可信回合收到匹配 Stop，同时存在 `claudeQueuedPrompts` 或 `interrupted=true`，结束后仍为 busy。此时主控收到“可以回收”的通知，实际回收仍会返回 `worker_working`。应修正提示，保留现有状态保护；未发现它因此提前杀掉 agent。

3. **[P2] 候选中的当前文档与新行为矛盾。**  
   `workbench/README.md:1270` 仍宣称异常 Stop 不完成回合，而本次明确新增“不可信 worker 回合拒收请求后完成回合”。`project_map.py status` 也报告 README、REVIEW 两项核对过期。合并前需同步 README，并完成地图中的 living docs 核对。

EVIDENCE:

- 全程未改文件、未提交；运行了只读检查和内存探针。
- 原有 cwd 单元测试的 13 个案例全部通过。
- 独立探针确认：异 session、子 agent、外部目录、同前缀兄弟目录、T-141 两类兄弟目录均被拒；compact 未启动时仍拒绝，已启动时不改 active。
- 拒收请求经过后续 Stop、重建 relay 对象及文件改名，均只重放拒收；执行次数为 **0**。
- 内存并发调用 `turnRefused` 得到独立编号，未改写任务；普通 `wakeThread` 拒绝被保存为 `undelivered`，不会传回 Stop。

COUNTEREXAMPLE:

- 保存的红态与变异结果覆盖 cwd、compact、错误执行、遗漏系统问题、窗格持续 busy，失败点符合需求。
- 符号链接反例在父版本被拒、候选被接受，确认是本次放宽引入。

LIMITATIONS:

- **未证实：** [panes.ts:1492](/Users/luckye/Documents/Code/a2a-wt/t251/workbench/src/panes.ts:1492) 仍要求 queued transcript 的 cwd 严格等于根目录。若原生记录报子目录，模块探针会留下队列、无法绑定下一回合；尚未确认真实 Claude 会产生这种记录。
- **未证实：** transfer 抛错时，窗格会变为永久失败的 unknown，保留 active，清除 `stopInProgress`。异常注入已确认这一结果，但未找到正常 `turnRefused` 路径中的实际触发条件。
- E2E 只断言问题出现在 `status`，没有断言执行主控收件箱实际送达，也没有“省略送达”的变异。
- 未重跑真实 CLI E2E 或完整回归。保存的绿态使用 `b013c477a`；它与本次 HEAD 的生产代码一致。`relay_scope` 的不完整结果在父版本也存在，不能算本次回归。

RULE:

- 在 cwd 边界测试加入真实向外符号链接；在拒收时序测试加入排队输入、interrupted，以及收件箱送达断言。

**结论：需修复上述 3 项；补齐收件箱送达证据后再判断可合并。**
codex
这两项过期文档已纳入审查结论。当前会话按“只读、不改任何文件”的约定，不修改文档或 Verified；请由实现会话处理。

审查结论仍为 **FAIL／需修复**。
tokens used
154,240
这两项过期文档已纳入审查结论。当前会话按“只读、不改任何文件”的约定，不修改文档或 Verified；请由实现会话处理。

审查结论仍为 **FAIL／需修复**。
