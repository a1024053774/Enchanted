# T-074 rev 4 最小后台验证计划

起点 `8d130af83806c6f9e4fbda1174f9370ed29ef9c4`，依据主控 #10、ticket ready_rev 4、spec 第 6 节和执行主控决定 04。沿用 project-map、reality-first-engineering、evidence-first-testing、document-writing 的规则。

REALITY GATE: INCOMPLETE。目标是在真实 CLI 入口核实本地提交状态能否挡住竞态，以及 Stop / 人工 release 能否安全放行；非目标是产品代码、T-075、全局配置和新的派发规则。Tracer bullet 只限证据后台到原生消息的一条验证路径；Deep modules 不引入产品 API；Ubiquitous language 沿用忙、空闲、原生会话和用户输入。

observed / measured：rev 3 两家 A 的 CR 后、Start hook 前，旧 Stop 规则都放行 B；真实原始证据作为已知坏规则的红态，不重跑危险旧规则。unknown：最新 Stop 是否足以正常释放本地忙状态，Esc 后释放的消息能否成为新消息。

- 后台独占 PTY；协议响应、初始化键、提交和 Esc 均经过同一个写入函数，每条标来源。提交的 CR 立刻记忙，记录提交编号和时间；Start 仅保存。Stop 必须关联一个先前未结束的提交，收到时刻晚于最近忙时刻才改为空闲。没有可对应提交时立即记录异常并停止派发。
- 初始状态空闲，CLI 不通过 argv 自带首条 prompt；就绪消息也从后台提交，避免无提交对应的启动 Stop。Claude 信任提示需要用户模拟回车时同样记忙；该非对话输入没有 Stop，用单独登记的模拟 release 恢复，初始化动作不计入验收样本。
- M3 的传输段落串行化；注入只在空闲或显式 release 时放出。release 是探针模拟用户 action，日志记为用户输入；不发送空回车、不生成模型消息。只放队首一条，提交后重新忙。
- 每家顺序完成：就绪 1；gated_idle 3；gated_race 三组 A/B 共 6；gated_user_submit 两组共 4；gated_after_esc 两组共 4。共 18 个预计原生回合。Codex 累计预计 50/55，Claude 累计预计 40/40。出现未预期模型调用时重新核算，绝不越额或重试。
- 普通 A 只要求简短回复；用户场景的 A 经 user_sim 提交。批准 A 只请求一次夹具内无害 Python 写入，用结构化 PermissionRequest 确认后 Esc；队列保持至少 30 秒，确认原生取消/拒绝与标记未产生，然后模拟 release，核对 B 原文及 Stop。
- B 在忙时写入、被当批准、正常 Stop 后不放出、Stop 无法对应提交，任一发生即停止新增样本并上报。每项原始数据追加；已有试验只做拒绝、收集与清理。
- oracle 是登记前固定的原文与原生 JSONL/rollout；模型回复、终端文字和后台自报不作为送达证明。只在初始化时人工核对信任提示，不用读屏规则判断运行状态。

维持版本与认证：Codex 0.162.1 / gpt-6-astra / xhigh / Fast 请求 / on-request，隔离 CODEX_HOME 仅 auth.json 与夹具信任、git add/commit 两条规则；每会话 hook 延续决定 03 授权。Claude 2.1.296 / claude-haiku-5-5 / manual / 普通登录。沿用现有 node-pty 1.1.0，不安装依赖。结束归档、删自己创建的 Codex home，保留 Claude 夹具。按任务卡由执行主控核对原始记录，不另开独立审查。
