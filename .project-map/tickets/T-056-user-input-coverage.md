---
id: T-056
title: 用户输入记录覆盖全部范围，观察器改名
type: build
status: closed
blocked_by: [T-055]
claimed_by: s11-t056
supersedes:
ready: yes
ready_by: ideation
ready_rev: 2
---

## What to build

让用户在任何会话、任何渠道的输入都被记成数据，并和主控、agent、自动化发出的提示词分开。范围：受管 worker、attach 会话（reviewer/monitor）、普通会话、带角色的主控会话里打的字；对 Codex 异步提问和结构化提问的答复；权限批准与拒绝；界面的停止与中断。每条记录带形态、渠道、目标键（project、task、attempt、thread、turn、message、request）和来源引用，`certainty` 为 `observed`。

现有 `human_intervention` 保留，改为受管 attempt 上"落进该 attempt 的用户输入"的派生事件，带 `input_id`。观察器及相关名字统一改为 `user_input_*`。设计见 [spec](../specs/controller-split-user-input-2026-10-09.md) 第 3 节。

## Acceptance

- [x] 红态在先：在本票的父修订上，下面覆盖矩阵里除"受管 worker 的消息"外的各项都没有用户输入记录，用例失败；保存输出与重放命令。
- [x] 覆盖矩阵正例（真实服务，隔离数据目录，每项至少一条）：受管 worker 的消息（既有行为不变）；attach 会话的消息；普通非受管 thread 的消息；带角色的主控会话的消息；Codex 异步提问的答复；结构化提问的答复（`user-input.respond`）；权限批准与拒绝（`approval.respond`）；界面的停止、中断。每条记录含形态、渠道、目标键、来源引用，`certainty` 为 `observed`。
- [x] 反例：agent、自动化、门禁自己发的消息与命令（dispatch/attach 提示词、automation、`a2a:` 前缀的命令）不产生用户输入；界面自动派生的命令（退出应用时的批量中断、临时线程清理）不被记成用户的明确决定（按 spec 第 3 节的处理）。
- [x] 观测点（用户 2026-10-09 选 A 修订）：非消息类输入在 WS RPC `dispatchCommand` 入口按枚举的命令类型记录；给相关命令加可选 `origin` 字段，只由界面自动派生点（退出时批量中断、临时线程清理等）设置，缺省为用户操作，自动派生的标 `ui-derived`、不算用户的明确决定；退出恢复路径 `prepareQuitResume` 入口也挂一次记录。允许改的上游文件仅限：contracts 的命令 schema、需设置 `origin` 的 web 调用点、`wsRpc.ts`；列入上游文件改动清单，不改其他命令语义。
- [x] fail-closed 范围：受管 attempt 的输入记录失败时，所有变更命令照旧被拒（沿用既有行为与测试，只改名字）；其余范围记录失败不阻断业务，恢复后由事件日志重放补齐，补不齐的写 gap 记录；重放不重复。
- [x] `human_intervention` 保留，改为受管 attempt 上的派生事件，带 `input_id`；界面标记与 AGENTS.md"受管 worker 里直接输入记为人工介入"的规则不变。
- [x] 改名：`human_input_observer`、`human_inputs`、`recordHumanInput` 等统一改为 `user_input_*` 系列。正式工作台的数据目录里已有旧名的表和历史事件，所以要有幂等的迁移，保留全部历史记录；迁移在一份旧格式夹具库的副本上验证，不碰正式数据目录。既有套件除名字外断言不变并全部通过；README 与界面文案同步。
- [x] 不使用正则或关键词规则判断内容含义；v1 不产生含义标注。
- [x] 既有套件（交付 8、恢复 9、编排 18、membership、T-044 的 35 项）、typecheck、lint 通过；对上游文件的改动列清单。

## 说明

- 开工前对照 [T-055](T-055-issue-report-tracer-bullet.md) 的实际结果重读 spec；发现 spec 与已建成的行为不符，停下发 `needs-decision`，不绕开。
- 失败方式清单（处理方式写进 RESULTS）：事件乱序；重复事件；重放与实时交叠；未知命令类型；超大负载（附件只存引用）；迁移中断后重跑；旧库缺少新列。
- 与 [T-057](T-057-issue-panel-completion.md)、[T-058](T-058-server-inbox-capabilities-wake.md) 会改同一批文件，同一文件同一时间只能有一个写入者，由执行主控串行安排。
- 授权来源：`ready_by: ideation`，`ready_rev: 1`。

## Resolution

