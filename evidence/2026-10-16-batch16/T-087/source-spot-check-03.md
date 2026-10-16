# T-087 第三轮独立来源抽查

结论：**PASS（限定于本轮静态来源抽查与文本再生成）**。前两轮 P2-01、P2-02、P3-01、P2-03 已按当前来源补正；未确认新的阻断问题。检查串顺序、所展示拒收码、抽查连接及逐分支持久化说明与来源相符。这个结论不代表产品运行验收、T-081/T-082 重新通过，也不关闭 T-087。

- 日期：2026-10-16。
- 仓库：`/Users/luckye/Documents/Code/a2a-wt-t087`；分支 `exec/t087`。
- 冻结候选：`70875e71cda1362eb7d3115a93fc6a0a1e11afa7`，开始及收尾以 `git rev-parse HEAD` 核对一致；开始工作区干净。
- 对象：`findings/ticket-gates-graph-2026-10-16.zh-CN.md` 与 `findings/generate_t087_graph.py`。下文“图第 N 行”指本冻结候选中的文档；`core.ts` 均指 `workbench/src/gates/core.ts`。
- 独立性：先读指定共享 checkout 的 reviewer 角色卡及本 checkout 的 T-087，再直接读源码、调用方、规格和角色卡。只读前两轮独立抽查报告以定位旧问题及避免重复抽样；未读作者会话、`RESULTS.md`、`source-spot-check-01-fix/` 或其他作者说明/证据报告。
- 小目标：确认展示图是否忠实表达当前机械路径、记录边界和判断边界。非目标：改图、改产品、派发/集成、真实故障注入、重验既有运行结论。Tracer bullet、Deep modules、Ubiquitous language 在此分别用于识别已有交付闭环、展开其内部边界、核对现有词汇，没有新增实现。

## 按严重度列出的问题与覆盖边界

**未确认 P1/P2/P3 新问题。** 前两轮四项的回核见第 4 节。以下省略项保留为抽查边界，不把代表码表误当完整接口错误表：

- **图中缺的**：代表码表未列出部分前置/生命周期拒收码，具体见第 1 节；图未逐一展开 claim 建 worktree 失败、清理延后、每一种底层 Git/I/O 失败。图第 300、381 行明确是代表性、定向摘录。本轮没有发现这种省略把已画分支的状态、计数或 issue 保证写反。
- **图中多的**：未发现无来源的机械步骤或虚构拒收码。Q13 是真实 `checkQualityEvidence` 调用；“需修复”正确作为业务结论，没有伪装成拒收码。
- **顺序错的**：未发现。实际成功串为路径→验收文件→完成条件→红态→规则→质量证据核对→尾注→请求审查→有效审查结果→结束核对→集成。不存在“源码先审查、图却先尾注”的差异。
- **拒收码错的**：所展示字符串及其归属未发现错误。特别保留 `oracle_failed` 与 `oracle_modified`、质量已知失败与 `verification_unknown`、有效“需修复”与协议失败之间的区别。

## 1. 从门禁源码独立读出的顺序与每关拒收码

先读 `request`、`verifyCandidate` 及直接被调用函数，再对照图，未用生成脚本的锚点行序作为独立 oracle。表中列业务检查直接产生或传递的主要码；不穷举输入 schema 和所有底层 I/O 错误。

