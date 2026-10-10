# 原生 CLI 状态信号与 PTY 注入：T-074-1 首轮事实

**BLOCKED，T-075 先停下。** 固定 Codex 0.162.1 的第一条直接 PTY 注入在 42 秒观察窗口内没有出现在原生用户消息记录里。按任务卡停止，没有补发 Enter 或重投。仅完成 1 次 idle 注入，R6 真实批准、另外两种状态与 Claude 实验尚未完成；不能据此宣称派发可靠，也不能宣称 PTY 方向不可行。

范围与要求来自 [任务卡](../evidence/2026-10-10-batch12/card-T-074-1.md)、[ticket T-074](../.project-map/tickets/T-074-pane-signal-and-injection-facts.md)，目标是核实第三阶段 [spec 第 6 节](../.project-map/specs/native-cli-orchestration-2026-10-10.md)的 R6/R7，不写产品代码、不设成功率门槛。原始记录与重放命令见 [RESULTS](../evidence/2026-10-10-batch12/T-074/RESULTS.md)。

## R7：本轮实际注入

| 项目 | 事实标签 | 记录 |
| --- | --- | --- |
| 入口 | observed | node-pty 1.1.0 托管 `/bin/zsh -il`，在其中运行原生交互 Codex；没有用 Herdr 窗格或无头模式 |
| 注入前状态 | observed | 原生 rollout 的 `task_complete`；未出现后续 `task_started` |
| 发送方法 | observed | 写入前 fsync 登记；一次 `pty.write` 写 UTF-8 单行标记文字与 `\r` |
| 次数与结果 | measured | idle：1 次 `other`；running：0；awaiting_approval：0 |
| 实际用户消息 | observed | 截止时原生 `user.text` 中没有登记文字，`observed_text=null` |
| 失败根因 | unknown | 丢失、草稿、其他输入拦截未区分；原生输入组件日志有 unhandled key event 与 `os error 2`，不足以确定因果 |

登记的文字是 `⟦主控 #1⟧ 中文编码探针一。只回复收到，不调用工具。`。登记时间为 `2026-10-10T19:49:31.927Z`，实际观察为 42.396156 秒。原生记录是消息归属的依据，终端原始字节只保留作诊断。没有从屏幕上抄出 `observed_text`，也没有把模型说“收到”当送达证据。

“**等确认时，注入文字被当作确认的回答**”单独结论：**unknown，未测试**。本轮在第一项未证实送达时已停止，没有实际批准弹窗；不能把未测试记为零次危险事件或安全通过。

## R6：查到的路径与证据边界

| 路径 | 事实标签 | 结论 |
| --- | --- | --- |
| Codex `notify` | observed | 本机收到初始化主回合及自动标题的 `agent-turn-complete` JSON；它证明回合完成通知能送到外部，不证明等确认通知 |
| Codex 终端通知 | unknown | 本次启动配置 `approval-requested` / `osc9` / `always`，没有触发批准；未测得等确认时的输出或时刻 |
| Codex rollout | observed / unknown | 测得 task_started/task_complete 与原生用户消息；批准事件是否落盘未测试 |
| Codex hook | inferred / unknown | 官方文档描述 `PermissionRequest`；本任务禁止安装 hook，本机固定版本的实际行为未测 |
| Claude hooks / OSC 7501 | inferred / unknown | 官方文档描述 PermissionRequest 与 2.1.295 起的 OSC 7501；本机 2.1.296 仅查版本/help，没有真实启动 |

官方配置说明把外部 `notify` 的支持事件列为回合完成，同时另列 TUI 的批准请求终端通知。该文档边界与本机收到的 JSON 相符，但本轮没有完成批准探针。[OpenAI 配置说明](https://learn.chatgpt.com/docs/config-file/config-advanced#notifications)。Codex 的 `PermissionRequest` 在批准前运行是文档事实；安装与信任 hook 需要另行授权，本轮没有采用。[OpenAI hook 文档](https://learn.chatgpt.com/docs/hooks#permissionrequest)。

Claude 文档说明 PermissionRequest 可在工具批准请求时发出 hook 输入，并描述 OSC 7501 的终端支持条件。两者均未在本轮真实测量。[Claude hook 文档](https://code.claude.com/docs/en/hooks#permissionrequest)、[Claude 终端状态文档](https://code.claude.com/docs/en/terminal-config#see-session-status-in-your-terminal)。

## 下一步需要决定什么

现有“写文字再回车”的描述还没有形成经三种状态验证的发送协议。应由构思主控批准下一轮协议、观察窗口和调用额度，保留这次未送达证据；继续核实 R6，再完成 R7 覆盖。本票不自行加自动 Enter、重试或读屏兜底。

Claude 的首次真实启动仍需用户指定隔离认证方式、模型与预算。可用独立 API key 私有注入，或由用户亲自在临时配置目录认证；预计 12–14 个主 turn，建议上限 16，未获批准。具体选项与需要确认的辅助调用计数见 [needs-decision](../evidence/2026-10-10-batch12/T-074/needs-decision-01.md)。两个自建探针已停止，临时 home 整体删除，凭据未进入证据或 Git。
