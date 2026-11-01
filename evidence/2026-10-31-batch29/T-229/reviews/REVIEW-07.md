STATUS: FAIL

FINDINGS:

- [P1] [panes.ts:1635](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1635)、[panes.ts:544](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:544) — **`beforeSubmit` 会被没有 UPS 的后续回车覆盖，恢复也没有核对提交身份。** 反例：空闲时提交文字，UPS 尚未处理，再按一次空回车；第一次 UPS 被阻断时，恢复的是第二次回车前的 `busy`。对候选代码的内存回放得到：Claude 为 `busy/active=null`，Codex 为 `busy/active=第一次回车创建的对象`，仍会挡住派发。Stop、Esc 也没有使快照失效（[panes.ts:2370](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:2370)、[panes.ts:1879](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1879)），存在恢复已结束或已退休回合的路径。快照需要绑定实际提交，并防止覆盖后来发生的状态变化。

- [P1] [panes.ts:560](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:560)、[daemon.ts:1035](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:1035) — **记录成功后发生异常，仍会留下被阻断提交的记录和忙状态。** `appendUserInput` 已提交用户输入与人工介入事务（[core.ts:617](/Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts:617)），`noteSubmission` 随即丢掉快照；之后 `turn_start_signal` 或 `request_result` 写入失败，后台回 `ok:false`，钩子据此阻断（[cli.ts:238](/Users/luckye/Documents/Code/a2a/workbench/src/gates/cli.ts:238)），但恢复已无快照可用，先前记录也不会撤回。现有故障注入都未覆盖“记录提交成功之后再失败”。记录、状态和钩子的最终放行结果需要保持一致。

- [P1] [daemon.ts:1052](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:1052)、[daemon.ts:1063](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:1063) — **阻断后新增的 drain 路径在数据库持续故障时会产生未处理拒绝。** 即使拒绝诊断失败已经标记观察器失败，仍会执行 drain／反馈查询；数据库继续报错时，catch 又向同一坏库写 `queue_stopped`，该异常穿过 `finally` 后无人接收，可能终止后台。内存回放确认该 Promise 链继续拒绝。这里应复用 [panes.ts:1313](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1313) 已有的、诊断写失败也能收束的故障处理。

- [P2] [test_t229_worker_input_e2e.py:57](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t229_worker_input_e2e.py:57) — **当前 `no-claim` 变异不能运行到业务断言。** 定位串要求 `if (ours && ours.text === text) {`，候选 [panes.ts:558](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:558) 已没有该花括号；静态计数为零，会在 [scripted_claude.py:48](/Users/luckye/Documents/Code/a2a/workbench/tests/scripted_claude.py:48) 报“变异定位必须唯一”。需更新定位并重新取得业务断言失败证据。

EVIDENCE:

- 开始、结束均逐字比较：`candidate.files` 限定的工作区 diff 等于 `candidate.patch`，候选未变化；HEAD 为 `59815ea30e3811d2e449bf5c67b7c70b050081ec`。已读票面、T-234、前六轮审查、REPORT、候选及相关调用路径。
- 第六轮回包等待问题已处理：worker UPS 从期限检查到处理返回没有显式异步等待；`settleInboxFeedback()` 已移到连接关闭后（[daemon.ts:1032](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:1032)、[daemon.ts:1058](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:1058)）。同步数据库操作仍没有固定耗时保证。
- `r9-claude-2.json`、`r9-codex-1.json` 及对应原库一致：两次 `abdc` 各记一条，已认领派发全文由用户重发后另记一条；`observed.claims=2`、`observed.human_interventions=3`。
- `r8-request-fails-claude-2` 原库事件 `seq=158` 的 `input.raw_stdin.prompt` 确含 `failrec⟦主控 #2⟧…`；Codex 对照及第九轮结果支持当前**空闲窗格单次阻断**的草稿处理，不能外推到忙中排队和并发输入。
- `r9-mutant-no-restore-*`、`late-handled-*`、`no-deadline-*` 的有效尝试均失败在业务断言。启动期限失败的尝试为零项业务检查，REPORT、摘要和 `runs.log` 没有将其算作业务通过。
- `red-{claude,codex}.json` 的基线为 `59815ea30`，`observed.after_1` 带 keys、`after_2=[]`。agy/opencode 的第九轮摘要保留 `text_uncertain`、不带按键；人工介入仍由记录事务派生。未发现新增兼容分支或备用记录路径。

LIMITATIONS:

- 未运行测试、status、服务或供应商命令，未连接 hc；新增发现来自静态可达路径及隔离内存回放，没有新增端到端复现。
- 未实测忙中阻断、恢复窗格、Tab 补全及问答确认与阻断交错；agy/opencode 使用替身。
- 后台连不上、余量外回包可以明确列为限制，但不能据此宣称“后台未回 ok 就证明 CLI 已阻断”。8 秒从 `requestAt` 起算，启动、输出和调度耗时仍未获得完整保证。
- 已删除夹具无法回查；未独立核实报告中的全部进程清理结论。