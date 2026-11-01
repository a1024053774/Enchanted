STATUS: FAIL

FINDINGS:

- [P1] [panes.ts:2151](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:2151)、[panes.ts:2172](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:2172) — **成功的 UPS 会释放后来输入的草稿。** 可达顺序：用户提交 A，UPS 尚未到后台；用户继续输入未发送的 B；A 的 UPS 随后成功，无条件设置 `userDraft=false`。此时 `pane.draft` 仍保存 B。A 回合结束后，[drain:1772](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1772) 只检查占用标志，允许派发粘到 B 后提交。Claude 排队分支 [2130 行](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:2130) 同样存在。需要把草稿释放绑定到对应提交，保留该次回车之后的新输入；补“成功 UPS 延迟期间输入 B”的回归。

- [P1] [daemon.ts:1035](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:1035) — **前轮“记录成功后又失败”仍未解决。** [core.ts:617](/Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts:617) 已提交用户输入及人工介入，后续提交事件或 `request_result` 写失败仍使钩子阻断；记录保留，窗格还可能留下没有真实执行的忙回合，重发再新增记录。[REPORT:82](/Users/luckye/Documents/Code/a2a-worktrees/T-229-evidence/REPORT.md:82) 描述诚实，但不能作为已解决。两条连接属实（`store.ts:35`、`gates/core.ts:193`），无法直接跨连接共用事务也属实；这并不证明必须先合并整个库。本层可研究把**这次 UPS 的记录、认领及相关编排写入**集中到一条连接原子提交，并覆盖“最终记录成功后再失败”的故障场景。

EVIDENCE:

- 审查开始、结束均逐字比较：`candidate.files` 范围内工作区 diff 等于 `candidate.patch`，候选未变化；HEAD 为 `59815ea30e3811d2e449bf5c67b7c70b050081ec`。
- 已读 T-229、T-234、T-206、项目规范、前八轮审查、REPORT、候选及相关调用路径。快照、恢复方法及调用均已删除，前轮三条**快照恢复**意见不再成立。
- `r11-mutant-late-handled-{claude,codex}-1.json.failed` 均包含 `no_record_for_blocked_submission`、`pane_idle_after_block`、`dispatch_waits_for_user_draft`，确实失败在业务断言。
- `r11-claude-1.json`、`r11-codex-2.json`：两次 `abdc` 分别记录，已认领派发由用户重发后另记一条；`observed.claims=2`、`human_interventions=3`。基线 `red-{claude,codex}.json` 的 `after_1` 带 keys、`after_2=[]`，红态有效。
- `r11-{agy,opencode}-1.json` 保留草稿文字及 `{text_uncertain:true}`，不带 keys；代码仍在回车时开回合。T-133/T-134、T-157、T-165、T-166、T-207 回归摘要支持各自列出的检查。
- `REPORT:87` 与摘要、`runs.log:642–645、682–693、700–701、729–730` 一致：启动期限失败的尝试没有业务检查，另有补跑，未冒充业务结果。
- T-157/T-166 单元夹具接入记录回调合理。T-108 本轮仍为 **INCOMPLETE，254/429**，通过名称集合与第十轮一致；T-078 runtime 业务摘要通过，但进程退出码仍为 1，日志有收尾错误，不能称整次运行通过。
- 未发现新增 fallback、兼容分支或备用记录入口；`recordFailure` 复用既有故障收束机制。

LIMITATIONS:

- 未运行测试、status、扫描器、服务或供应商命令，未连接 hc；上述发现来自静态可达路径，未新增端到端复现。
- 已删除夹具只能核对保留摘要；未实测成功 UPS 与后续草稿交错、忙中阻断、旧库恢复及 Tab 补全。agy/opencode 使用替身。
- 固定期限余量不能证明所有同步写入及回包都能及时完成。