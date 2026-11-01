STATUS: FAIL

FINDINGS:

- [P1] [panes.ts:555](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:555)、[daemon.ts:1033](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:1033) — 第二轮修复仍未保证阻断到达 CLI。`noteSubmission` 返回阻断后，外层还会写 `request_result`；该写入失败时，catch 会把结果替换成 `ok:false`，丢失 `hook_output`。更早的 `request_received`（daemon.ts:1028）和 `hook_received`（panes.ts:2013）失败也会绕过阻断。数据库持续写入失败时，回车已经送入 CLI，最终却得到退出码 1（gates/cli.ts:226）；现有变异证据已证明两家 CLI 会继续执行，留下没有用户输入记录和人工介入的回合。阻断结果必须覆盖整个钩子请求路径，不能依赖外围日志成功。
- [P2] [panes.ts:546](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:546) — 查询或认领失败、但 `user_submission_blocked` 写入成功时，没有把观察器标为失败。`recordUserSubmission` 尚未调用，而 `onEventWriteFailed` 只在诊断也失败时调用。因此后续窗格输入仍获准进入，与本处提示及 [REPORT.md:12](/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence/REPORT.md:12) 声称的“观察失败后不再接收输入”不符。失败状态应在共同 catch 中设置。

EVIDENCE:

- HEAD 为 `59815ea30e3811d2e449bf5c67b7c70b050081ec`；两次逐字比较，八个范围内文件的工作区 diff 均等于 `candidate.patch`。已读票面、T-206、T-216、前两轮结论、候选及直接调用路径。
- 第二轮的局部诊断失败已修复：`r4b-diag-{claude,codex}.json` 四项检查通过；对应 `diagnostic-unguarded` 变异均失败于 `unrecorded_submission_not_sent_to_model`，模型收到 `failrec`。但 [测试:56](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t229_worker_input_e2e.py:56) 只注入记录和指定诊断事件失败；只读检查夹具库确认，同次请求的 `request_received`、`hook_received`、`request_result` 均成功，未覆盖上述 P1。
- 第一轮第 1 条普通记录异常已阻断；第 2 条已通过最新粘贴及后续提交信号限制认领（[panes.ts:538](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:538)）；第 4 条用户新回合的 prompt 检查已前移；第 5 条已增加重发已认领派发的断言（[测试:274](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t229_worker_input_e2e.py:274)）。`r4-{claude,codex}.json` 均为 `claims=2`、`human_interventions=3`。
- 第一轮第 3 条原引用不足以维持意见：[test_t078_empty_declaration_entry.ts:126](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t078_empty_declaration_entry.ts:126) 模拟注入正文不一致并成功阻断，没有证明用户成功提交被漏记。主控针对该夹具的否定理由成立。
- `red-{claude,codex}.json` 的 `revision=59815ea30`，`observed.after_1` 带 keys、`after_2=[]`，确在业务断言失败。认领、重复记录、草稿光标、清稿及逐键记录变异也有对应失败；T-206 保留了文字、清稿、人工介入和终端字节检查。
- `submitHook` 覆盖当前四种 CLI 名称。agy/opencode 的 `observed.after_2.content` 仅为 `{"text_uncertain":true}`。Claude 包装由 `claudeSubmittedText` 解开，派发末尾换行由 [store.ts:155](/Users/luckye/Documents/Code/a2a/workbench/src/store.ts:155) 去除，未确认规范化缺陷。
- 只读检查 T-166、T-216、T-207 夹具库：忙中用户输入有记录；已提交的门禁反馈、主控答复按派发认领，未重复进入用户输入。REPORT 的主要运行结果与摘要、日志一致，但完整 fail-closed 主张受上述发现限制。新增 catch 的“返回阻断”属于本层职责；未发现额外重试、fallback 或兼容路径。

LIMITATIONS:

- 未运行测试、启动服务、连接 hc 或供应商；两条发现来自静态可达路径，未新增故障复现。
- 未实测旧库恢复、被中断派发、Codex 忙中排队、Tab 补全及受管主控／审查员的全部输入路径。
- agy/opencode 使用替身；未核验真实 CLI、截图或进程清理结论。