| 实际阶段 | 来源实际内容与拒收码 | 与图的比对 |
| --- | --- | --- |
| 公共锁 | `core.ts:3127` 在业务分支前取任务锁；`:238` 起用独立 SQLite 写事务互斥，占用为 `operation_busy`（`:250`）。 | 图第 206、304 行正确；锁释放不是通过证据。 |
| Claim / dispatch | `core.ts:1333` 起依次检查 ready/无当前 attempt、全局路径预留、起点及验收文件存在性，保存快照与 attempt/session/fence/intent 后才建 worktree 和会话。码含 `already_claimed`（`:1340`）、`path_overlap`（`:1082`）、`oracle_not_found`（`:1879`）、`worktree_failed`（`:1404`）；dispatch 另有 `runtime_required`、`runtime_mode_required`（`:1336`）。 | L3、E04/E05、第 324 行顺序正确。除 `oracle_not_found` 外这些代表码未列全；建 worktree 失败暂停未单画。 |
| Submit / Q0 | `core.ts:3466` 起先检查 attempt/session/fence/spec，再核对 caller、原生身份与 turn；随后状态、候选、祖先、HEAD、脏工作区；最后绑定交付事实并存 submitted（`:3570`）。码含 `stale_attempt/session/fence/spec/thread/turn`、`identity_conflict`、`invalid_state`、`candidate_conflict`、`invalid_commit`、`not_descendant`、`workspace_head_mismatch`、`dirty_worktree`、`repair_requires_new_candidate`、`delivery_facts_required/unknown`。冲突重交另有 `conflict_delivery_unconfirmed`、`conflict_candidate_unchanged`、`rework_baseline_changed`。 | 图第 180、219、305 行支持成立。代表表省略上述部分状态、交付事实和冲突专用码，没有给它们错误后果。submit 只到 submitted。 |
| verify 前置 / Q1 | `core.ts:3376` 先拒未完成冲突返工：`conflict_rework_required`；`:3379` 要求 submitted/verifying。`:1519` 保留中断验证，随后检查 repair、submitted、无旧 intent、质量快照，再取 G/C、构造 M。码有 `quality_rejection_limit`、`repair_submission_required`、`not_submitted`、`needs_reconciliation`、`project_quality_snapshot_required`、`rework_baseline_changed`；真实内容冲突在 `:1614` 为 `merge_conflict`。 | 图 Q1/E20、E49/E57 顺序正确；部分前置码未展示。合并冲突没有误画为路径失败。 |
| 路径边界 / Q2 | `core.ts:1629` 调 `checkPaths`；`:1860` 比较候选基线→C 与 G→M，`:1867` 为 `path_boundary_failed`。 | 图第 182、236、249、307 行正确。 |
| 验收文件 / Q3 | 紧接 `core.ts:1631` 调 `checkOraclePaths`；`:1886` 固定认领起点→C 加 G→M，`:1893` 为 `oracle_modified`。认领时另检查存在性。 | 图第 183、237、250、307 行正确，未把两种基线混为一谈。 |
| 完成条件 / Q4 | `core.ts:1644` 起按卡执行命令；有返回结果的非零退出打回 `oracle_failed`（`:1714`）；执行的 Refusal 在 `:1659` 转为 unknown/paused，保存后抛 `verification_unknown`（`:1674`）。底层无退出码可能是 `command_timeout` / `command_unavailable`（`:1230`）。 | 图第 184、238、251、269、306 行正确，未知出口 E60 与已知失败 E42 分开。 |
| 红态 / Q5 | 完成条件全过才在 `core.ts:1679` 进入质量串；`:1921` 起先核测试清单，再跑起点加测试及候选。四码为 `red_test_file_invalid`、`red_test_not_changed`、`red_test_symlink`、`red_state_failed`。未配置记 `red_not_applicable`（`:1961`）。 | 图第 185、239、252、308 行正确；非五码错误经 E65 暂停而非计数打回。 |
| 规则 / Q6 | 红态之后 `core.ts:1962` 遍历配置，非零为 `rule_check_failed`（`:1967`）；空列表记 `rules_not_applicable`（`:1969`）。 | 图第 186、240、253、308 行正确；未知经 E66。 |
| 质量证据 / Q13 | `core.ts:1680` 在质量串后、尾注前调 `checkQualityEvidence`；`:1975` 起检查快照、数量、清单及通过结果，不符为 `quality_reverification_required`（`:1981`）。verify 的 catch 转 `verification_unknown`；review_submit/integrate 的复核可直接返回原码。 | 图第 187、241、278、313 行完整保留这个调用位置及不同调用方后果。 |
| 尾注 / Q7 | `core.ts:1698` 调用；`:2000` 起按 task→字段完整唯一→身份→launch/tool/model/effort 核对，码为 `trailer_task_mismatch`、`invalid_trailers`、`trailer_identity_mismatch`、`trailer_launch_record_missing`。全无尾注在 `:2017` 记推断的人工介入；model 字面量 unknown 在 `:2009` 有例外。 | 图第 188、242、254、309 行正确，没有将全无尾注写成必拒收。 |
| 请求 reviewer / A5 | `core.ts:1717` 请求；`:2206` 同 C 的已通过审查须先 `requireReviewed` 才复用。新审查先保存 requested 再建目录/副本、启动及核对。码含 `review_runtime_required`（`:2212`）、`review_launch_boundary`（`:2154`）及副本身份/链接检查码（`:2098` 起）。 | 图第 189、243、327 行区分新请求与复用。副本专用码未穷举，未虚称每次重验都新建会话。 |
| 审查协议 / Q8 | `core.ts:3424` 起核 reviewer→attempt/session/fence/spec→C→verification→质量证据→实时身份→独立性/未续接→结构化结果。码含 `reviewer_required`、`stale_review`、`review_candidate_mismatch`、`review_verification_mismatch`、`stale_verification`、`quality_reverification_required`、`review_identity_unknown`、`review_launch_boundary`、`review_writer_conflict`、`review_native_session_reused`、`review_requirements_mismatch`。`QualityProtocolError` 映射 `invalid_review_result`（`:3735`）。有效“需修复”在 `:3462` 走 independent_review 打回；真实 Stop 的解析/转交失败另走 failReviewProtocol。 | 图第 190、255、279、310–314 行正确。代表表未逐项列 `review_identity_unknown`、`stale_verification`，但没有混淆业务结论和格式失败。 |
| 结束核对 / Q9 | `core.ts:2281` 先取已存 review_result；核 idle→停止/归档→副本外边界→两处清理，成功才记 review_reclaimed。码包括 `review_result_required`、`reviewer_not_idle`、`review_reclaim_unconfirmed`、`review_shared_refs_changed`、`review_worktree_changed`、`review_worker_workspace_changed`，还有副本/清理专用码。 | 图第 191、245、310 行顺序正确；verified 本身不能替代结束记录。 |
| 打分 / Q10 | `core.ts:2381` 读取参数，`qualityProtocol.ts:64` 校验结果、0～3 分与理由，`core.ts:2389` 补客观事实。码含 `score_required`、`invalid_score`、`score_provenance_required`、`attempt_already_scored`；重放另核 `score_replay_mismatch`（`:3577`、`:3590`）。 | 图第 192、246、312 行正确；后一个重放码未列入代表表。格式校验没有被说成评分正确性证明。 |
| 集成 / Q11 | `core.ts:3574` 起先验分数、verification、质量证据、已结束审查与交付来源；核已有意图或保存新 pending intent 后才 CAS，随后读回引用/内容并在事务内保存 accepted/score。码含 `not_verified`、`stale_verification`、`quality_reverification_required`、`review_required`、`stale_review`、`review_end_check_required`、`needs_reconciliation`、`integration_compare_failed`、`integration_revalidation_limit`；Git 工作区层还有 `integration_not_fast_forward`、`integration_worktree_changed/unknown`、`dirty_integration_worktree`。 | 图第 193、247–248、260–265、310、316、330 行正确；前三次 CAS 落空可重验，第四次暂停。部分工作区专用码未列，未把前置拒收概称为自动 issue。 |
| 回收 / Q12 | `core.ts:3359` 可取历史 attempt；`:3692` 判断是否仍拥有 task。核 pending intent、绑定、身份、错误可解释性、非 blocked、idle，再停止/归档读回，保存 reclaimed，最后清理。码有 `needs_reconciliation`、`no_bound_thread`、`identity_conflict`、`run_external_unknown`（`:2482`）、`run_blocked`、`worker_working`、`stop_unconfirmed`、`reclaim_unconfirmed`。 | 图第 194、248、275、316、331 行支持成立；代表表未列完整回收码，也未把前置拒收写成已清理/已上报。 |

