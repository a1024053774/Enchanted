# 原生 CLI 状态信号与 PTY 注入：T-074 rev 2

**BLOCKED。两家 worker 的“不问模式”各三次验证通过；主控权限 hook 只记录到开始，尚不能支持批准结束后恢复派发。** 按执行主控决定 02 停止后续竞态与 Claude R7 基本项。Claude 认证已解决，不再是本轮阻断点。

本报告截至 2026-10-11 UTC，依据 [ticket rev 2](../.project-map/tickets/T-074-pane-signal-and-injection-facts.md)、[执行主控决定 02](../evidence/2026-10-10-batch12/T-074/controller-decision-02.md)。全部原始输出、CLI 版本、argv、调用用量与重放命令在 [RESULTS](../evidence/2026-10-10-batch12/T-074/RESULTS.md)。旧报告及旧反例保留在证据目录与 Git。

## worker 不弹批准：六个场景的证据

| CLI / 参数 | 越界拒绝 | 随后 M3 消息 |
| --- | --- | --- |
| Codex 0.162.1，workspace-write、-a never | 3 次原生 exec 返回 PermissionError / exit_code 1，标记文件不存在 | 3/3 完整进入 user.text |
| Claude 2.1.296，claude-haiku-5-5、dontAsk，加本会话 Python 命令 deny 规则 | 3 个 Bash 调用均有匹配 tool_use_id 的 is_error=true 拒绝结果，标记文件不存在 | 3/3 完整进入本次原生 JSONL |

observed / measured：消息写入前登记，收到的中文、标记与标点逐字核对；测试阶段没有发送批准按键，没有把后续消息当批准回答。结论只覆盖这六个夹具场景，不是所有越界路径或全部 CLI 配置的保证。启动夹具信任按用户例外明确选择，单独记录。

## 主控 hook：开始可见，结束和请求标识不足

observed：Codex 在 `2026-10-11T01:02:01.928589Z`、Claude 在 `01:02:06.520248Z` 各送出一个 PermissionRequest JSON。两个 logger 都只追加输入原文，不返回批准或拒绝。

关闭之后再观察 30 秒，仍各只有原来的一个 hook 事件。Codex 的 Esc 实际对应 **Cancel / turn_aborted**；独立 Decline 回答未测。Claude 有明确的原生工具拒绝结果。两家标记文件都没有写入。不能把取消改写为已验证全部拒绝/批准路径。

Codex hook 有 session_id、turn_id；Claude 有 session_id、prompt_id，均没有审批 request_id / tool_use_id。Claude 的 prompt_id 与当前用户输入的 promptId 相同，官方定义也明确是用户输入标识。[Claude hook 公共字段](https://code.claude.com/docs/en/hooks#common-input-fields)。

Codex 内部日志另有带 request_id 的 Cancel 响应和 serverRequest/resolved，尚未作为外部编排接口验证；hook/completed 只表示记录脚本完成，并不表示批准窗口结束。没有把这些日志、回合结束或终端文字当作 hook 的替代实现。[Codex hook 文档](https://learn.chatgpt.com/docs/hooks#permissionrequest)。

官方 Claude 文档中，PermissionDenied 只针对 auto mode，不覆盖人工拒绝；PostToolUseFailure 不覆盖执行前的权限拒绝。这些不是本次已验证的结束通道。[PermissionDenied](https://code.claude.com/docs/en/hooks#permissiondenied)、[PostToolUseFailure](https://code.claude.com/docs/en/hooks#posttoolusefailure)。

inferred：已选 PermissionRequest 通道不足以满足 spec 第 6 节“等批准暂停、批准结束后再送”的完整合约。**分段注入竞态未测**，不能宣称它可避免或无法避免；按前置停止条件留待主控决定。

## 原始次数与尚未完成的覆盖

rev 1 已有 16 条 Codex 注入：M1 idle 2 次未证实送达；M2 idle 2 次送达；M3 idle 7 次、running 4 次送达，awaiting_approval 1 次被处理成 Accept 并写入夹具文件。这个危险反例没有删除。

rev 2 新增 14 条：两家各 4 条 idle（拒绝/批准请求的起始消息）和 3 条 never_after_denial，均送达。累计原始文件 30 条。Claude 仅有 7 条，尚未达到至少 10 次，也没有 running 与受控竞态覆盖。没有设成功率门槛，也没有因为尚有额度就越过停止条件继续。

Codex 累计 23/30 个主 turn。Claude 原生输入回合 10（含认证失败），对首次没有原生记录的启动再保守计 1，共 11/15。探针没有读取凭据或发起登录；成功会话的原生模型字段确认为 claude-haiku-5-5。所有探针已停，隔离 CODEX_HOME 已删除，Claude 夹具按要求保留在 /tmp。

## 对 T-075 的影响

worker 不问方式可以作为已经取得样本证据的部分；主控“批准结束后恢复派发”的规则仍需要改设计或暂停。请构思主控决定使用什么可核对的恢复条件，再明确后续验证范围。本 worker 不自行改通道、不加读屏、自动回车或重试。决定请求和未完成项见 [needs-decision-03](../evidence/2026-10-10-batch12/T-074/needs-decision-03.md)。
