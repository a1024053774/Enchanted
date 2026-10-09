STATUS: PASS

TARGET: `/Users/luckye/Documents/Code/synara` 冻结候选 `90e38b667e224caca75318591fac43e676bf77e3`；本轮 parent `808156d63ef8e265a0e2c017fae7851e50a51019`；T-044 基线 `28e2f1b4ca6634d4faba9bd921a55a51640407e4`。PASS 仅适用于 T-044 与 `controller-decision-01.md` 明确批准的本地隔离范围。

EVIDENCE:
- 独立预期来自 T-044、任务书和主控决定：create 自动建立任务窗口，dispatch/attach 自动归属并保存角色、模型和指令；attachment 不产生交付 attempt、不获得门禁推进权限；受控 error 回收保留历史；同候选重跑 35 项及 membership 场景。
- `round2/final-window-02/create.jsonl` 与 `reclaim.jsonl` 保存生产 CLI HTTP 传输的完整步骤，全部退出 0。独立输入含随机任务身份、标题、角色和指令。原生 projection 读回 worker 的 xhigh/Fast 请求配置及 reviewer 的 high/非 Fast 配置、对应指令与项目归属。
- `round2-ui-active-02.png/json` 显示 worker、reviewer 自动出现；`round2-ui-ended-clear.png/json` 显示相同两会话均“已结束”、opacity 为 0.55，消息历史保留。membership 的两个 endedAt 与各自门禁回收事件时间一致；普通会话回收前后 task 完全相同；没有 submitted、verification_started 或 integrated 事件。
- `round2-permission-control-final.log` 使用同一合法交付：reviewer 经实际 `a2aSubmitTool` handler 得到 `stale_thread`，当前 worker 成功进入 submitted。其余受控 caller 门禁推进请求均拒绝且 task 不变。`round2-submit-counterexample-02.log` 另覆盖 create/dispatch/attach/claim 等拒绝条件。
- `round2-error-positive-final.log` 中 worker、reviewer 的 inactive error 均成功回收；`round2-error-negatives-final.log` 覆盖两角色共 22 个拒绝输入，包括 provider 存在、活跃 turn、待批准、待输入、待处理计划和身份不符；均在 stop/archive 前拒绝，task 与副作用列表保持不变。error run 返回 `run_external_unknown`，未调用 oracle、未 accepted、未 completed。
- `round2/prior-failures-raw.json` 保留两种原失败时间线。旧全量身份快照在 submit 前耗时越过既有期限；受控 8.2 秒 events 延迟使旧夹具失败，新身份读取路径通过。`fixture-change.diff` 仅改变 `current_attempt()` 的身份读取，未改期限或业务断言，完整快照仍留在业务检查点。
- `round2-orchestration-final` 为 18/18，`round2-delivery-recovery-final` 为 17/17；保存的 core、CLI、contract、HTTP、service、orchestration 源码均与冻结提交逐字一致。35 个夹具根目录与 62 份快照仍存在。验收包含独立分页 oracle、坏候选拒绝、Git 引用与副作用读回、替换身份和历史 attempt 保护。
- `round2-membership-final.jsonl` 与 `membership-boundaries-final.json` 覆盖两任务、角色归属、revision CAS、未知项目/会话、重复成员、跨项目身份、可信 origin 和 operation lock。attachment 的事件写入失败回滚、membership 写入失败后重放修复，以及旧 worker 记录移除再加入的结束标记恢复均在本候选通过。
- fmt、lint、typecheck 退出 0；lint 为 0 errors、868 warnings。核心测试 1/1、服务测试 11/11 通过。审查开始与结束的 project-map status 均为 Problems 0、Stale living docs 0；结束时 HEAD 仍为冻结候选。

FINDINGS:
- 未发现本次合同范围内已证实的 P1/P2/P3 违规。error 的原生观察改为显式读回对象后，受控回收检查由门禁核心负责；run 观察、等待收尾及 native submit 继续拒绝 error。attachment 的完成记录与完成事件同事务提交，membership 修复保持同一任务操作锁。

COUNTEREXAMPLE:
- 缺失实现的 `red-02`：create 后没有 membership，HTTP attach 被拒，未误判通过。
- parent 上 inactive error 正例被 `run_external_unknown` 拒绝；本候选通过。
- 删除 error 回收 guard 的 mutant：provider-present 输入虽最终返回 `stop_unconfirmed`，已先产生 stop 请求；测试通过副作用断言明确报红，未把“最终拒绝”当作保护成功。
- 旧夹具在受控慢观察下分别出现 thread KeyError 与 stale_attempt；新夹具保持原期限和验收断言通过。
- 权限同输入正例排除了“始终拒绝”实现；随机身份、标题、角色、模型参数、指令及历史读回排除了固定输出或仅伪造成功日志的实现。

LIMITATIONS:
- 截止点：2026-10-09 06:28:39 UTC。本次只读，未修改候选、数据库或分支，未运行重型套件，未操作正式工作台或调用模型。
- 编排与 error 拒绝矩阵采用受控 native 事实；权限验证采用受控 active native caller 帧。它们证明门禁逻辑与 handler 行为，未证明真实模型、签名 Gateway 认证链、实际供应商 tier 或生产运行。真实入口证据为隔离 dev 服务、CLI HTTP、原生 projection 与实际 web UI。
- 能力轴：编排/状态、异步事件、身份/作用域、交互界面、文件输入、Git/记录副作用适用；检索/记忆为 N/A；生产部署/canary 为 N/A。35 项通过不构成可靠性、吞吐或成本改善结论。
- `round2-submit-counterexample-final` 的缺失夹具 ENOENT 未作为通过证据；采用有效的 `-02` 和独立权限正例。UI 保留了请求取消与 favicon ORB 诊断；对应任务和两会话实际呈现已核对。
- 审查请求配置来源：主控 `collaboration.spawn_agent`，`agent_type=explorer`、`fork_turns=none`、`model=gpt-6.1-sol`、`reasoning_effort=xhigh`。该接口没有 CLI argv 或 service_tier 参数；只证明请求配置，实际供应商 tier 未验证。
- 本结论允许在上述明确范围内判定 T-044 PASS，不替代生产发布、正式工作台切换或真实模型闭环的验收。

RULE:
- 无新增重复失败类 finding。现有 error 反例应继续在回收前断言零 stop/archive 副作用；慢观察探针应继续保留固定 submit 期限与原业务断言。