## 2. 至少十条其他连接的来源语义抽查

共 **14 条**：ticket 字段 2 条、收件箱 4 条、恢复 4 条、持久化 4 条；不以文件存在或摘录字符串存在代替支持关系。

| 类别 / 连接 / 图中位置 | 打开的来源与实际支持内容 | 判断 |
| --- | --- | --- |
| ticket E02，第 214 行 | `scripts/inbox:334` 读票据；`:346` 只取 open；`:351` 检字段齐全；`:357` 限 ready=yes、ready_by 为 ideation/executor、正 ready_rev；`:364` 限类型/无人认领；`:366` 每个 blocked_by 必须存在且 closed/superseded。 | PASS：支持筛选，不支持证明授权正文含义。 |
| ticket E16，第 233 行及第 15 行限定 | 同函数 continue/diagnostics 是只读排除；后台 `taskCards.ts:104`、`:128` 只验来源 ready/rev 与卡号绑定，没有重做 status、ready_by、blocked_by 筛选。 | PASS：正确保留两者差别，没有把前者过滤规则强加到后台。 |
| 收件箱 E03，第 215 行 | 交接 spec `controller-split-user-input-2026-10-09.md:257` 明确 assign；实际条目 `20261016T082147Z-ideation-assign-001.md:2`–`:6` 为 ideation→executor，refs 含 T-087，`:13` 含 ready_rev；`scripts/inbox:149` 是文件发布函数。 | PASS：支持本批交接；筛选器没有发条目或建 task。 |
| 收件箱 E07，第 220 行 | spec `:263`、`scripts/inbox:211` 支持 issue→triage。后台另读 `core.ts:626` raiseIssue，`:671` 保留角色来源、`:672` 指 triage、`:694` 调 appendIssue；`:557` 将记录及 issue_issue 事件写入同一事务。 | PASS。图所引 qualityIssue 是 system→executor 的自动上报函数，不能单独证明 worker 身份；需结合同文件实际 raiseIssue 调用方。没有把自动 issue 冒充 worker 上报。 |
| 收件箱 E11，第 225 行 | spec `:265` 要逐字答复、refs 带 issue/worker；executor 角色卡 `:14` 要投递成功后 delivered/ack，已结束则 forward(session-ended)。 | PASS：协议义务有来源，不能由 answer 条目存在推断已投递。 |
| 收件箱 E14，第 230 行 | `scripts/inbox:217` 必须原收件人回原发送人；`:221` 禁止 ack 再 ack；`:223` 已确认不重复追加。spec `:266` 限为收到/执行确认。 | PASS：不等于验收。 |
| 恢复 E49，第 258 行 | `core.ts:1519` 重进时先调 interruptVerification；`:1295` 只处理 verifying，`:1298` 核 running/无 intent，`:1299` 标 interrupted，`:1311` 保存；缺输出仍 unknown。 | PASS：锁释放后可重验，不适用于直接重跑 paused（`:3379` 会拒绝）。 |
| 恢复 E52，第 261 行 | `core.ts:3594` 全部原意图绑定及 G/M 比较；M 分支 `:3613` 核内容、`:3620` 补 integrated_reconciled/score 后返回；G 分支继续原意图。 | PASS：不会在 M 分支重复 Git 更新。 |
| 恢复 E56，第 265 行 | `core.ts:1729` 连续计 misses，`:1736` 第四次 paused，`:1737` 先保存比较失败/计数，`:1742` 才上报并抛 integration_revalidation_limit。 | PASS：不是第三次暂停，也不是所有 CAS 落空都新增 issue。 |
| 恢复 E61，第 270 行 | `core.ts:2305` 捕获结束失败调 reviewLifecycleFailed；`:2178` 核 current，只有 current 才 unknown/paused，`:2183` 保存并上报；重启在 `:2196` 还区分状态及已回收记录。 | PASS：历史失败仍留原 review 的记录和 issue，不改新 attempt。 |
| 持久化 E04，第 217 行 | `core.ts:3227` 事务保存卡快照/create_intent；claim 在 `:1370` 绑定快照，`:1377` 存身份/intent，`:1392` 才建工作区。 | PASS：支持先落身份，不支持 ticket Markdown 与 SQLite 原子联动。 |
| 持久化 E05，第 218 行 | `panes.ts:196` 先存 launch，`:199` 才 spawn；`:372` 经 store.register 写 dispatch_records 后入队。`scripts/launch-worker:61`、`:75` 与 `scripts/dispatch:53`、`:73` 分别写 Herdr 两份日志。 | PASS：区分两个载体，登记与实际送达有不同事件。 |
| 持久化 E27，第 243 行 | `core.ts:2227` 新请求先保存再建副本/启动；`:2206` 的复用分支需已通过且 requireReviewed，`:2209` 仅保存 review_reused 即返回。 | PASS：复用不创建新请求/会话，不能统一说成总写 review_requested。 |
| 持久化 E32，第 248 行 | 正常 `core.ts:3682`、`:3683` 同事务记 integrated/score；恢复 `:3620`、`:3621` 记 integrated_reconciled/score。绑定 worker 的 reclaim 在 `:3729` 另写 reclaimed，随后 cleanup。 | PASS：accepted、回收成功、工作区删除不是一条记录。 |

