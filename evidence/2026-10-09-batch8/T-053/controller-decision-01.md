# T-053 执行主控决定 01：不合规清单只检查 open 的 ticket（2026-10-09）

依据 ready_rev 1。主控在真实仓库运行 `scripts/inbox ready`：3 条 READY 之外，另有 52 行"不合规"，绝大多数是协议出现之前就已 closed、superseded 或 out-of-scope 的旧 ticket。spec 第 5 节的就绪条件本身包含 `status: open`，对已结束的 ticket 报"缺字段"没有意义，只会淹没真正需要注意的项。

缺陷级修正（T-053 范围内）：
1. "不合规"只针对 `status: open` 的 ticket；已 closed、superseded、out-of-scope 的不列出。
2. open 但缺 `ready` 字段、且没有任何就绪字段的旧 ticket（协议出现前的 open 任务），列为"未标就绪"而不是"不合规"；只有三个字段缺一部分（例如有 `ready` 缺 `ready_rev`）才是"不合规"。
3. 在夹具中各补一例并先红后绿；在真实仓库重跑 `ready`，输出与前后 git 状态存证。
