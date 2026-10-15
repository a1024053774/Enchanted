# T-078 needs-decision：停止条目发给"尚无会话的角色"时怎么处理（2026-10-15）

## 现象（A-13 I1，真实 Claude + 假 API，0 真实模型回合）
- 一次性 Yes 送达，Claude 执行 protocol I_SEND_STOP（inbox send），排队回执结算通过（responses 2）。
- Stop 钩子 → relay 收到请求，**stop 条目已正确生成**（from ideation → to executor，refs thread/attempt/input，entry 982f243c…）。
- 但投递结果 `undelivered`，原因 `role_session_missing`：executor 角色此时还没启动（冻结计划规定 I1 的唤醒读回之后才启动 executor B1）。relay 因此返回 `ok:false, error: wake_undelivered`（事件 116 relay_rejected）。
- 门禁随即给 ideation 自动派发一条反馈回合（事件 117 dispatch_queued "⟦门禁 #3⟧ 本回合的异步请求处理结果如下……"）。假 API 未登记这一回合，回 409 `dispatch_replayed`，Claude 重试 11/11 后停：requests 13、responses 2。A-13 ideation 预算（4 roots / 6 Messages）已超。

## 冲突
冻结的 09B protocol 期望 I1 "实际 Stop/relay 唤醒 executor"，同时又规定 executor 在 I1 之后才启动；产品当前把"目标角色没有会话"视为投递失败并回灌反馈回合。两者不能同时成立。A-13 排练里 executor 是一个确定性 spy 会话，所以没暴露。

## 选项（最小选择在前）
1. **产品：条目留存、待角色会话出现时再投递**。relay 对 role_session_missing 返回成功（delivery 状态为 pending/queued），不回灌反馈回合；executor 会话启动后由现有唤醒路径投递。改 relay/投递语义（core/relay），protocol 与预算不变。
2. **计划：先启动 executor 再做 I1**。改冻结的 09B 启动顺序（I1 前先完成 executor B1 与 onboarding），产品不变。
3. **保持产品语义，protocol 接纳反馈回合**：把"wake_undelivered → 门禁反馈回合"登记进 I1，预算相应增加。

执行主控倾向 1（stop/answer 本应在收件人不在线时留存，用户在构思主控那边发"立刻停 X"时 X 未必正在运行），但这是产品语义与验收口径的改变，按 T-004 交用户决定。

## 现场
A-13 root /private/tmp/t078-2-09b-run-0fe6fcpf 保留未回收（API 45050/45051、daemon 45053、target 45144/45148、ideation Claude 45962/45963）。事件序号 107–126；controller-decision-04.md #297。T-078 真实运行暂停，等决定。
