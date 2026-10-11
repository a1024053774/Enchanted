# 原生 CLI 状态信号与 PTY 注入：T-074 rev 3

**BLOCKED。两家各五次普通空闲注入均完整送达，但“最近事件是回合结束”挡不住新回合开始事件到达之前的输入；T-075 的主控自动注入需要设计决定。** 已停止追加实验，没有用剩余额度重试。

本报告截至 2026-10-11 UTC，依据 [ticket rev 3](../.project-map/tickets/T-074-pane-signal-and-injection-facts.md)、[执行主控决定 03](../evidence/2026-10-10-batch12/T-074/controller-decision-03.md)。原始记录、完整 argv、版本、用量和重放命令见 [RESULTS 的 rev 3 节](../evidence/2026-10-10-batch12/T-074/RESULTS.md)，可离线核对的汇总见 [analysis-rev3.json](../evidence/2026-10-10-batch12/T-074/analysis-rev3.json)。旧报告、失败现场和此前的批准代答反例均保留。

## 空闲样本送达，竞态未被挡住

本轮使用 Codex 0.162.1 / **gpt-6-astra xhigh，Fast 请求**，Claude Code 2.1.296 / **claude-haiku-5-5**；都以需要批准的主控模式运行。供应商实际服务 tier unknown。门禁只读取本次原生会话的 UserPromptSubmit / Stop，最近事件为 Stop 才开始完整 M3：bracketed paste 后至少 300 ms 再发 CR。

| 场景 | Codex | Claude |
| --- | --- | --- |
| 普通空闲注入 | 5/5 原文进入 user.text | 5/5 原文进入普通 user 记录 |
| A 已提交、开始 hook 已收到，再尝试 B | B 排队，未写入 | B 排队，未写入 |
| A 已提交、开始 hook 未收到，再尝试 B | B 被旧 Stop 放行，原文送达 | B 被旧 Stop 放行，原文送达 |
| 正常时序中 Esc 后的队列 | 约 63 秒截止时仍未发送 | 约 64 秒截止时仍未发送 |

observed / measured：Codex 的 A 提交到开始事件收到相隔 **267.998 ms**，Claude 为 **144.548 ms**；B 的第一段都确实写在窗口内。到 B 的 CR 前，两家开始事件已经到达。探针按预先登记的协议只在完整 M3 开始前判断，保存两段的事件快照；没有自行用本地发送占位或第二道判定修补规则。

这两条 B 被原生记录收到，不代表门禁成功：本场景要求它们排队，实际写入已经触发停止条件。不能据此推断在 CR 前多查一次就能消除竞态，第一段已经进入 CLI。四个竞态是第一次结果可知前启动的一批；发现漏放后只完成已启动样本的明确 Esc、观察与清理，没有新增或重试。

## 开始与结束事件并不总能配成一对

observed：两家都取得了 UserPromptSubmit / Stop。Codex 事件带 session_id / turn_id；Claude 带 session_id / prompt_id。正常结束有 Stop，但 UserPromptSubmit 不是可靠的一回合一次通知：Codex 竞态 A/B 共用 turn_id；Claude 运行中三条输入共用 prompt_id，只产生一次正常 Stop。

Claude 还有标识关联差异：五条普通空闲样本中，#501/#502/#503/#505 的开始 hook prompt_id 与该消息最终原生 promptId 不同。例如 #501 开始沿用了前一条就绪消息的标识，随后原生消息和 Stop 使用另一个标识。[原始 hook](../evidence/2026-10-10-batch12/T-074/rev3-claude-main/turn-hooks.jsonl) 与归档中的原文联结保留了这个差异；不能简单按 prompt_id 配对全部开始与结束。

四个 A 的批准请求都明确用 Esc 关闭，Codex 有 turn_aborted / interrupted，Claude 有匹配工具调用的拒绝结果；标记文件都不存在。正常时序两窗再观察约 60 秒，仍没有 Stop，B 一直排队。gap 两窗的观察窗口更短，结果分别记载，没有冒充同样的 60 秒证据。Claude 官方文档也明确 Stop 不在用户中断时运行；这与本次实测相符。[Claude Stop](https://code.claude.com/docs/en/hooks#stop)。

inferred：只看最后一个 Stop 的规则既有提交后的漏放窗口，也缺少本次中断后的队列恢复条件。其他接口能否解决仍 unknown，本轮未授权或验证替代方案。

## Claude running 文字进入附件，未形成独立普通消息

Claude 的两条 running M3 文本完整进入原生 `attachment.queued_command`，队列记录原因为 `absorbed_mid_turn`，以 system reminder 交给当前回合。它们没有形成两条独立普通 user 记录，均记 **other**，附上原文及附件来源；没有写成 lost 或新回合成功。

本轮新增登记 21 条，实际写入 19 条，另两条 B 排队未写入。Claude 累计实际注入 **18 次**，包含两次 running；另有一条未写入队列记录，不计入注入次数。没有设成功率门槛，也不将完整送达文字与成为独立新用户消息混为一项。

## 旧证据仍适用的范围

rev 2 的 worker 不问模式，两家各三次越界请求被真实拒绝，随后三条 M3 消息完整进入原生记录。这个样本结论保留；Codex 使用 **gpt-6.1-sol**，不能改写成 Astra 的结论。PermissionRequest 只有开始、缺少结束与审批请求标识的事实也保留，但 rev 3 已撤回依赖它恢复注入的设计。

rev 1 中，**gpt-6.1-sol / Codex 的批准窗口曾把 M3 输入处理为 Accept**，并执行夹具写文件；登记的文字没有成为用户消息。本轮没有新增批准代答，不能撤销旧危险反例。原始 M1 未证实送达、M2/M3 的样本与失败记录均保留，未拿本轮结果替旧模型或不同方法背书。

## 对 T-075 的影响与交付

spec 第 6 节需要再决定：暂缓主控自动注入，还是修订并验证提交中的状态、分段发送、中断恢复和回合标识关联。worker 不自行实现 pending 状态、重试、自动回车或读屏；也不开始 T-075。最小决定范围见 [needs-decision-04](../evidence/2026-10-10-batch12/T-074/needs-decision-04.md)，blocking issue 为 `20261011T014740Z-worker:s12-t074-issue-001`。

Codex 累计 **32/40** 主 turn；Claude 以原生 promptId 计本轮 11，加此前保守占用共 **22/25**。所有本轮探针已停，两个隔离 CODEX_HOME 已完整删除，Claude 夹具按决定保留。离线脚本核对通过只表示归档与计数一致，整票仍 BLOCKED；按任务卡由执行主控核对原始证据，未另做独立审查。
