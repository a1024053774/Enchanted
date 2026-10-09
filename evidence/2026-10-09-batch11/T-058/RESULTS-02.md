# T-058 实现与修复交接

状态：**INCOMPLETE（已修复独立审查发现；最终候选未再独立审查，ticket 保持 open，待主控关闭）**。

依据主控 #13/#14、T-058 ready_rev 1、[决定 01](controller-decision-01.md) 和 spec 第 1、5 节。最终 fork 为 **`d9fc40a5f8b14d22ec7568c7ccef542572e79102`**，基线 `e9545960c50e4d0f8d687aef0da8073b2419adaa`；首个完整候选为 `9f29f66b3c8566d6c6c945dc43e12b207e197404`。分支 a2a，未 push。首轮 BLOCKED 报告、全部失败与旧候选证据保留。

## 主控需要决定

唯一一次 fresh-context 只读审查结论为 **FAIL**，目标是 9f29：[原始中文结论](acceptance-review-19.md)。发现 P1：executor 可以发送只允许 ideation→executor 的 assign；请求虽有合法凭据，方向却非法，仍追加并唤醒。

已在实际应用 MCP 入口重现并修复。最终核心在追加前检查 assign/revise/cancel、report/needs-decision 的固定方向及 issue 的上报者方向；stop、answer、disposition、ack 保持各自既有条件。所有十种 kind 的非法组合经 MCP、HTTP、CLI 验证在追加前拒绝，原记录与送达回执逐条不变。[真实红态](direction-red-20/mcp-assign.json)、[最终方向反例](direction-green-21/direction-oracle.json)、[完整命令](direction-green-21-command.json)、[单元红态](direction-unit-red-20.json)。

任务书明确要求：“若审查 FAIL：修复后不自行追审，交付 INCOMPLETE 由主控决定。”没有再开审查，旧 FAIL 没有上调。执行主控需决定自审这些修复证据，或另行授权复核；worker 未验收、集成或关闭整票。

## 实现与证据边界

Tracer bullet 经过 attach 的预设选择、持久 thread 绑定、真实凭据签发、实际 MCP 目录/调用、SQLite 收件箱及原生消息。Deep modules：门禁业务仍只有同一核心；预设保存沿用 a2a 数据模块，签发只复制固定能力；三种传输不另写门禁。Ubiquitous language 沿用 ideation/executor、worker/reviewer/monitor、task/attempt/thread、条目与 ack。

| 条件 | 结果与证据 |
| --- | --- |
| 原父修订红态 | PASS（合同未实现的红态）：旧 registry 不能选择精确 worker 能力；旧核心不能保存 inbox_send。inbox-contract-red-02、registry-parent-red-06 保留命令与退出码。父源码副本仅改导入位置供隔离重放，不改行为 |
| 收件箱 | 追加 UUID/schema/from/to/reply_to/refs/created_at/body；同一核心支持三个入口，十种 kind，无编辑/删除。SQL 对原条目与送达回执拒绝 UPDATE/DELETE。原收件人确认、ack 终结、重复确认均有覆盖。最终 gates 17/17，真实入口见 serial-final-26 |
| 门禁 MCP | create/claim/dispatch/attach/verify/integrate/reclaim/run/revoke/revise/status/events；同一核心和既有门禁锁/身份条件。十二入口的负面调用与 HTTP 对齐，实际 create/claim/revoke/revise 通过；原业务 task 不变，见 serial-final-26-extra26 |
| 精确工具集 | 实际 MCP tools/list 与手写预期相等：executor 17、ideation 8、worker 2、reviewer/monitor 各 1；反例拒绝 worker operate/inbox、ideation operate、reviewer submit、monitor inbox、executor stop，见 serial-final-26 |
| 凭据冻结 | 实际持久预设更改后，旧凭据仍是原工具集，重新签发采用新集；随后恢复预设。普通原生会话实际签发仍是父修订的六种能力。见 serial-final-26-presets15；纯 registry 亦有父反例 |
| 唤醒 | agent 来源、条目 id 与首行摘要、忙时 queue、正文保留；不写成用户输入。缺失、多目标、结束、明确失败与未知错误保留记录，未送达不报成功，不重送。最终无模型真实入口覆盖见 serial-final-26；实际新 Codex turn 只在 9f29 候选验证，见下一行 |
| 三个真实 Codex turn | 9f29 的接收者 READY 后，唤醒形成不同 turn 并逐字回复随机条目 id/摘要；第三个 worker turn 经超过两分钟的 stop 实际读回 interrupted，门禁 task 未变，随后两会话经 gate reclaim。real-11/real-oracle；这是旧候选的边界证据，未冒称 d9fc 的新模型复验 |
| 窄 stop | 只发 thread.turn.interrupt，不发 stop session/archive/reclaim/verify/integrate；owned worker/reviewer/monitor、refs、超过两分钟、无 executor ack 必须同时成立。时钟 0/119999/120000 拒绝、120001 放行；无记录、错目标、主控目标、已 ack、无能力反例覆盖 |
| T-057 结束转交 | 现有 forward/session-ended 原记录在 executor 未确认列表可见，未迁移、复制旧文件条目；最终真实服务的原生 archive 分支再次验证，serial-final-26/transport-oracle |
| 最终检查 | d9fc：fmt、lint、全 workspace typecheck、migrations:check、gates 17、server 87 通过；既有编排 18、交付 8 + 恢复 9 共 35 全过。final-21-* 保存完整命令/版本/干净受控状态。未运行整仓测试、桌面构建或外观判断 |
| 独立审查 | 9f29 FAIL；d9fc 未再审。整体 INCOMPLETE，不以绿测试替代最终独立结论 |

