# T-056 恢复交接

状态：**BLOCKED，待主控决定；ticket 保持 open，待主控关闭。** 依据 `ready_rev: 2`。本轮已实现并保存部分候选，发现新的界面绕过入口后按 brief 停止产品编辑，不宣称整票 PASS，未向业务门禁 submit。

fork 父修订：`d479dab2a1608c3219b7a4e1c07e9056bfb63a9e`。审查候选：`c7aaaa433a064aff032d3d5d511cf496507ecd83`。最新代码候选：`2ad957d359281215ad3bf21fe47595ad6ad39c80`，分支 a2a，未 push。当前候选包含审查后的故障范围修复，没有再次独立审查。

## 需要主控决定

[新入口待决说明](needs-decision-25.md) 和 [源码快照](ui-path-scope-25.json)：Unblock 按钮调用 `reconcileProviderDelivery`，绕过已批准的 `dispatchCommand` 与 `prepareQuitResume`。需要核对该用户操作的本票范围、额外挂接授权，以及一次按钮操作和循环 blocker 请求之间的记录单位。未擅自缩小验收或给第三个 RPC 加挂接。

另外保留两处尚未补齐的工作目录切换派生停止命令（BranchToolbar），以及普通 thread 的 prepareQuitResume 项目键核对项。新的绕过路径触发停止时，它们仍未完成。blocking 问题：`20261009T190952Z-worker:s11-t056-issue-001`；交执行主控的 needs-decision：`20261009T190500Z-worker:s11-t056-needs-decision-001`。

显式 submit 的身份与传输也未提供；当前工具没有 a2a_submit，brief 禁止读取正式工作台 endpoint。先前上报见 [submit 传输核对](submit-transport-11.md)，问题 `20261009T175417Z-worker:s11-t056-issue-001`，needs-decision `20261009T180305Z-worker:s11-t056-needs-decision-001`。代码提交、候选报告和门禁 submit 收据分别报告，不伪造 attempt/session/fence。

## 实现与证据

Tracer bullet 贯通真实 WS/HTTP、域事件、SQLite 与人工介入，再扩展覆盖矩阵。Deep modules 的记录与事务留在门禁核心；Ubiquitous language 使用用户输入、人工介入、task/attempt/thread。没有内容含义的正则或关键词分类，没有含义标注。

| 检查 | 状态与证据 |
| --- | --- |
| 实际父修订合同红态 | PASS（红态证据）：d479dab2a 上 worker 消息 1 条、其余 9 项 0 条，原断言退出 1。[原命令](red-matrix-03.command.json)、[矩阵](red-matrix-03/summary.json)。这是新功能的预期红态，不称父修订已有缺陷 |
| 最新候选 10 项矩阵 | PASS（列出的矩阵）：实际服务、WS、门禁、事件流与 SQLite，10 项各 1 条；不扩大成全部 UI 操作通过。[命令](final-24.command.json)、[矩阵](final-24/summary.json) |
| 来源、目标字段与反例 | PASS（c7 候选）：agent/automation/a2a 来源排除；ui-derived 记录不派生人工介入；相同命令去重；未知非观测命令不记输入；prepareQuitResume 挂接；受管动作带 input_id。[边界](boundaries-14/summary.json)。后续故障范围修复没有更改该来源筛选与命令枚举；未借此覆盖新增 UI 缺口 |
| 非受管恢复与 gap | PASS（已测失败路径）：输入表写失败但 ingress 成功时恢复原输入；ingress 也失败且重启后来源不可核对时，写覆盖 52–54 的 gap，不猜用户决定。[正常恢复](boundaries-14/after-restart-inputs.json)、[旧失败](source-loss-05/loss-summary.json)、[gap 绿态](source-loss-14/loss-oracle.json)、[跨范围恢复](scope-recovery-20/loss-oracle.json) |
| managed fail-closed | PASS（已测输入写失败）：受管输入失败拒绝 RPC，后续门禁变更被 user_input_observer_failed 拒绝。[收据](boundaries-14/managed-refusal.json) |
| 故障归因 P1 修复 | PASS（修复入口红绿）：原候选只在非受管写失败时，也会因受管元数据事件错误 failed；修复按实际输入归因，补录失败不推进游标。[红态](scope-18.command.json)、[绿态](scope-22.command.json)、[恢复保护](scope-recovery-20.command.json) |
| 进度表故障的同类反例 | PASS（修复入口红绿）：无受管输入写失败时，进度表故障不触发 managed fail-closed，且带故障的副本冷启动可用。[红态](checkpoint-21.command.json)、[绿态/冷启动](checkpoint-23/cold-start-oracle.json) |
| 迁移与历史保留 | PASS（c7，迁移代码未在后续修复改动）：只在旧格式夹具副本验证，历史 data/ledger 逐条相同；事务中断回滚、重跑幂等、nullable 目标支持；父修订缺 user_input_events 被反事实拒绝。[绿态](migration-frozen-14.json)、[父修订反例](migration-parent-11.command.json) |
| 重复、大负载与重放 | PASS（c7，记录序列化未在后续修复改动）：24,582 字符文本逐字保持，附件只存 id/type/message 引用，相同命令一次，重启前后输入与 gap 逐条相同。[额外场景](extras-16/summary.json) |
| 原生 Codex 异步提问/答复 | PASS（固定 c7 的真实边界）：Codex 0.162.0 产生原生 questions，答复为恰一条 answer，指向原问题，原生会话实际收到哨兵；后续只改故障策略，未再调用模型，不将旧审查结论移给新候选。[问题](native-frozen-15/question-observation.json)、[输入 oracle](native-frozen-15/answer-oracle.json)、[原生接收](native-frozen-15/native-ack.json) |
| membership | PASS：既有独立场景仍通过，覆盖两个任务、角色、CAS、未知身份、重复成员和 trusted origin。[命令](membership-frozen-16.command.json) |
| 最新格式、lint、类型与相关测试 | PASS：2ad 上 fmt、lint、全 workspace typecheck、migrations:check、gates 10、server 77、web 4 均退出 0。[最终命令](final-typecheck-24.command.json)，其他同名 final-*-24.command.json |
| 既有交付 8、恢复 9、编排 18 | PASS（最新 2ad）：原断言与期限不变，18/18 + 17/17。[编排](orchestration-final-25/command.json)、[交付/恢复](delivery-recovery-final-26/command.json) |
| 独立审查 | FAIL（固定 c7/P1），原结论保留；修复后的 2ad 没有再次独立审查。[审查](acceptance-review-18.md) |
| 整票、全部 UI 范围与门禁交付 | BLOCKED：新入口及已知缺口待决定；未 submit、未验收/集成/关闭，不把自然语言完成当作门禁事实 |

