# T-066 验收计划（ready_rev 1）

基线：Synara fork `49cae984f22924de006e0f8358cb447eb881aaf6`，分支 a2a。开工时受控文件干净，未跟踪 `.grok/` 保留；a2a 开工时仅主控追加的 controller-poll.log 有修改，不纳入提交。

目标：凭据的 stop 能力负责放行，凭据中的角色、thread、turn 负责记录；目标 thread 独立保存。非目标：改变两分钟与 ack 条件、扩展中断到回收/归档/验收/集成、修改其他命令的角色投影、真实模型调用、正式工作台操作。

Tracer bullet：真实 MCP 凭据 → a2a_stop → 核心 SQLite 事件 → 既有任务窗口门禁事件读取。Deep modules：沿用唯一核心与已有事件查询，不增加平行接口。Ubiquitous language：调用地址、调用者 thread/turn、目标 thread 分开表达。

独立预期来自 ticket Acceptance 与 spec 第 5 节；固定字段名 `caller_thread`、`caller_turn` 是本票新增事件契约。旧 JSON 事件没有这两个字段，读取时显示“未记录”。

| 失败方式 | 预期处理与计划证据 |
| --- | --- |
| 执行主控同时持有 operate 与 stop | stop 成功，actor 为 executor；旧实现错误记成 ideation。真实 MCP 红绿同场景。 |
| 非主控角色被授予 stop | actor 为其实际角色地址，不按能力猜角色。真实 MCP 哨兵输入。 |
| 参数伪造角色、调用者 thread/turn | 忽略额外参数，只记录网关上下文。真实 MCP 反例。 |
| 调用者凭据已失效 | 网关拒绝，核心不追加停止事件；分别核对 inactive turn 和 revoked token。 |
| 同一目标被两个角色先后 stop | 独立追加两条，角色和调用者分别正确，目标相同；不覆盖旧条目。 |
| stop 与 ack 交叠 | 保留条目操作锁；ack 先完成则 stop 拒绝；stop 持锁期间 ack 拒绝忙，释放后 ack 可追加。真实核心的受控并发测试。 |
| 期限为 120000 毫秒或更早 | 不放行；120001 毫秒后放行。既有受控时钟用例与真实服务端自然等待。 |
| 旧库缺新列 | 事件详情是 JSON，本票不新增列；原事件原字节保存，读取原样返回，界面显示未记录。 |
| 目标身份不符、目标不属于 worker/reviewer/monitor | 沿用现有拒绝；运行既有 stop 用例。 |

审查只对冻结候选执行一次；reviewer 不读 RESULTS、Resolution、inbox 正文和旧审查。机械输出、独立 oracle 与重放命令可读。首轮夹具缺身份观察字段的 setup 失败保留为 red01，不作为产品红态。