工具与能力的最终名字没有改动 spec 中 operate/read/inbox/stop：内部另用 a2a:submit、a2a:raise 供两个既有工具；operate 含 read，使状态/事件共用名称；inbox 含已存在的 a2a_disposition。worker 仍只看到 a2a_submit/a2a_raise；两种主控仍以 controller 保存归属，attach 的 preset 区分 ideation/executor。未增加自由编辑能力的界面。

## 六种失败方式

- 同一角色多个活跃归属：ambiguous_role_session，保存未送达回执，不自行挑选。
- 目标正忙：沿用原生 queue，实际服务已保存排队消息；9f29 的空闲接收者有真实新 turn。用户消息与唤醒交叠没有另做真实模型实验，未把已有 queue 语义当作这一组合的独立通过。
- 条目写入后唤醒失败：明确 Refusal 为 undelivered，其他外部错误为 unknown；中断后 pending 不能当成功，不自动重送。
- 重复确认：返回同一非空 ack id，不追加、不重复唤醒；ack 自身不能再确认。
- 能力在会话中途变化：已有凭据不变，重新签发才变化。最终串行真实凭据探针覆盖。
- 用户输入交叠：来源由服务端设置为 agent，用户输入记录器不记录唤醒消息；仅此来源区分已有真实依赖证据，未扩大为所有交叠场景通过。

## 范围、失败和清理

额外上游只改三处：AgentGateway.ts 的 import/注册、Services/AgentGatewaySessionRegistry.ts 的能力类型、Layers/AgentGatewaySessionRegistry.ts 的持久预设读取与签发。其它源码均在获批模块内。没有修改 provider adapter、sessionLease.ts、AgentGatewayCredentials.ts、computerToolPermission.ts、AGENTS/CONTEXT/地图或他人的 ticket；没有扩大免确认目录。

真实 Codex 固定 0.162.0，gpt-6.1-sol/xhigh，显式请求 Fast、禁用启动更新。auth home 在 /tmp（实际规范路径 /private/tmp），只复制 auth.json，只信任核对过的夹具根，仅 git add/commit 两条规则，无 hook。全部认证 home 已删除，原生日志/journal 留本机、不入归档；请求配置不证明供应商实际 tier。native provider journal 核对正好三个 turn；没有追加模型调用。

准备/检查失败均保留：最初 exactOptionalPropertyTypes 两处类型错误；一个测试错误假设列表首项；events 负例错误假设没有拒绝诊断；eval 导入缺少 root workspace alias；原生 SQLite 文件名/独占读锁诊断；错误假设 interrupt 一定有 turn.completed 日志。另一次把两个修改同一预设的探针并行，CLI 正确报目标角色缺失；修复后全串行补验。方向修复后旧负例仍使用非法 executor→monitor report，预期已纠正为合法方向、真实已归档目标，见 fixture-corrections-26。以上均未当作产品红态，未改写原失败。

只停止本票启动并经 PID、启动时间、完整 argv 与 ready 根目录核对的服务；所有实例最终停止，见 cleanup-*-16。没有操作正式工作台、用户 Herdr、用户配置或共享 dist，没有构建、替换目录或建立链接。未 push。他人的 .grok/、controller-poll.log 等保留。

Source/Git/门禁现场归档及索引保留；内嵌 Git repo 只进入 tar，不登记 gitlink。文本证据扫描未含夹具 bearer，认证/原生私有日志不入 Git。中文报告按 document-writing 做 UTF-8、实际文件与链接检查。最终版本、归档、project-map status 与提交范围检查另见 final-delivery-28.json。

源码 diff --check 通过；a2a 暂存交付的 diff --check 返回 2，原因是原始 lint/Vitest 日志的尾部空白和空行，完整输出见 staged-diff-check-29.json。原始日志没有为格式检查改写，该检查不记为通过。认证 overlay 另核对剩余 auth.json 为 0，见 auth-overlay-check-29.json。

重放使用 start-server-06.py 加全新 label，依次运行 transport-entry-07.py、live-presets-15.py、transport-extra-26.py；三个步骤必须串行。方向专项用 direction-entry-20.py；真实模型实验另用 real-entry-11.py，不能把它的旧通过结论转移到新候选。所有输出独占创建，不覆盖旧场景。依据 brief 的 Herdr 交付约定，本轮交两个仓库的提交和 DONE 行，不走门禁 submit，不需要 attempt/session/fence。