## 3. 持久化、记录、issue 与上报的逐分支核对

检查图第 177、184–206、208–279、318–347、355–366 行中的相关断言。下列按真实写入分组覆盖这些断言；“保存/上报”均按图第 208 行的限定，指相应写入成功的路径，不将未完成的调用意图当已落地事实。

| 图中断言 / 位置 | 来源中的实际分支与边界 | 结果 |
| --- | --- | --- |
| L0/L5、I01/I04/I06/I12；第 170、178、213、227、231、234、322 行 | ready/rev/Resolution/status 在票据文件；ideation 卡 `:8`、`:17` 及交接 spec `:251` 规定标就绪/修订；executor 卡 `:9` 写 Resolution。T-030 `:5`/`:26`、T-028 `:5`/`:30` 是 superseded/out-of-scope 的真实例子。`core.ts:3682` 的集成路径保存后台状态，没有写 ticket 文件。 | PASS：文件决定及汇总义务不等于自动更新；跨介质无原子提交是限定于已读路径的推断。 |
| L4、E03/E07–E14、I03；第 177、215、220–230、323 行 | Herdr `scripts/inbox:160` O_EXCL、`:175` fsync、`:177` link、`:180` 目录 fsync；不覆盖已发表条目。answer/disposition/ack 各追加新文件。后台 appendIssue `core.ts:557` 追加 issue_records 和 events。 | PASS：条目与事件可落地；角色职责不能证明本次已完成投递，ack 不能代验收。 |
| L2/L3、E04/E05、第 324 行 | create、claim intent、卡快照和身份先保存；launch 与 dispatch 另登记。`save :985`–`:1019` 更新 task/attempt/verification 并追加事件；store `:14` 才是 launch/dispatch/orchestration_events 的防改触发器。 | PASS：未把所有状态表描述成不可变，也没把所有写入合成一个跨系统事务。 |
| Q0、E06/I07、第 325 行 | submit 成功 `core.ts:3570`；重复相同候选且无 repair 可在 `:3535` 返回 replayed。verify `:1532`、`:1540` 新建 G/C/M 绑定和 ID，`:1559` 存 verification_intent。`run :2608` 可自动触发 verify。 | PASS：已提交不等于已验收；重放不是新增一次交付记录。 |
| Q2/Q3、E20/E21、第 326 行 | `core.ts:1865`、`:1890` 在比较得到集合后分别写 path_check/oracle_check；比较所需 Git 由 execute 写 command_intent/result。比较前发生底层错误时，不能凭进入函数声称已有 path_check。 | PASS：图已改为“本关比较完成后”/“执行比较后”。 |
| Q4、E22/E42/E60、第 344 行 | `core.ts:1648` 先写 completion_intent；取得返回结果才 `:1653` completion_check；非零进入已知失败。Refusal catch `:1661` unknown、`:1662` paused，`:1673` verification_result，抛 verification_unknown。 | PASS：E60 没有调用 qualityIssue/lifecycleIssue/appendIssue，也不加打回次数。 |
| Q5/Q6、E23/E24/E43/E44、第 326 行 | `core.ts:1912` 每命令 quality_command_intent；红态取得两次结果才 `:1958` red_check，规则取得结果才 `:1966` rule_check；无配置 `:1961`/`:1969` 才记不适用。 | PASS：未把命令意图说成已有检查结果。 |
| Q13、E25/E67、第 241、326 行 | `core.ts:1973` 是纯证据核对，无独立成功事件；正常路径 `:1711` 最终 verification_result。失败在 verify 的质量 catch 分流。 | PASS：没有虚构逐关成功日志。 |
| Q7、E26/E45、第 242、326 行 | `core.ts:1984` 先列新增提交，`:1986` 遍历，`:2013` 逐提交 trailer_check。提交列表为空时无逐提交事件；某提交完全无 A2A 尾注时 `:2017` 追加人工介入推断。 | PASS：空循环和全无尾注分支已区分。 |
| Q8/Q9、E27/E30/E46、第 327 行 | `core.ts:2227` 新请求；`:2209` 复用；`:3461` 有效结果；需修复才 `:3462` 调 rejectDelivery；结束核对清理完成才 `:2304` review_reclaimed。 | PASS：四种记录不混用，判断正确性未被当作程序保证。 |
| R1、E40–E48、第 328、340 行 | `core.ts:2053` 按 attempt 算 delivery_rejected 次数；`:2061` 存 repair/计数，第三次 `:2062` 在同一事务写 blocking issue。无绑定 thread `:2066` 另建 issue。有原会话还须实时核对才调用 qualityFeedback；`panes.ts:359` 停止分支取消质量返工队列并记 quality_feedback_stopped，否则先登记 dispatch 后入队。 | PASS：打回记录没有被当作回写成功；停止反馈事件也不是无条件发生于所有异常分支。 |
| R2/E53/I10、第 196、262、271、341、365 行 | `core.ts:3594` 对已有 intent 核绑定及 actual=G/M；不符抛 needs_reconciliation，保留 integrating/pending，不新增 issue。`revoke/revise :3333` 不能绕过 pending intent。 | PASS：P2-03 的第二个反例已正确体现；没有统一 task.paused 或统一 issue 的保证。 |
| R2/E56、第 342 行 | `core.ts:1737` 保存 misses；仅到第四次 `:1742` 调 lifecycleIssue。 | PASS：计数先落地，达到上限才上报。 |
| R7/E57–E59、第 201、266–268、343 行 | `core.ts:1610` 保留候选/base refs，`:1612` 保存冲突；`:1461` 保存返工意图。原会话可用则保存 delivered；结束则读回停止/归档、回收、失效、新 claim。catch `:1507` 将 repair 设 unknown、`:1510` 保存并调 lifecycleIssue，不将 task 统一设 paused。 | PASS：投递/创建结果未知不等于可盲重送，也不等于 task.paused。 |
| R2/E60/I10、第 269、271、344、365 行 | 完成条件 unknown 只保存 verification_result；公共外层可追加 rejected，但没有 issue 写入。下一质量块的 `:1695` 不会替这条已抛出的路径补上报。 | PASS：P2-03 的第一个反例已正确体现。 |
| R2/E61/E63、第 270、274、345 行 | `core.ts:2178` current 判断保护新执行；`:2183`、`:2184` 在事务内保存 review_lifecycle_failed 并创建原 review/attempt 的 issue。历史失败仍留记录，但不改新执行的状态。 | PASS：不能把所有 review_lifecycle_failed 都解释成当前 task 已 paused。 |
| R2/E65–E67、第 276–278、329、346 行 | `core.ts:1683` 只认五个已知失败码；其余 unknown/paused，`:1690` 保存，`:1695` qualityIssue，`:1696` 对外 verification_unknown。 | PASS：有 issue，不计 delivery_rejected；不外推给全部 R2。 |
| R2/E68、第 279、347 行 | `daemon.ts:102` 解析失败或 `:135` 转交失败调 failReviewProtocol；`core.ts:2264`/`:2266` 先核绑定/caller。运行中 `:2274` 保存、`:2275` 上报；cancelled 的迟到分支 `:2268` 仅记 review_after_termination。 | PASS：解析失败不保证有门禁 request 外层 rejected；图已写清。 |
| Q11/R5/R6、E31/E32/E51–E56、第 330 行 | `core.ts:3656` pending intent 早于 `:3659` Git；`:1815` prepare、`:1827` commit；正常读回 `:3682`，引用已到 M 则 `:3620` 补账。任务接受与打分同事务。 | PASS：Git 与 SQLite 不同事务，恢复不重写已完成 Git。 |
| Q12/R8/E62/E64、第 194、273、275、331 行 | reclaim 先身份/idle/停止归档读回，`:3729` 存 reclaimed；cleanupAttempt `:1094` 未回收则仅 deferred，`:1106` 未解决验收保留并上报，`:1127` 脏目录同样保留；成功删除前 `:1130` 保留 ref、`:1132` 存 cleanup intent。catch 只对 `:1151` 列明的 Refusal 做 preserve。abandon `:3416` 存终结/分数，返回 cleanup:not_performed。 | PASS：没有把前置拒收、延后、保留上报和删除成功统一成一种结果。 |
| 公共 rejected 及 I01–I12 的判断记录；第 208、332 行 | `core.ts:3751` 只有 taskId 已知、观察器未 failed 时才尝试 `:3752` rejected；save 不隐式建 issue。角色卡/规格要求记录决定，却不证明授权、处置、评分或变异判断正确。 | PASS：条件和证据能力限定均保留；不会因“有日志”就宣称判断正确。 |

