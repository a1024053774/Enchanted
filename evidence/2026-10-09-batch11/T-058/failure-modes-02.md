# T-058 实现前的失败方式

依据 ready_rev 1、spec 第 1/5 节、决定 01。首个红态已由父修订的真实 registry/工具定义取得；以下合同测试在实现前补充，预期来自规格。

- 签发：普通会话能力被改；worker 得到通用工具；reviewer/monitor 得到 submit；构思得到 operate；凭据随中途角色变化而变；首次 attach turn 在预设保存前签发。
- 收件箱：kind/字段错误；reply_to 悬空；编辑或删除原记录；ack 确认 ack；非原收件人确认；重复 ack 追加或重复唤醒；blocking 处置由非 user 关闭；HTTP/CLI/MCP 分叉。
- 唤醒：角色无会话、已结束或多活跃会话；目标正忙；用户输入交叠；保存后投递失败；重启未知回执被当成功或重送；把 agent 来源算用户输入。
- stop：没有 stop、不满/刚好两分钟、已经 executor ack、ref 不匹配、主控或非 gate-owned 会话、凭据无能力；中断被扩成关闭、回收、验收或集成。
- 集成：既有门禁锁、fence、CAS、attempt 被改变；T-057 的结束转交不出现在 executor 未确认列表；旧文件迁移/双写。

时钟与 SQL 不可变性需隔离验证，采用注入时钟和真实 SQLite/Git 的核心测试。传输、凭据签发、原生消息/turn 与中断另走实际应用服务及受控会话；不把纯逻辑测试外推成真实 provider 成功。
