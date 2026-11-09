# native-04 退出竞态约束（修改前确定）

范围：只修新测试驱动 `stop_owned`，同一 Popen 句柄拥有本次正整数 PID。产品、原生 argv、权限、onboarding、业务断言和 240 秒期限不变。native-03 的原生超长拒绝是真实父版红态；该轮整体因清理竞态 INCOMPLETE，候选尚未开始。native-01/02 继续保留为启动/驱动 INCOMPLETE。

| 时序 | 必须保持的不变式 |
| --- | --- |
| 未退出 | 每轮信号前先由同一 Popen.poll 核对；记录 PGID、当前 PGID 与本次正整数 PID 一致，且不是本进程组，才可发送原有 TERM/KILL。 |
| 已退出 | poll 观察退出后，同一 Popen.wait 取得退出码；不查询或向可能已复用的进程组发送信号。 |
| 检查后退出 | getpgid 或 killpg 的 ProcessLookupError 不能单独证明已回收；只有同一 Popen.wait 成功取得退出状态才可标 complete。wait 超时或其他失败仍 INCOMPLETE，不再发信号。 |
| TERM 后退出 | TERM 等待超时后，在 KILL 前重新 poll；若已经退出则 wait 回收、不发 KILL。若重新检查时 ESRCH，走上一条 wait 证明，不用 ESRCH 猜成功。 |
| 身份改变 | 记录/当前 PGID 不一致，或 PID 不合法，不发该轮信号；继续拒绝并保留诊断。 |
| EPERM | 保留原错误并标清理不完整；不把它当 ProcessLookupError，不改权限，不换信号路径、不重试。 |

在现有 mock 检查中加入退出位置的有界表：初始已退出、TERM 前查询消失、TERM 发送时消失、TERM 超时后已退出、native-03 的 TERM-timeout→ESRCH→wait、KILL 发送时消失、ESRCH 后 wait 无结果、身份改变与 EPERM。全部 OS 调用保持 mock，不增加框架或原生运行。

修改后的检查见 `driver-green-exit-race-04.txt`：10 个检查方法通过，其中本表含 9 个子场景。native-03 冻结脚本上的同一表由 6 个业务断言拒绝，见 `exit-race-native03-counterfactual-04.txt`。未退出时原有 TERM 后 wait 路径、已退出不发信号、EPERM 不替代、身份不一致拒绝及 onboarding 原检查继续通过。当前仅证明驱动修正，候选真实验证仍 INCOMPLETE。

结构自查：只捕获与真实退出竞态对应的 ProcessLookupError；处理层仍是自有进程清理所有者，结果来自原 Popen.wait。wait 失败不转换为成功，其他异常不被捕获为进程已退出；没有新 API、第二套驱动、权限替代或无界重试。
