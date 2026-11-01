STATUS: FAIL

FINDINGS:

- [P1] [cli.ts:235](/Users/luckye/Documents/Code/a2a/workbench/src/gates/cli.ts:235)、[daemon.ts:1027](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:1027) — **7 秒检查、8 秒放弃仍不能消除“已记录却被阻断”的窗口。** 记录及回合修改完成后，后台仍先 `await settleInboxFeedback()` 才回包；其中 [daemon.ts:168](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:168) 会等待进程观察，单次允许耗时 5 秒（[panes.ts:1358](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1358)）。请求若在第 6 秒通过检查并记录，反馈处理超过剩余时间，钩子仍会在第 8 秒阻断，留下未执行提交的用户输入、人工介入及回合状态。当前故障注入只延迟 `handle` **之前**（[测试:79](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t229_worker_input_e2e.py:79)），覆盖不到这条路径。至少应把反馈处理移出回包前路径，并补记录成功后回包延迟的业务检查；[REPORT.md:79](/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence/REPORT.md:79) 的保证尚不成立。

- [P1] [panes.ts:1611](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1611)、[测试:239](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t229_worker_input_e2e.py:239) — **T-234 是本票引入的阻断后状态回归，不能仅靠拆票排除。** 本票跳过回车前记录后，回车先把窗格设为 `busy`，Codex 还建立 `active`；随后钩子阻断，没有相应 Stop 恢复状态，后续派发被 [panes.ts:1770](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1770) 持续挡住。现存 `r7d-request-hangs-claude-3.json` 的 `details.no_turn_for_blocked_submission.state="busy"`；`r7d-request-hangs-codex-2.json` 同字段为 `busy`，且 `active.nativeTurn` 非空。[T-234:21](/Users/luckye/Documents/Code/a2a/.project-map/tickets/T-234-blocked-claude-submit-leaves-pane-busy.md:21) 也明确记载修前记录失败会挡住回车。收窄断言后获得 PASS，没有解决这个新增退步。

EVIDENCE:

- 开始、结束均逐字比较：`candidate.files` 范围内工作区 diff 等于 `candidate.patch`，候选未变化；HEAD 为 `59815ea30e3811d2e449bf5c67b7c70b050081ec`。已读票面、前五轮审查、REPORT、候选、直接调用路径及相关摘要和日志。
- [daemon.ts:880](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:880) 的检查在 `panes.signal` 之前；Claude/Codex 提交分支从该检查到 `noteSubmission`、对应回合修改没有 `await`。但同步执行不等于耗时有上界，回包前另有上述异步等待。
- 入口即过期时，外层留下 `request_received`、`request_rejected`，不会进入 [panes.ts:2006](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:2006) 写 `hook_received`，也不会认领、记录或写提交信号。所查消费者没有把 `request_rejected` 当作成功提交证据。
- `r7d-request-hangs-claude-3.json`、`r7f-request-hangs-codex-2.json`：`observed.inputs=[]`，拒绝原因为 `prompt_submit_deadline_passed`。`r7b-mutant-late-handled-claude.json`、`r7e-mutant-late-handled-codex-1.json` 均在记录／拒绝的业务断言失败，确实区分了第五轮前后行为。
- Codex 删除“active 必须为空”的理由成立：[panes.ts:1625](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1625) 由窗口回车建立 active，[panes.ts:1507](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1507) 从 rollout 绑定 nativeTurn；过期请求不进入 `panes.signal`。但这只能证明这些状态不是过期钩子创建的，不能证明阻断后状态正常。
- `red-{claude,codex}.json`：`revision=59815ea30`，`after_1` 带 keys、`after_2=[]`，红态失败在业务断言。`r7-claude.json`、`r7d-codex-1.json`：编辑、历史重发、派发排除、已认领全文重发均通过，`claims=2`、`human_interventions=3`。
- `r5-agy.json`、`r5-opencode.json` 保留草稿文字及 `{text_uncertain:true}`，没有 keys；光标、清稿、重复记录、逐键记录变异均有对应业务失败。人工介入仍在 [core.ts:574](/Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts:574) 的记录事务内派生；查询／记录失败标观察失败的证据与报告一致。
- `run-round7d.sh`～`7f.sh`、`runs.log`、启动失败摘要及日志区分了启动期限失败与业务结果，没有发现用启动失败替代业务通过。未发现候选新增吞异常、fallback、兼容分支或平行阻断路径。

LIMITATIONS:

- 未运行测试、status、服务或供应商命令，未连接 hc；新增时序发现来自静态可达路径，未新增运行复现。
- 两端使用同机 `Date.now()`，没有跨机时钟偏差或时区换算问题；系统校时、休眠及调度延迟未验证，绝对时间检查不能证明固定余量足够。
- 已删除夹具无法回查原库、原生日志或逐条派发认领；旧库恢复、Tab 补全、Codex 忙中排队未实测。agy/opencode 证据使用替身。
- 报告中后台“约 12 秒才起来”及进程清理结论，现存摘要、简短日志和状态表不足以独立核实。