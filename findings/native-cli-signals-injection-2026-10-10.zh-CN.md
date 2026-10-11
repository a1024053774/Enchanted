# 原生 CLI 状态信号与 PTY 注入：T-074 rev 4

**PASS。证据目录里的最小后台完成了决定 04 要求的全部样本：两家各 3 次竞态、2 次模拟用户提交、2 次 Esc 后保持再放行、3 次空闲送达。** T-075 可以按现行 spec 第 6 节实现本地忙状态与人工放行；ticket 保持 open，待执行主控核对关闭。

本报告截至 2026-10-11 UTC，依据 [ticket rev 4](../.project-map/tickets/T-074-pane-signal-and-injection-facts.md) 与 [执行主控决定 04](../evidence/2026-10-10-batch12/T-074/controller-decision-04.md)。完整参数、原始记录、逐次时刻和重放命令见 [RESULTS 的 rev 4 节](../evidence/2026-10-10-batch12/T-074/RESULTS.md)，离线核对结果见 [analysis-rev4.json](../evidence/2026-10-10-batch12/T-074/analysis-rev4.json)。

## 本地记忙挡住了已知竞态

本轮使用 Codex 0.162.1 / **gpt-6-astra xhigh，Fast 请求**，Claude Code 2.1.296 / **claude-haiku-5-5**；两家均为需要批准的主控模式。供应商实际服务 tier unknown。

后台独占 node-pty，所有输入经过同一个写入函数，区分 inject、user_sim、release。提交 CR 写出就记忙，不等开始 hook；UserPromptSubmit 只作记录。正常恢复只认收到时刻晚于最近记忙时刻的 Stop，其余注入排队。两家每次 A 的 CR 后立即尝试 B，后台都已记忙，B 没有落入上一轮的事件延迟窗口。

| 样本 | Codex | Claude |
| --- | --- | --- |
| 竞态 B 被挡住，再由 Stop 放行 | 3/3；排队 1513～2030 ms | 3/3；排队 1141～1459 ms |
| 模拟用户提交后，注入 B 被挡住 | 2/2；排队 1570～1766 ms | 2/2；排队 1090～1363 ms |
| Esc 后保持至少 30 秒，人工 release 后送达 | 2/2 | 2/2 |
| 普通空闲注入作为新消息送达 | 3/3 | 3/3 |

observed / measured：全部 B 都逐字进入普通原生用户记录。两家各 18 次对话提交，分别产生 16 个 Stop；每个 Stop 都能与原生提交的 turn_id / promptId 对上。两次 Esc 中断没有 Stop，没有把它们推断为空闲。未出现未授权的忙时写入、批准代答、正常 Stop 后不放行或无法对应提交的 Stop。

## release 是探针模拟的用户动作

**本轮所有 release 均“由探针模拟”**，记录为用户输入的 action，未声称用户亲自点击了产品界面。

四个批准请求都由 PermissionRequest 确认，随后各一次明确 Esc。Codex 的原生记录有 turn_aborted，Claude 有匹配工具调用的拒绝结果；四个夹具标记文件均未产生。Esc 后保持窗口分别为 Codex 30.153431、30.109941 秒，Claude 30.169985、30.111458 秒，其间一直忙、B 零字节写入。

之后模拟用户 release，只放出队首一条。它是明确的人工放行例外，不伪造 Stop；原始 `gate_state` 仍记录 busy，并有先行的 `release_action`。B 提交后继续忙，直到它自己的 Stop。四条 B 总排队时间为 32213～33270 ms，均完整成为新消息。

Claude 首次信任夹具时的确认回车也经后台记忙，随后另有一次初始化 release，不计入上述两次 Esc 验收。该夹具信任沿用用户已批准的例外；探针没有读写 Claude 凭据或全局设置。

## 证据计数与旧反例

本轮每家 15 次注入，共 30 条 R7，全部 ok；每家另有 3 条 user_sim 消息，单独记录，没有混入注入计数。验收按 case_id 和 B 统计，A/B 两条不算两次竞态。每条文本先登记，再以原生 rollout / JSONL 核对；模型回复“收到”和后台自报均不作为送达证明。

rev 3 两条真实漏放轨迹被本轮的同一许可条件拒绝，本轮 14 条排队 B 全部满足“提交后等待更新 Stop 或显式 release”。这是已有真实轨迹的离线反事实核对，没有重新运行旧危险规则。[红态证据](../evidence/2026-10-10-batch12/T-074/red-rev4.json)。

旧失败原样保留：rev 1 的 Codex / gpt-6.1-sol 曾将批准窗口中的 M3 输入处理为 Accept，并执行夹具写入；rev 3 的旧 Stop 规则曾漏放，两家开始 hook 与回合也不一一对应。这些事实没有被本轮 PASS 撤销。rev 2 两家 worker 不问模式各三次拒绝与后续送达的样本结论继续保留。

## 对 T-075 的影响与限制

inferred：本地提交记忙封住了已观察到的窗口，Stop 与人工 release 各有真实样本支持；T-075 可按现行 spec 第 6 节继续，本轮不需要再改派发规则。用户输入、提交和 release 都必须走同一个后台并保留来源，不能退回只看开始 hook 的方案。

本次 PASS 只覆盖决定 04 的探针场景。产品 GUI 放行、进程重启恢复、任意并发人工编辑、重复或延迟 Stop、多行与其他粘贴模式均未新增验证；也不保证用户在批准仍未结束时误点 release 的结果。不设长期成功率门槛，不将探针通过写成产品验收。

Codex 本轮 18 个主 turn，累计 **50/55**；Claude 本轮 18 个原生回合，加此前保守占用共 **40/40**，已达上限。全部探针已停，隔离 Codex home 已删除，Claude 夹具保留。按任务卡由执行主控核对原始记录，未另开独立审查；产品实现属于 T-075，本 worker 未开始它。