2026-10-09，s11-t056：**BLOCKED**，待主控决定，保持 open，待主控关闭。开工核对发现 ticket 指定的 WS RPC `dispatchCommand` 入口在 fork 的 `apps/server/src/wsRpc.ts:1322`，超出 brief 允许目录；按 brief 在产品编辑前停止。请求只额外批准该文件的 import 与入口调用，记录实现仍留在 a2a 模块，不改命令契约。

依据 `ready_rev: 1`；fork 父修订 `2330534b2cf906b9d8f0a0b643adb370683d7fe0`。证据与重放命令见 [RESULTS](../../evidence/2026-10-09-batch11/T-056/RESULTS.md)、[待决说明](../../evidence/2026-10-09-batch11/T-056/needs-decision-01.md)、[只读输出](../../evidence/2026-10-09-batch11/T-056/preflight-01.json)。收件箱 blocking 问题为 `20261009T130122Z-worker:s11-t056-issue-001`，发给执行主控的 needs-decision 为 `20261009T130122Z-worker:s11-t056-needs-decision-001`。未实现、未运行业务验收或独立审查、未 submit；Acceptance 均未勾选。

执行主控决定 01 已解决上述接入范围阻塞。2026-10-09 第二轮：**BLOCKED**，待主控决定，保持 open，待主控关闭。真实隔离服务的父修订红态已取得：worker 消息 1 条，其余 9 项无用户输入记录，全部 RPC 接受且有域事件；provider 禁用，未调用模型，不主张原生提问交互验收。窄探针确认用户操作与自动派生的停止/中断在现有合同中不可区分；另发现 `prepareQuitResume` 绕过 `dispatchCommand` handler。按 ticket、spec 第 3 节及决定 01 再次在产品编辑前停止，未改命令契约。

证据见 [第二轮待决说明](../../evidence/2026-10-09-batch11/T-056/needs-decision-02.md)、[红态矩阵](../../evidence/2026-10-09-batch11/T-056/red-matrix-02/summary.json)、[来源窄探针](../../evidence/2026-10-09-batch11/T-056/origin-probe-02.json)。新 blocking 问题为 `20261009T131628Z-worker:s11-t056-issue-001`，needs-decision 为 `20261009T131629Z-worker:s11-t056-needs-decision-001`。产品代码无改动，fork 父修订不变；仅核对并停止本次隔离服务，完整现场已归档。未 submit，迁移/绿态/既有套件/独立审查未运行。


2026-10-09，恢复轮（ready_rev 2）：**BLOCKED，待主控决定，保持 open，待主控关闭。** fork 父修订 `d479dab2a1608c3219b7a4e1c07e9056bfb63a9e`，已保存实现候选 `2ad957d359281215ad3bf21fe47595ad6ad39c80`。实际父修订矩阵先红，已实现矩阵、来源与去重、迁移、原生 Codex 问答、恢复与 gap；唯一一次独立审查在 `c7aaaa433` 上 FAIL/P1，故障归因已在真实入口先红后绿修复，修复后没有再次独立审查，不继承旧候选判定。

新发现 Unblock 直接走 `reconcileProviderDelivery`，绕过两个获批入口；按 brief 停下，未自行增加第三个挂接或减少范围。BranchToolbar 的两处派生停止与 prepareQuitResume 普通项目键核对仍列为缺口。blocking 问题 `20261009T190952Z-worker:s11-t056-issue-001`，执行主控 needs-decision `20261009T190500Z-worker:s11-t056-needs-decision-001`。submit 身份/传输此前已上报，未提供；未向业务门禁 submit、未验收或集成，Acceptance 未勾选。详见 [恢复交接](../../evidence/2026-10-09-batch11/T-056/RESULTS-02.md)、[新范围待决](../../evidence/2026-10-09-batch11/T-056/needs-decision-25.md)、[唯一审查](../../evidence/2026-10-09-batch11/T-056/acceptance-review-18.md)。旧失败现场与报告保留，正式数据与工作台未动，未 push。

2026-10-09，执行主控决定 02 后：**INCOMPLETE（最终候选独立审查缺项），保持 open，待主控关闭。** 决定已解决此前范围与交付阻塞。实现 Unblock 每请求一条输入、BranchToolbar 派生停止标记、普通退出恢复项目键；追加审查在 cb9 返回 FAIL/P1（编辑重发与检查点回退漏枚举）。真实 WS 红绿修正后冻结 fork `ddcff9a643e15dd68c18186782e688e492bb44a8`，补目标 message、人工介入展示及来源丢失 gap。最终 10+5+2 项矩阵、故障边界、原生权威事件重放、membership、既有 18+17 项、fmt/lint/typecheck/migrations 与相关测试均通过；本轮没有新增 provider turn。旧 FAIL 保留，不继承为新候选 PASS；第三次审查未自行启动，已交主控 needs-decision `20261009T201420Z-worker:s11-t056-needs-decision-001`。详见 [本轮报告](../../evidence/2026-10-09-batch11/T-056/RESULTS-03.md)、[追加审查](../../evidence/2026-10-09-batch11/T-056/acceptance-review-35.md)、[待决](../../evidence/2026-10-09-batch11/T-056/needs-decision-44.md)。按决定 02 用代码及证据提交、报告、DONE 行交付，不要求 Herdr 期门禁 submit；未验收、集成或关闭，Acceptance 未改。只停自建服务并归档现场，未动正式数据、Herdr、用户配置或 dist，未 push。

