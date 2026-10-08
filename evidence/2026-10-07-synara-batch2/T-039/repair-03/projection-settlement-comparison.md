# 投影落定机制对照（2026-10-08）

目标：在原门禁的thread/turn/worktree判断前取得明确的已处理前缀，原自动run必须completed；不改GateRuntime合同、拒绝规则或上游文件。授权为controller-decision-02。

| 现有机制（observed） | 能证明什么 | 不能证明什么 |
| --- | --- | --- |
| `OrchestrationEngine.getEventHighWaterSequence` | 已提交domain journal的序号H | 不包含尚未被ingestion转换的native事件，也不是等待投影的API |
| `readEventsThrough`、ProviderCommandReactor:2807 | 读取截至H的持久事件，核对已提交的取消等事实 | 读取完日志不等于某个consumer或投影已处理到H |
| CheckpointReactor:2628、2849 | runtime先、domain后的两个fence；包含native快照之前的已提交cut | 单独采样两个head不代表处理已完成 |
| CheckpointReactor:2930–2967 drain | 自己的worker、ACK cursor和最终heads全部追上才返回 | 这是checkpoint consumer的落定，不是通用投影屏障；不应为门禁做Git checkpoint drain |
| `ProviderRuntimeIngestionService.drain`，3814–3826 | 捕获runtime high-water R，消费有限前缀并验证ingestion ACK cursor>=R；失败抛出 | 不保证未来事件，不能当原子全局快照；等待须受已有期限约束 |
| `ProjectionSnapshotQuery.getSnapshotSequence`，840–879、2957 | 必需snapshot projectors的最小已处理序号P；缺cursor时抛错 | 是证明/检查接口，不自己等待；必须核对P>=捕获的H |
| `ProviderCommandReactor.drain`，8994起 | consumer ACK追上domain head后返回；包括stop意图的实际处理 | 不是单个thread专用，持续新事件可延长等待；须受已有回收期限约束 |
| engine.dispatch的hot transaction | domain事件、receipt与hot投影在同一transaction提交后发布 | `thread.session.stop`只是stop-requested；实际stopped由ProviderCommandReactor后续写session-set |

选择（inferred，由上述实现支撑）：先采provider快照；复用runtime ingestion的有限前缀drain；再捕获domain H，验证snapshot P>=H，最后读shell再分类。停止命令后复用provider command drain，再走同一投影前缀检查；archive后也核对已处理序号。这样消除先读旧shell再读新provider的拼接，不添加“等等再试”的循环。

期限：复用原run phase记录的submit期限和回收60秒窗口，等待超时返回原错误码；不更改门禁接口。没有active run的原生操作也须有界。探针将验证deadline、未落定前不读shell/推进业务，以及错误与真实turn更换仍拒绝。若现有服务图无法提供这些机制或期限需要合同变更，停止交主控。

已知限制：这是明确序号的有限前缀屏障，不是阻止未来provider事件的全局锁。真实边界仍需全新模型闭环证明；受控替身不得替代它。
