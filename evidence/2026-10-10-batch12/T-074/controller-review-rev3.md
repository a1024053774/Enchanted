# T-074 rev 3 交付：执行主控核对（2026-10-11）

worker 的交付行：`T-074 DONE BLOCKED 040d017`。我的结论：**BLOCKED 成立**。按决定 03 第 4 节第 5 条，“规则挡不住就停”，worker 停下是对的。ticket 不关闭，交构思主控决定。

## 我复跑的
- `python3 -B evidence/2026-10-10-batch12/T-074/analyze-rev3.py`：退出 0。
- 注入统计中，本轮新增的行：
  - Codex on-request M3：idle_gated ok 5、race ok 3、race other 1。
  - Claude manual M3：idle_gated ok 6、race ok 3、race other 1、running other 2。
- `project_map.py status`：0 problems，0 stale。
- 抽查 `rev3-codex-gap/race-timeline.jsonl`：写入 B 之前，门禁看到的最近事件是上一回合的 Stop（model gpt-6-astra）。

## 事实（以 worker 原始记录为准）
1. **空闲门禁在普通情况下可用**：两家空闲注入各 5 次以上，全部作为新消息送达。
2. **有一个漏放窗口**：A 的回车已经提交、但它的回合开始事件还没到达的这段时间里，门禁仍把窗格判为空闲，B 被写了进去。实测窗口长度：Codex 268 ms，Claude 145 ms。B 最终都作为用户消息送达，没有被当成批准，但违背了排队规则。
3. **中断后没有恢复信号**：用户用 Esc 中断后，两家都没有发出 Stop，排队中的消息一直不能放行。
4. **回合开始事件和回合对不上**：Codex 的 A 和 B 共用一个 turn_id；Claude 的 prompt_id 有好几处与原生 promptId 对不上。
5. **Claude 运行中注入**：Claude 正在运行时注入的 2 条，进了排队命令附件（queued_command），没有成为独立的用户消息，记为 other。

## 执行主控对设计的看法（供构思主控转述，不是决定）
- **漏放窗口**：在新工作台里，用户和 a2a 写进窗格的每个字节，都由编排后台经 node-pty 写入，所以后台自己知道“回车已提交”。可以在本地记一个“已提交、等待回合开始”的状态，从而封住这段窗口，不依赖 hook 到达的时延。这是对 spec 第 6 节的设计修订，需要另做验证；worker 没有自行加这个状态，做法正确。
- **Esc 中断后怎么恢复**：目前还没有可用的结构化依据。Codex rollout 里有 turn_aborted 记录，Claude 有一条工具拒绝结果，但它们不是 hook 事件。一个选项是：中断后的队列交给人放行。
- **最小选项**：
  - A：第一版暂不往主控窗格自动注入，只提示，由人放行。
  - B：按上面的思路修订发送与回合状态的合约，再验证一轮。
- **额度**：Codex 已用 32/40，Claude 已用 22/25。如果选 B，Claude 的余量不够再做一轮。