### 前两轮未专门抽过的路径

对照前两轮抽样表和新增路径表，本轮另选以下四条；不是复用它们原来的 PASS：

1. **尚未回收 worker → 清理延后**：`core.ts:1094`–`:1096` 只写 `worktree_cleanup_deferred` 后返回，不写 `worktree_preserved`，不新增 issue，也不删除。紧邻的未解决验收分支 `:1105` 则通过 preserve 保存并上报。图 Q12 第 194 行没有把这两条支路混同；第 331 行也没有声称一进入清理就删除。
2. **integrate 缺审查结束记录 → 直接拒收**：`core.ts:3588` 调 requireReviewed，`:2172` 可抛 `review_end_check_required`；这一路没有调用 reviewLifecycleFailed，外层只按条件记 rejected，原 verified 状态不因此自动 paused。图第 310 行的新限定明确写“前置拒收本身只走外层 rejected，不自动建 issue”，支持成立。结束流程内实际边界失败才是 E61。
3. **尾注新增提交列表为空**：`core.ts:1984` 的列表为空时不进入 `:1986` 循环，所以既没有 trailer_check，也不进入 `:2017` 的缺尾注人工介入。图 E26 第 242 行及第 326 行已限定空循环，无虚构持久化记录。
4. **历史 review 的回收失败**：`reclaimReview :2284` 按 review_id 取旧 review_result，失败在 `:2306` 重新加载当前 task。`reviewLifecycleFailed :2178` current=false 时仍写旧 review 的失败事件/issue，但不使新 task/review 暂停。图 E61/E63 第 270、274 行的历史分支限定有直接来源。

