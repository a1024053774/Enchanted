# T-074 rev 3 探针计划（2026-10-11 UTC）

起点 d732b8ebecaa42b8c4fa5843a43d1d292ae19b58。依据主控 #9、ready_rev 3、controller-decision-03 和 spec 第 6 节。REALITY GATE: INCOMPLETE。只做事实探针；不开始 T-075，不改产品代码，不补重试或自行修改派发设计。

1. 固定 CLI：Codex 0.162.1 / gpt-6-astra / xhigh / Fast 请求 / on-request；Claude 2.1.296 / claude-haiku-5-5 / manual，继续普通 CLI 登录与每会话设置的既有例外。
2. UserPromptSubmit 作为开始候选，Stop 作为结束候选；保留原始事件、收到时刻、标识，与原生记录核对。记录器只追加 stdin。Codex Stop 按文档输出空 JSON 对象作为协议响应，不含任何决定；不续接回合。
3. 空闲门禁只读本次原生会话的 UserPromptSubmit/Stop 事件，最近一个为 Stop 才开始一次完整 M3（paste + 300 ms + CR）。每段写入的时刻和当时事件都记录。不用本地 pending 占位修补可能的事件滞后。
4. PermissionRequest 继续用同一个只追加记录器作为诊断观察点，仅用于按决定 03 第 4 节确认何时发送 Esc，不作为空闲门禁或恢复条件。其结束事件要求已撤回。其余状态记录只作核对，不参与门禁。
5. 每家至少五次 idle_gated。Claude 另做两个 running 输入；原生消息是送达 oracle。两个竞态：开始事件已到后 B 应排队；A 的 CR 已写入、开始事件还没收到时尝试 B。两种时序分别使用独立窗格，以免一次取消留下的状态影响下一次。
6. 不把排队且未写入的 B 计入成功注入数。队列最多观察 60 秒，保存等待时长；不满足门禁不补 Enter。规则放行了应排队的 B、发生批准代答或缺少必要事件时，保存现场并停止后续执行。

预算预留：Codex 已 23，预计新输入最多 11，累计不超过 34/40；Claude 按已用 11 计，预计最多 14，累计不超过 25。辅助调用单列；启动异常不自动追加额度。所有标记写入只在自建夹具，批准操作只用明确 Esc 取消/拒绝。

CLI 文档已核对 UserPromptSubmit/Stop：Stop 是正常结束，Claude 文档明确它不在用户中断时触发；不把这条文档边界提前当成实测通过或忽略掉。若取消后队列不能恢复，如实记录。

人工介入：controller-review-rev2.md 已补记本 worker 被中断、换为 gpt-6-astra xhigh，以及收到无标记“继续”。本轮 RESULTS 引用该记录，不把整理证据阶段换模型改写成旧探针使用了新模型。

Tracer bullet 未开始；Deep modules 仅调整证据宿主；Ubiquitous language 沿用原生会话、窗格、派发记录。继续用 project-map、reality-first-engineering、evidence-first-testing 和 document-writing 的已读规则保存事实与失败。
