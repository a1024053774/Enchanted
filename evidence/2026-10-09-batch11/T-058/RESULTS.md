# T-058 首轮接入检查

状态：**BLOCKED（等待两处额外上游 registry 接入批准；ticket 保持 open，待主控关闭）**。

依据主控 #13、[brief](../brief-T-058.md)、T-058 ready_rev 1。fork 基线 `e9545960c50e4d0f8d687aef0da8073b2419adaa`，本轮没有 fork 改动或 fork 提交，未 push。

必须先批准的最小接入见 [needs-decision-01.md](needs-decision-01.md)：`apps/server/src/agentGateway/Services/AgentGatewaySessionRegistry.ts` 与 `Layers/AgentGatewaySessionRegistry.ts`。前者声明 a2a 能力和 thread 预设绑定接口；后者签发时冻结精确能力集合。预设定义、持久角色和调用留在获批 a2a/contracts 模块。brief 明确要求这类额外上游接入“先停下说明位置与最小接入，主控批准后再改”。

已按 worker 协议追加 blocking 问题 `20261009T205838Z-worker:s11-t058-issue-001`；这是任务上报，不是迁移、测试或改写真实收件箱旧条目。现有 registry 总是授予六种通用能力，无法仅靠 a2a 工具注册实现 spec 第 1 节的精确工具集。本轮未越过这一批准点。

| 检查 | 结果及证据 |
| --- | --- |
| 项目状态 | 开工 status：Problems 0、Stale living docs 0；最终原始输出另存 status-before-delivery-01.txt |
| 前置结果与规格 | 已读指定 T-055 RESULTS-03、T-056 RESULTS-05、T-057 RESULTS-02，以及 spec 第 1、5 节。旧报告的独立审查、OS 通知及未确认列表缺项没有上调；T-057 executor 转交未确认列表仍待本票实现 |
| 新合同红态探针 | [capability-preflight-01.json](capability-preflight-01.json)：实际 registry 签发、实际三个 a2a 工具定义和实际 capability 筛选器；手写 worker 预期为 a2a_raise/a2a_submit，观察多出 a2a_disposition，子进程退出 1。无 handler 调用或模型替身 |
| 红态边界 | 这是父修订尚未提供新角色合同的证据，只检查既有 a2a 工具集合；没有执行完整 MCP tools/list，不能代替最终角色工具集、身份反例或真实 turn 验收 |
| 产品实现与验收 | 未改产品代码；收件箱三入口、全套 MCP、能力预设、真实唤醒、stop 反例、T-057 转交可见性均未实现/未运行 |
| 35 项、静态检查、独立审查 | 未运行。没有冻结产品候选，未消耗任务书允许的一次 fresh-context 审查；只对本轮文档和证据做 UTF-8、链接、差异检查 |
| 服务、模型与隔离 | 没有启动服务或 provider，没有新模型 turn、认证副本、正式工作台、Herdr、用户配置或 dist 操作；Bun 仅经 fork 的 a2a/scripts/bun，使用独立外置盘 slot s11-t058-preflight |

重放命令保存在 [run-preflight-01.py](run-preflight-01.py) 与结果的 argv/cwd/env_override 字段。结果输出采用独占创建，复跑须换新编号，原红态不能覆盖。helper 返回 0 仅说明保存证据成功；真实 probe 返回 1。证据不含 bearer/token。

准备时有几次只读查询使用了错误 cwd/文件名而失败，随后按实际路径读取；它们不是业务红态，不用于通过结论。既存 `.grok/` 和他人的 controller-poll.log 保留，仅提交本票证据、自己的上报条目和本票 Resolution。

本轮停止条件是明确的源码接入批准，不是测试通过或完成交付。批准两处接入后继续同一 ticket，不关闭、不修改验收条件、不改地图、术语或他人 ticket。
