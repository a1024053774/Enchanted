# 原生 CLI 状态信号与 PTY 注入：T-074 Codex 事实

**BLOCKED。Codex 事实采集完成，完整 T-074 只差 Claude 的隔离认证与真实实验；T-075 的统一窗格派发需要改设计。** Codex 在 idle/running 时能收到分段发送的消息，但在批准窗口的一次注入被处理成命令批准，正文没有成为新用户消息。

范围来自 [任务卡](../evidence/2026-10-10-batch12/card-T-074-1.md)与[执行主控决定 01](../evidence/2026-10-10-batch12/T-074/controller-decision-01.md)。本票只核实 [spec](../.project-map/specs/native-cli-orchestration-2026-10-10.md)的 R6/R7，不写产品代码、不设成功率门槛。原始记录、完整 argv、重放命令、调用与清理见 [RESULTS](../evidence/2026-10-10-batch12/T-074/RESULTS.md)。

## R7：三种发送方法分别计数

固定 Codex 0.162.1，在 node-pty 1.1.0 托管的 zsh 中运行原生交互 CLI。M1 一次写文字与回车；M2 写文字，300 ms 后单写回车；M3 用 bracketed paste 包裹文字，300 ms 后单写回车。每次写前登记，实际收到的文字从原生 user.text 逐字核对。

| 方法 | idle | running | awaiting_approval |
| --- | --- | --- | --- |
| M1 | 2 次 other | 未测 | 未测 |
| M2 | 2 次 ok | 未测 | 未测 |
| M3 | 7 次 ok | 4 次 ok | 1 次 taken_as_approval |

measured：总计 16 次，13 次完整消息、2 次未找到原生消息、1 次批准代答。各方法先有 2 次 idle pilot，随后 M3 的另外 10 次覆盖三状态。旧 M1 的观察为 42 秒，新实验未送达窗口为 60 秒；旧失败没有重投或删除。四次 running 消息独立成条，没有合并。这里只报告原始次数，不宣称长期可靠性。

unknown：M1 未送达的根因、M2 在运行/批准窗口的行为、多行输入、关闭 bracketed paste 的表现和其他渲染时序仍未核实。首轮原报告保存在证据目录，不把它的未知悄悄改成通过。

## 等确认时，文字变成批准操作

observed / measured：模型为夹具文件写入显式请求 require_escalated；批准前文件不存在。M3 写入的正文是：

```text
⟦主控 #16⟧ 这是新的用户消息，不是批准：请不要执行标记命令，只记录本条文字。
```

正文未成为 user.text。登记输入的 bracketed paste 于 `2026-10-10T20:03:16.779Z` 写入，回车于 `20:03:17.083Z` 写入；随后原生日志记录 Accept 响应，命令于 `20:03:17.214Z` completed / exit_code 0，文件内容为 `T074 approval trial 1`。没有额外空白 Enter 或人工批准，副作用只限隔离夹具。该反例单列 taken_as_approval，不能把“不是批准”的正文当作已交给模型的新指令。

## R6：外部程序能拿到什么

observed：同一批准请求在 `2026-10-10T20:03:16.748Z` 发出 OSC 9，payload 为截断的 `Approval requested` 展示文字。inferred：本会话只配置 approval-requested / osc9 / always，因此外部可以结合固定启动配置把这个控制序列映射到等待批准；payload 没有 request id，不构成完整批准协议。

observed / measured：真实批准前后 notify 都只有 agent-turn-complete，未找到批准等待 notify；rollout 保存调用与执行结果，但本轮 event_msg 类型中没有专门的批准等待事件。内部原生日志提供带 request_id 的 Accept 响应作交叉证据。没有读屏或用关键词规则判断状态。

官方配置说明分别描述外部 notify 的回合完成事件和 TUI 的批准请求通知；这里仍以本机固定版本实测为准。[OpenAI 配置说明](https://learn.chatgpt.com/docs/config-file/config-advanced#notifications)。官方文档有 PermissionRequest hook，但本任务未获 hook 安装授权，该路径本机行为仍 unknown。[OpenAI hook 文档](https://learn.chatgpt.com/docs/hooks#permissionrequest)。

Claude 2.1.296 仅查版本/help，未真实启动。PermissionRequest hook 与 OSC 7501 的文档事实不替代实测。[Claude hook 文档](https://code.claude.com/docs/en/hooks#permissionrequest)、[终端状态文档](https://code.claude.com/docs/en/terminal-config#see-session-status-in-your-terminal)。认证继续等用户决定。

## 对下一张票的影响

T-075 要改派发设计，先停下。idle/running 的成功不能外推到批准窗口；写入中状态改变的竞态是 inferred / 本轮未测试。主控需要决定派发与用户批准如何区分，再决定后续验证，不在本 worker 会话加队列、自动回车或重试。决定请求与原始证据见 [needs-decision-02](../evidence/2026-10-10-batch12/T-074/needs-decision-02.md)。

累计 14 个主 turn，未超过 30；另有 4 个自动标题完成通知，不能当作 API 请求总数或金额。所有自建探针已停止，完整临时 home 已删除，凭据未入证据或 Git。Codex 部分已完成采集，整票仍因 Claude 未实测而 BLOCKED；主控尚未独立验收，不上调为 PASS。
