STATUS: FAIL

FINDINGS:

- [P1] [panes.ts:553](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:553) — **迟到的阻断会覆盖后续输入状态，缺少提交身份核对不可接受。** 例如 `request-hangs`：A 在 CLI 端超时阻断后，用户输入尚未发送的 B；后台稍后拒绝 A，却无条件把 Codex 的 `userDraft` 清为 false。B 仍在输入框，排队派发却能通过 [drain:1793](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1793) 的检查，粘到 B 后面并提交。恢复需要核对所属提交及之后的输入变化，保留新草稿。

- [P1] [panes.ts:1872](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1872) — **门禁发送的 Esc 没有使快照失效。** `interruptThread` 退休 Claude 当前回合，但保留 `beforeSubmit`；随后未决 UPS 被拒绝，[submissionBlocked:553](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:553) 会恢复已退休的 `active`。内存回放得到 `active=A`、`claudePromptId=null`、`interrupted=true`。窗口 Esc 的修复应覆盖这个实际中断入口。

- [P1] [panes.ts:2043](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:2043) — **未匹配的旧 Stop 也会删除当前提交的恢复快照。** 清除发生在身份、回合及 Stop 匹配检查之前。反例：空闲时按回车提交 B，旧 Stop 随后到达并被记为 `stop_not_matched`，B 的 UPS 再失败；快照已经消失，窗格仍为 `busy/active=null`。应在确认相关回合确实结束后处理快照。

- [P1] [daemon.ts:1035](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:1035) — **第七轮“记录成功后再失败”的记录问题仍未解决。** 用户输入及人工介入已由 [core.ts:617](/Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts:617) 提交，之后 `turn_start_signal` 或 `request_result` 写失败仍使钩子阻断；恢复窗格不会撤销这些记录，重发又新增一条。[REPORT.md:81](/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence/REPORT.md:81) 对遗留的描述诚实，但不能算已修复。可考虑延后最终记录提交，或统一相关写入的事务边界；追加式记录不要求提前提交。

- [P2] [test_t229_worker_input_e2e.py:262](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t229_worker_input_e2e.py:262) — **本轮 Codex `late-handled` 变异只验证错误码差异。** `r10-mutant-late-handled-codex-1.json` 的四项业务检查全部通过，唯一 `failed` 是 `late_request_refused`：请求已被另一条身份检查拒绝，只是错误码不同。因此 [REPORT.md:87](/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence/REPORT.md:87) 的“都失败在业务断言”过强。应保留单次回车的期限场景，另测重复回车的快照场景。

EVIDENCE:

- 开始、结束逐字比较均确认：`candidate.files` 限定的工作区 diff 等于 `candidate.patch`；HEAD 为 `59815ea30e3811d2e449bf5c67b7c70b050081ec`。已读票面、T-234、八轮候选差异及前七轮审查、REPORT 和相关调用路径。
- 第七轮的重复回车覆盖已修：`beforeSubmit ??=`；两种 CLI 的 `snapshot-overwritten` 变异均在 `pane_idle_after_block` 失败。`no-claim` 定位已修，本轮确实进入业务断言。
- 确认已移到 `request_result` 写入之后。但 [daemon.ts:971](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:971) 可返回 `ok:true, hook_output:{decision:"block"}`，[1051 行](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:1051) 仍清快照；所以 RPC 的 `ok` 并不完全等同于 CLI 放行。
- `r10-{claude,codex}-1.json` 及原库一致：用户记录三条，派发认领两次，人工介入三条。基线 `red-{claude,codex}.json` 的 `after_1` 带 keys、`after_2=[]`，红态确实失败于业务要求。
- `r10-{agy,opencode}-1.json` 及原库保留草稿文字、`text_uncertain`，没有 keys。T-166、T-216 回归原库支持已提交派发被认领、没有混入用户输入。
- 启动期限失败的尝试为零项业务检查；`runs.log:591–598` 保留四次失败，`:628–629` 另记补跑，未冒充业务通过。
- [daemon.ts:1063](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:1063) 的 `recordFailure` 仅改变 drain 异常收束，正常成功路径没有新增分支；未发现新增 fallback、兼容路径或备用记录入口。

LIMITATIONS:

- 未运行测试、服务或供应商命令，未连接 hc；新增反例来自静态路径和内存回放，尚无新增端到端复现。
- 未实测并发提交、Tab 补全及旧库恢复；agy/opencode 使用替身。已删除夹具只能核对保留摘要。
- 7 秒处理期限、8 秒客户端期限仍依赖同步处理和回包及时完成，不能证明所有超时都已被后台观察。