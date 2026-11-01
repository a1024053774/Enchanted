STATUS: FAIL

FINDINGS:

- [P1] [panes.ts:557](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:557) — **成功 UPS 仍会误释放回车后开始的 IME 组合输入。** 可达顺序：提交 A，A 的 UPS 尚未处理；用户开始组合输入 B，尚未产生 `onData`。此时 [beginComposition:1585](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1585) 已设置 `userDraft=true`，但 `draft.chars=[]、uncertain=false`；A 成功后，`draftHeld` 将占用清为 false。A 结束后，[drain:1779](/Users/luckye/Documents/Code/a2a/workbench/src/panes.ts:1779) 就能在用户仍编辑 B 时送入派发。Claude 新 prompt、排队输入和 Codex 共用此路径。需要保留回车后新产生的组合输入占用，并补“延迟 UPS → compositionstart → UPS 成功 → Stop”的检查。

EVIDENCE:

- 开始、结束逐字比较：`candidate.files` 范围内工作区 diff 均等于 `candidate.patch`，候选未变化；HEAD 为 `59815ea30e3811d2e449bf5c67b7c70b050081ec`。
- IME 调用链：[renderer.tsx:318](/Users/luckye/Documents/Code/a2a/workbench/app/renderer.tsx:318) → [main.ts:574](/Users/luckye/Documents/Code/a2a/workbench/app/main.ts:574) → [daemon.ts:779](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:779)。组合开始只预留占用，不向草稿写字符。现有 [测试:244](/Users/luckye/Documents/Code/a2a/workbench/tests/test_t229_worker_input_e2e.py:244) 只输入 ASCII `zq`，覆盖不到上述反例。
- `r12-{claude-1,codex-2}.json`：主流程五项通过，`observed.claims=2`、`human_interventions=3`。`red-{claude,codex}.json` 的 `after_1` 带 keys、`after_2=[]`，红态有效。
- `r12-{after-record-fails,result-fails}-{claude,codex}-1.json`：提交确实到达本地模型接口、恰好一条记录、窗格失败可见。对应 `record-then-block` 有效尝试失败在业务断言。当前 worker 路径的后续写入失败已由明确的窗格失败状态收束；[daemon.ts:1040](/Users/luckye/Documents/Code/a2a/workbench/src/daemon.ts:1040) 对其他请求仍抛错，未确认新增静默吞异常或备用记录路径。
- 本轮期限、阻断、观察失败变异均有业务断言失败；`r12-{agy,opencode}-1.json` 保留 `text_uncertain`、不带 keys。人工介入仍由 [core.ts:574](/Users/luckye/Documents/Code/a2a/workbench/src/gates/core.ts:574) 的记录事务派生；T-133/T-134、T-157、T-165、T-166、T-207、T-216 回归摘要支持所列结果。
- REPORT:87 所列四次启动期限失败均为零项业务检查，另有补跑，与 `runs.log:741、755、777、811` 起的记录一致。T-108 两个夹具补空草稿合理；重跑与上一轮的 429 项名称及状态完全相同，仍为 **254 PASS、175 INCOMPLETE**。T-078 runtime 业务摘要 PASS，但进程退出码仍为 1，报告没有隐去收尾错误。

LIMITATIONS:

- 未运行测试、status、扫描器、服务或供应商命令，未连接 hc；新增发现来自静态可达路径，未新增运行复现。
- 已删除夹具只能核对保留摘要；未实测旧库恢复、Tab 补全及上述 IME 交错。agy/opencode 使用替身。
- 记录后异常的现有证据支持指定注入场景；固定期限余量仍不能证明任意调度、同步写入及回包延迟下“有记录就必然执行”。