[behavioral-acceptance-review](</Users/luckye/.agents/skills/behavioral-acceptance-review/SKILL.md>) 明文要求 “Review one frozen candidate snapshot in a fresh, read-only context.” brief 第 14 行又限定一次独立审查。该次已用在 c7；没有自行再开一次。若主控需要新候选的 fresh-context 审查，需要明确追加授权。这里的最终独立验收缺项为 INCOMPLETE，整体因新范围问题为 BLOCKED。

## 失败方式与保留边界

- 事件乱序：消费者按真实引擎的提交序号重放；客户端时间不是排序依据。async answered 事件关联其后消息，数据按稳定 message/event/command 键去重。未声称可正确处理任意外部伪造的乱序事件。
- 重复事件与实时/重放交叠：先订阅、再取 high-water；SQLite 事务与稳定来源键去重。extras-16 的实际重启逐条比较保持记录和 gap 不变。
- 未知命令：v1 只记录枚举的渠道形态，不按正文猜含义。未观测的命令不自动归为用户 action。
- 超大负载：正常合同上限沿用上游，文本保持；附件仅存引用，未测试上传界面。
- 迁移中断后重跑：真实 SQLite DDL 后、COMMIT 前注入异常，事务回滚后副本逐条保持；重跑两次相同。不是 OS 崩溃时序试验。
- 旧库缺少新结构：构造器建立新 ledger/ingress/checkpoint，迁移旧 NOT NULL/UNIQUE 限制与旧去重表；旧 data 和历史事件不改写。

所有红态、异常、旧报告、源码和命令保留。首轮类型错误保存在 typecheck-03.log；客户端来源反例误用 WS（codec 会剥离 dispatchOrigin）保存在 boundaries-08；native-10 的 Option 包装读取错误只停止轮询 helper，原生问题保留并由 native-11 完成，未补称第一次 helper 成功；fmt 初轮发现父候选 README 格式问题；收件箱的跨仓 file 引用被拒，见 inbox-ref-setup-failure-25.txt。这些准备失败不计为功能红态。

## 上游文件和共享名字

实际上游改动仅四个文件：contracts 的 orchestration.ts 命令 schema，加可选 origin；RunningChatsQuitCoordinator.tsx 的退出中断标记；useTemporaryThreadLifecycle.ts 的清理停止标记；wsRpc.ts 的 import 和两个获批入口挂接。新发现的 BranchToolbar 还没有改动，第三个 RPC 没有加挂接。

其他实现位于获批目录。共享改名为 A2AUserInputObserver、user_input_observer、user_input_events、recordUserInput、installUserInputRecording、userInputObserverView 等。human_intervention 与界面人工介入概念保留。issues.test.ts 只改一处方法名，断言不改；问题处置、发送与面板行为未重写。user_inputs 新记录补齐可空目标键；README 与记录器界面文案同步。前端样式不变，未使用布局或外观自评作验收。

## 隔离、版本与收尾

真实模型共 4 个完成 turn：初始问答 2 个、固定 c7 问答 2 个。只复制 auth.json；两份 CODEX_HOME 均在 /tmp，仅信任已核对夹具根，仅 git add/commit 两条规则，无 hook，显式 Fast 请求、关闭启动更新。供应商实际 tier 未证明。两个 home 已整目录删除，原始 rollout 本机私有且 Git 忽略；[第一次清理](cleanup-auth-12.json)、[冻结阶段清理](cleanup-auth-17.json)。实现 worker 的实际启动 argv/实时 Herdr 身份未由任务书提供，未冒称验证；[版本与 skill 快照](versions-18.json)。

只停止创建并核对 PID、启动时间和命令的服务；正式工作台、Herdr、用户配置、dist 与依赖目录未操作，未 push。保留 .grok 和 controller-poll.log 的他人工作。Git/worktree 与门禁完整现场在 retained-git-gates-17.tar.gz，后续故障现场追加归档为 retained-git-gates-26.tar.gz，最新 35 项现场为 retained-final-suites-27.tar.gz；原生服务库、profile 与 control 留原目录本机，不发布认证材料。夹具没有登记 gitlink。

没有运行完整全仓测试、Electron 构建或 GUI 外观检查；这些受 brief 的执行范围约束，不写为通过。project-map status 的开始与结束均保存为 0 problems、0 stale。a2a 只提交本票新增证据、自己的收件箱条目及 T-056 Resolution；所有验收框和 open 状态留给主控。

源码 fork 的 diff --check 为 PASS。a2a 暂存证据的 diff --check 退出 2，原始 lint/Vitest 输出含尾部空白与末尾空行；完整诊断见 staged-check-27.json。原始运行输出保留，不为格式检查改写，证据空白检查不写为 PASS。