2026-10-09，决定 03 审查轮：**INCOMPLETE，保持 open，待主控关闭。** 已在冻结 fork `ddcff9a643e15dd68c18186782e688e492bb44a8` 做授权的一次 fresh-context 整票只读审查，原始结论 INCOMPLETE：当前 gap 分支证据未获确认，补充探针因 Bun 路径错误未启动。候选没有改动，没有补跑或第四次审查；退出码未知与原始失败现场均保留。另将受管结构化答复的人工介入显示静态风险单独上报，未冒称为独立 FAIL。triage 问题 `20261009T203240Z-worker:s11-t056-issue-001`、`20261009T203240Z-worker:s11-t056-issue-002`；最小补验/修正选项交执行主控。见 [审查轮交付](../../evidence/2026-10-09-batch11/T-056/RESULTS-04.md)、[原始审查](../../evidence/2026-10-09-batch11/T-056/acceptance-review-54.md)。Acceptance 未改，未验收/集成/关闭；按 Herdr 方式提交报告与证据，产品 provider turn 为 0，未动正式数据、Herdr、用户配置、dist 或他人工作，未 push。

2026-10-09，决定 04 工程轮：**PASS（本轮获批修正与检查），保持 open，待执行主控自审与关闭。** 最终 fork `e9545960c50e4d0f8d687aef0da8073b2419adaa`；dd 上真实受管 WS 答复、有持久 pending request、SQLite 派生事件交实际 web 解析器先红，修正后绿。派生事件保留 request_id/channel；只接受无 message、有有效 request 的 WS answer，消息答复仍需 message，全部 answer 放行的 mutant 被拒。冻结最终候选同时失去普通 input/ingress INSERT 时业务继续，恢复只补一条覆盖 52–54 的 gap，不派生人工介入，再次重启逐条相同；启动均绑定完整修订、正确 wrapper/cwd 和隔离目录。最终 fmt/lint/typecheck/migrations、gates 10、server 77、web 5、编排 18 与交付/恢复 17 均通过。类型检查首轮和 gap helper 清理失败保留，不冒称首轮成功。按决定 04 未启动独立审查，交执行主控自审，Acceptance 未改，未验收/集成/关闭；产品 provider turn 为 0，未动正式数据、Herdr、用户配置、dist 或他人工作，未 push。详见 [本轮交付](../../evidence/2026-10-09-batch11/T-056/RESULTS-05.md)、[候选源码](../../evidence/2026-10-09-batch11/T-056/final-source-71/revision.json)。

**执行主控关闭（2026-10-09）：PASS，依据 ready_rev 2 与执行主控决定 01～04。** fork 最终候选 `e9545960c`（分支 `a2a`，父修订 `d479dab2a`），证据至 `93934d2`，见 [RESULTS-03](../../evidence/2026-10-09-batch11/T-056/RESULTS-03.md)、[RESULTS-05](../../evidence/2026-10-09-batch11/T-056/RESULTS-05.md)。覆盖矩阵 10 项 + 决定 02 追加 5 项（Unblock 每请求一条、BranchToolbar ui-derived、退出恢复项目键）+ 重试 2 项，均先红后绿；迁移在旧格式夹具副本验证；既有 35 项、membership、fmt/lint/typecheck、相关测试通过。三次独立审查：c7 FAIL/P1、cb9 FAIL/P1，均已修复并有红绿；dd INCOMPLETE（gap 证据不足、受管结构化答复显示风险），决定 04 补 gap 绿态，并修复受管结构化答复的人工介入显示（真实入口红态→绿态，全放行 mutant 被拒）。决定 04 的四文件差异（core 派生事件补 request_id/channel，web 解析器只对 ws-rpc、无 message、有 request 的 answer 放宽）由执行主控自审通过；改名只余迁移中的旧表名。上游改动清单：contracts 命令 schema（origin）、web 自动派生调用点、`wsRpc.ts` 三处入口。Unblock 的记录单位为执行主控默认，blocking 问题 `20261009T190952Z-worker:s11-t056-issue-001` 仍待用户关闭；用户若改记录单位另行修订。