## 4. 前两轮四项的回核

| 原问题 | 当前图中位置与直接来源 | 本轮结论 |
| --- | --- | --- |
| P2-01 质量未知出口缺失 | 图 Q13 第 187 行、E65–E67 第 158–160 / 276–278 行、第 313、329、346 行。`core.ts:1679`/`:1680` 的两次调用及 `:1683`–`:1696` 的已知/未知分流均已直接打开。 | PASS：补了质量证据核对和未知暂停/上报，未知不计作打回。 |
| P2-02 审查协议失败出口缺失 | 图 E46 第 255 行限定有效需修复；E68 第 161、279 行及第 314、347 行。`daemon.ts:102`、`:106`、`:135`，`core.ts:2260`–`:2277`，`qualityProtocol.ts:33`、`:45`，`core.ts:3735` 支持解析、门禁转交和取消例外。 | PASS：业务需修复、协议失败与 cancelled 迟到三条后果分开，未增加协议失败打回计数。 |
| P3-01 model unknown 例外遗漏 | 图 Q7 第 188 行、第 309 行；`core.ts:2009` 双重不等才拒收，`:2001` 仍要求九个必需字段齐全、唯一、非空。 | PASS：例外仅为 model 字面量 unknown，没有放宽 launch/tool/effort。 |
| P2-03 R2 统一保证 issue | 图 R2 第 196 行、公共限定第 208 行、E53/E60/I10 第 262、269、271 行、完整分支表第 334–347 行及第 365 行。`core.ts:1659`、`:3594`、`:985`、`:3751` 分别支持 unknown 结果、pending 引用不符、save 能力及 rejected 条件；另逐支核对有上报的路径。 | PASS：已删除通用 issue/paused 保证；完成条件未知与 pending 意图第三值明确无新增 issue。 |

