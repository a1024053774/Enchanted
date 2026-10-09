# 决定 04 的失败方式与验收信号

目标：受管 WS 结构化 answer 没有 message、有有效 request 时显示；消息渠道的 answer 仍须有 message 身份。非目标：provider 行为、审批语义、UI 布局和正式工作台。Tracer bullet 走受控待答状态 → 真实 WS → SQLite 输入及派生事件 → 实际 web 解析器；Deep modules 的事实字段仍在门禁事务里生成，Ubiquitous language 沿用 request、channel、用户输入与人工介入。

显示路径可能失败：

1. 有效结构化答复进入受管 attempt，记录成功，解析器因 message 为空抛错。
2. 派生事件没有 request/channel，解析器无法区分结构化答复和缺身份的消息答复。
3. 只按 form 放行全部 answer，导致无 request、空 request、错误类型 request，以及 thread-message/issue-panel answer 缺 message 都被接受。
4. 错误的 task/attempt 身份绑定被新分支绕过。
5. 相同命令或事件产生重复人工介入；原有历史消息和有 message 的 answer 被误拒。

先在 dd 获取第 1 项真实 WS/SQLite/解析器红态。受控请求由实际引擎的 user-input.requested activity 建立，并读取持久 pending repository 确认 request，不使用孤立的回答哨兵。provider 禁用，不证明模型发问或回调送达。绿态保留同一信号；负例改变真实派生事件的字段，要求实际解析器拒绝，并让“全部 answer 放行”的 mutant 失败。

gap 可能失败：普通范围因记录器故障拒绝业务；来源丢失却猜成用户输入；丢失序号无覆盖；gap 派生人工介入；再次重启重复；启动 cwd/wrapper 错误或证据版本不明。最终冻结候选上通过真实 WS 注入普通输入，同时让 input、ingress 和去重 INSERT 失败；保留原库，复制库恢复后只补带序号/原因的 gap，再重启逐条比较。每次启动记录完整 HEAD、干净受控状态、argv、cwd、环境隔离与时间；不删除旧失败。
