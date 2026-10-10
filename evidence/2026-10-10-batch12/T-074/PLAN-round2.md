# T-074-1：执行主控决定 01 后的 Codex 实验（2026-10-10）

依据当前对话“主控 #5”及 controller-decision-01.md，起点 `92bda89cf9a46e503fe73a337ab11522d961e57d`。目标与非目标保持：只核实 R6/R7，不写产品、不做 T-075、Claude 不启动。REALITY GATE: INCOMPLETE，待真实证据。

- M1：一次写文字加 `\r`；旧实验 1 次补字段 M1，旧观察窗口 42 秒不改写成 60 秒。
- M2：写文字，300 ms 后单写 `\r`。
- M3：写 bracketed paste 包裹的文字，300 ms 后单写 `\r`。
- idle pilot 每种合计 2 次。失败输入不重投；采用新序号。未送达方法只报 pilot，不加自动 Enter。
- 后续为送达方法记录至少 10 次，覆盖 idle/running/awaiting_approval；观察窗口 60 秒，原生 user.text 是实际消息 oracle。无法取到时不从屏幕补值。
- R6 在夹具中通过明确 require_escalated 的一次标记文件写入触发批准。记录 notify、OSC、native rollout、内部日志的外部接收时刻。只有登记的实验输入带回车，不发送空白 Enter 默认批准；收尾用取消/中断或停止自己的进程。
- 30 个主 turn 上限含前轮 2 个已启动主 turn，辅助标题另计。计划不超过 26 个累计主 turn，留出检查空间；预算预留按 launch + 注入请求计，再以 native task_started 核对实际。
- 状态只取 native task_started/task_complete/turn_aborted 和仅启用 approval-requested 的 OSC9；OSC9 的 awaiting_approval 标签明确是按启动配置推断，需实际调用与夹具副作用交叉核对。不能把未知状态自动补成 idle。
- 允许维护 findings/README.md 一行索引；其余原写入边界不变。全部旧结果与异常记录保留。本轮每个宿主保存实际脚本副本，避免运行中脚本变化影响重放。

Tracer bullet 仍未开始；Deep modules 不引入产品 API；Ubiquitous language 沿用原生会话、窗格与派发记录。每项新实验写前登记、分方法计数，异常与批准代答单列。