## 5. 隐式边抽查与 T-081/T-082 覆盖

自行检索而后打开实现及直接调用方，执行过的检索包括：

```sh
rg -n 'ready_by|ready_rev|needs-decision|completion_conditions_sufficiency|mutation_checks|cancel|qualityIssue|lifecycleIssue|unknown|paused' workbench/src/gates/taskCards.ts workbench/src/gates/qualityProtocol.ts scripts/inbox scripts/dispatch
rg -n 'ready_rev|ready_by|completion_conditions_sufficiency|needs-decision|failReviewProtocol|checkQualityEvidence|command === "(verify|revoke|revise|abandon)"' workbench/src/gates/core.ts workbench/src/daemon.ts
rg -n 'source|blocked_by|ready_by|ready_rev|needs-decision|disposition|reviewEvidence|scoreData|command === "verify"|command === "abandon"' workbench/src/gates workbench/src/daemon.ts scripts --glob '*.ts' --glob '*.py' --glob 'inbox' --glob 'dispatch' --glob 'launch-worker'
```

“无机械来源”按图第 351 行理解为无程序证明语义判断正确，不是完全没有输入检查、状态机或记录。grep 无匹配没有单独充当全仓库不存在功能的证明。

| 隐式边 / 图中位置 | 机械边界及剩余判断 | T-081 / T-082 的覆盖判断 |
| --- | --- | --- |
| I01，第 213、355 行 | `scripts/inbox:357` 只验字面字段；`taskCards.ts:105`、`:128` 只验来源 ready/rev。授权含义由 ideation 卡 `:8`、交接 spec `:287` 交给人/主控，没有解析自由正文证明用户同意的实现。 | PASS：T-081 `:18` 起是交付坏行为及能力/正例；T-082 `:18` 是完成条件/变异要求。两票均不能证明用户授权含义。 |
| I04，第 227、358 行 | 交接 spec `:251` 明确旧 rev 的 worker 继续还是重来由执行主控决定。`core.ts:3331` 的门禁 revise 会使旧身份失效，但那是已经选择 revise 后的机械操作，不是自动从收件箱修订文字推导执行策略。 | PASS：T-081 `:22` 覆盖迟到旧身份拒收，不保证应该继续还是重来；T-082 保护候选/审查绑定，不决定修订策略。 |
| I08，第 244、363 行 | `qualityProtocol.ts:33`–`:42` 只核结构和节名，注释明确不核判断或变异是否应失败；`core.ts:3453` 绑定副本与要求，`:3461` 保存结论。协议错误出口是 E68，不能归入此语义判断。 | PASS：T-082 `:31` 明确不把 reviewer 判断正确作为门禁通过条件；T-081 坏行为样本不能证明任意 reviewer 判断正确。图已保留覆盖边界。 |
| I10，第 271、365 行 | 已有具体暂停/等待出口；`core.ts:3379` 阻止直接重跑 paused，`:3333` 保护 pending intent。后续修复、撤销、放弃或升级仍受 executor 卡 `:13`、T-004 `:18` 的判断边界约束，没有统一自动解锁成功路径。 | PASS：T-081 `:30` 的 CAS 样本不覆盖所有未知恢复；T-082 `:21`/`:30` 覆盖审查结束边界与失效上报，不能扩大为主控全部后续决定或所有质量/协议失败。 |

T-081/T-082 的日期统计只核票据 Resolution（T-081 `:48`–`:49`、T-082 `:43`–`:46`）与范围，没有读取它们所链的 RESULTS 来继承运行结论，也没有重跑旧套件。

## 6. 再生成、文档反例与完成条件的能力

在 `/tmp/t087-spot-check-03-vr2h6qij/` 复制生成脚本，用 `--root` 指向冻结 checkout；脚本以 stdout 返回生成文档。实际命令：

```sh
python3 -B /tmp/t087-spot-check-03-vr2h6qij/generate_t087_graph.py --root /Users/luckye/Documents/Code/a2a-wt-t087
python3 -B /tmp/t087-spot-check-03-vr2h6qij/generate_t087_graph.py --root /Users/luckye/Documents/Code/a2a-wt-t087 --check /Users/luckye/Documents/Code/a2a-wt-t087/findings/ticket-gates-graph-2026-10-16.zh-CN.md
```

