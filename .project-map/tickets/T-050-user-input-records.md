---
id: T-050
title: 用户输入记录：类型、存放、与人工介入的关系、过渡期
type: decide
status: closed
blocked_by: []
claimed_by:
supersedes:
---

## Question

用户本人的输入怎么落成数据：记什么、分几类、存在哪里、和现有的人工介入事件什么关系、Herdr 期怎么办？

## Resolution

2026-10-09 grilling 确认。账本 [controller-split-user-input](../../.grilling/controller-split-user-input.md) 的 C3、C4、C9、C10、D1、D2、D10、D11、D21–D23、D25、D27、D32；设计见 [spec](../specs/controller-split-user-input-2026-10-09.md) 第 2、3 节。

- **范围与分离**：记录用户本人的输入——在 worker 会话里打的字、对 agent 提问的答复、权限批准或拒绝、界面操作、在主控对话里说的话。主控、agent、自动化发出的提示词是派发记录，永不进用户输入记录（C3）。
- **两层类型**：形态由渠道决定，客观记录：`message`、`answer`、`approval`/`denial`、`choice`、`action`。含义（建议、指令、纠正、偏好、补充信息、决定……）是推断，事后追加标注，可多标签，不改原记录。用户输入时不选类型。含义判断一律用意图识别，不写正则或关键词规则；v1 不产生含义标注，也不做批量标注（C9、C10）。
- **关联**：记录里存稳定的键——project、task、attempt、thread、turn、message、request、`reply_to`——后续结果（门禁事件、提交、验收）靠这些键关联，不存进输入记录。
- **存放**：工作台服务端新增追加式表 `user_inputs`，与门禁同库、同一写入入口，覆盖受管 attempt、attach 会话、普通会话、主控会话、界面操作；可导出 JSONL。现有 `human_intervention` 保留，改为"落进受管 attempt 的那条用户输入"的派生事件，带 `input_id`。fail-closed 只保留给受管 attempt 的输入；其余范围尽力记录，由事件日志重放补齐，补不齐写 gap 记录。
- **来源标记点**：非消息类输入在 WS RPC `dispatchCommand` 入口按枚举的命令类型记录，不改命令契约；界面自动派生的命令不算用户的明确决定。面板发出的答复在入口前登记 `message_id`，避免重复计数。
- **Herdr 期**：发给 worker 的每段文本走派发包装，加标记 `⟦主控 #序号⟧` 并记派发日志；worker 回收前和批次结束时把原生会话文件和主控对话文件的新增字节段复制进该批证据，副本不进 git，清单进 git；抽取成输入记录等有消费者时再做；来源只认标记与日志，不对内容做模式匹配。
- **使用**：v1 不跑自动分析。Enchanted 与改进分析的消费以后再说；消费端的前置条件是脱敏、权威的来源标记、记录不可变。
- 实现切片：[T-053](T-053-inbox-script-and-role-cards.md)、[T-054](T-054-dispatch-wrapper-and-session-copy.md)、[T-055](T-055-issue-report-tracer-bullet.md)、[T-056](T-056-user-input-coverage.md)。