生成退出 **0**，stderr 为空；stdout 与提交文档按 UTF-8 解码后完整文本直接比较，**631 行，全文一致**。没有使用哈希、校验和或指纹。`--check` 退出 0：35 个点、68 条连接、241 行来源、621 次来源使用；结果明确 `semantic_audit` 未执行。

可在仓库根目录重现文本比较：

```sh
python3 -B - <<'PY'
from pathlib import Path
import subprocess
r = subprocess.run(['python3', '-B', 'findings/generate_t087_graph.py'],
                   text=True, encoding='utf-8', capture_output=True, check=True)
assert r.stdout == Path('findings/ticket-gates-graph-2026-10-16.zh-CN.md').read_text(encoding='utf-8')
print(len(r.stdout.splitlines()), repr(r.stderr))
PY
```

另在该临时目录构造三个文档级错误实现，引用与 ID 保留不变，分别运行上述 `--check <反例绝对路径>`，再与刚生成的完整文本比较。预期判断来自源码分支，而不是生成物自己的输出：

| 反例 | 具体改动 | 实际结果及独立 oracle |
| --- | --- | --- |
| M1-completion-issue | E60 的“不新增 issue，不计作已知失败”改成“新增 issue，并计作已知失败”。 | `--check` 退出 0；全文比较不等。`core.ts:1659`–`:1674` 没有 issue 或 rejectDelivery 调用，独立来源拒绝这个变异。 |
| M2-review-reuse | E27 的“不新建请求或会话”改成“仍新建请求和会话”。 | `--check` 退出 0；全文比较不等。`core.ts:2206`–`:2210` 保存 review_reused 后返回，没有进入新请求分支，独立来源拒绝这个变异。 |
| M3-historical-review | E61 的“历史失败不改新执行”改成“历史失败也暂停新执行”。 | `--check` 退出 0；全文比较不等。`core.ts:2178`–`:2180` 只有 current 才改状态，独立来源拒绝这个变异。 |

因此单靠 `--check` 不足以验收语义；生成脚本和文档同时写错也可能全文一致。本票把非作图会话的独立来源抽查列为完成条件，这一步能识别上述明显错误。没有将引用检查的 PASS 冒充语义 PASS，也不把三个文档反例称为产品代码变异。

保留检查过程中的失败：第一次临时驱动在生成脚本返回之后，试用 `Path.write_text(..., newline=...)` 保存输出，本机 Python 不支持该参数，驱动报 `TypeError: write_text() got an unexpected keyword argument 'newline'`。这是抽查驱动失败，没有据此宣称文本一致；随后仅将临时驱动改为 `Path.open(..., newline='\n')` 并重跑，得到上面的实际结果。两次 TemporaryDirectory 均自动清理，成功目录读回 `exists=False`。另一次探索性 rg 将不存在的 `scripts/launch` 加入参数，返回文件不存在；随后实际打开的是 `scripts/launch-worker`，未将前一次命令当作完整检查证据。

## 7. 术语、未运行项与收尾

术语：**PASS**。对照 CONTEXT 及 T-087 的术语要求，图第 9–11、166–202 行继续使用确定性步骤/门禁检查、agent 会话、人工决定点与 task/attempt。脚本 `point`、`edge`、`points`、`edges` 是绘图构造函数和局部数据，没有新增领域对象、执行 API 或产品总称；文档的“点/连接”是一般读图用词，没有替多个领域概念定义新名字。`Graph Engineering` 未写入 CONTEXT；本候选没有借图新增执行器。

未运行项：产品服务、真实 CLI/模型回合、完整门禁端到端场景、T-081/T-082 回归和 Mermaid 视觉渲染。没有门禁提供的一次性产品副本，未做 reviewer 角色卡所述的产品代码变异；本次仅在授权的 `/tmp` 新目录里做文档反例。结论严格限于用户派发的静态来源抽查，不能当作完整 T-082 产品审查或运行可靠性证明。

实际在开始、写报告前及最终回读时核对：

```sh
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
git rev-parse HEAD
git branch --show-current
git status --short
```

地图检查退出 0，`Problems (0)`、`Stale living docs (0)`；冻结 HEAD/分支未变。最终文件回读检查 UTF-8、无 BOM、LF、无替换字符、末行标记；唯一新增文件为本报告。没有改候选、其他证据、票据、地图、产品或全局配置；没有 git commit/checkout/reset、模型 API、外部发送或沙箱升级。

最终结论：**PASS（本轮抽查范围）**。前两轮四项已补正，新增路径及记录边界核对未确认新问题；省略码和未运行项如上保留，不作全路径或运行验收承诺。

T-087 SPOT-CHECK 03 DONE
