# T-087 第二轮独立来源抽查

结论：**NO_GO，需修复**。第一轮的 P2-01、P2-02、P3-01 均已按来源补正；成功检查串的顺序正确，重新生成的全文一致。本轮另确认一处恢复记录描述错误：I10 把不同分支汇入 R2 后统一写成“issue 有记录”，而完成条件未知、pending 集成意图引用不匹配两条已画路径并不创建 issue。以下结论针对冻结图文档的来源准确性，不是产品运行验收。

- 日期：2026-10-16。
- 仓库：`/Users/luckye/Documents/Code/a2a-wt-t087`；分支：`exec/t087`。
- 冻结候选：`c69da1c81c59328927e02b45cd87ba3c6110122e`，由 `git rev-parse HEAD` 确认；开始和写报告前均未变化，工作区干净。
- 审查对象：`findings/ticket-gates-graph-2026-10-16.zh-CN.md`、`findings/generate_t087_graph.py`。下文“图第 N 行”均指该冻结文档。
- 已读指定共享 checkout 的 reviewer 角色卡、本 checkout 的 T-087、MAP、CONTEXT、intent 及所引源码/规格。只读第一轮独立报告 `source-spot-check-01.md` 以识别原三项和已抽路径；未读作者会话、`RESULTS.md`、`source-spot-check-01-fix/` 或作者其他证据报告。T-081/T-082 只读票据要求及日期 Resolution，不继承其 PASS 为本图背书。
- 小目标：核对每关顺序与拒收码、其他连接的来源语义、隐式判断、持久化边界、重生成和术语。非目标：修图、改产品、派发、集成、运行服务或模型、重验 T-081/T-082。
- 重要边界：这是静态来源抽查加文本检查。没有门禁提供的一次性产品副本，未做产品代码变异或真实故障注入；文档反例仅在新建 `/tmp` 目录内构造。未把它写成完整 T-082 产品审查。

## 按严重度列出的问题

### P2-03：I10 将“暂停或等待核对”错误地统一描述为已有 issue

**图中位置**：第 269 行 I10（R2 → R3）的持久化列写“issue 有记录；不存在通用自动解锁成功路径”，由生成脚本第 332 行固定输出。R2 明确包含第 151/267 行 E60（完成条件未知），也包含第 144/260 行 E53（pending intent 第三值/引用丢失）。这不是只描述质量未知和审查协议失败的局部句子。

**来源实际内容与两个静态反例**：

1. 完成条件命令不能启动或超时：`workbench/src/gates/core.ts:1230` 将缺退出码的执行错误变为 `command_unavailable` / `command_timeout`；完成条件的 catch 在 `core.ts:1659` 起设 `v.state="unknown"`、`task.state="paused"`，保存缺失输出和退出码，`core.ts:1673` 只调用 `save(..., "verification_result", ...)`，`:1674` 抛 `verification_unknown`。该块没有调用 `qualityIssue`、`lifecycleIssue` 或 `appendIssue`。不能用下一质量块 `core.ts:1695` 的上报替它背书：前一块已抛出。
2. 已有 pending 集成意图，而集成引用既非 G 也非 M（含返回空引用）：`core.ts:3593` 起核对 intent 绑定，`:3609` 的条件不成立时在 `:3610` 拒绝为 `needs_reconciliation`。这里没有 issue 写入，也没有把 task 从 `integrating` 改为 `paused`；保留的是原 pending intent。图 E53 的“保留 pending intent”正确，后续 I10 的统一 issue 断言不正确。

两条路径的公共外层 `core.ts:3732` catch 只在 `:3752` 追加 `rejected` 事件，不补 issue；`save` 的 `core.ts:985` 实现只更新 task/attempt/verification 并追加事件，也不隐式建 issue。即使经 `run` 进入，`core.ts:2645` 的错误处理最终在 `:2694` 保存 `run_finished`，没有补这项 issue 保证。

**影响**：读者可能以为所有 R2 情形都会出现待处置问题，因而只查问题面板而漏看 task/verification、门禁回执或 pending intent。这正涉及本票要说明的持久化边界；有失败事件不能写成有 issue。

**最小修正**：只改生成脚本和文档，将 I10 限定为“按具体分支核对持久记录；部分分支另有 issue”，并注明 E60 保存 verification_result/rejected、E53 保留 pending intent/rejected；保持质量未知与审查协议失败的上报说明。无需借本票改变产品行为，也无需发明通用恢复机制。

未发现 P1。除上述 P2 外，未确认新的拒收码拼写错误、成功主串顺序错误或新增业务术语。下文列出的未展开支路与代表码表省略项作为覆盖边界保留，不自动升级为另一个阻断问题。

## 1. 从门禁源码读出的实际顺序与拒收码

先以实际调用与函数体确定顺序，再对照图的 Q0–Q13、E20–E32；未用生成脚本的锚点顺序作独立 oracle。下表覆盖图中每关及直接前后边界；不穷举每个输入 Schema、底层 Git、文件系统和进程错误。

| 实际阶段 | 来源实际内容、主要拒收码 | 与图逐项比对 |
| --- | --- | --- |
| 公共操作锁 | `core.ts:3127` 取锁；`core.ts:238` 的实现占用时报 `operation_busy`（`:250`）。 | 图第 206/302 行正确；释放锁不替代验收。 |
| Claim | `core.ts:1333`：ready/无当前 attempt → `$claims` 锁 → 路径预留 → 读起点 → 验收文件存在性 → 快照与身份入库 → 建工作区 → 创建会话/派发。码有 `already_claimed`（`:1340`）、`path_overlap`（`:1082`）、`oracle_not_found`（`:1879`）、`worktree_failed`（`:1404`）；dispatch 还要求 `runtime_required`、`runtime_mode_required`。 | L3/E04/E05 的成功顺序正确。图只列了部分 Claim 码，未展开建工作区失败暂停，见第 4 节。 |
| Submit 身份 | `core.ts:3466` 依次核对 attempt、session、fence、spec、thread/活跃身份、turn：`stale_attempt`、`stale_session`、`stale_fence`、`stale_spec`、`stale_thread`、`identity_conflict`、`stale_turn`。`current` 另在 `:2028` 防过期身份。 | Q0/图第 303 行支持成立。 |
| Submit 候选 | `core.ts:3491` 起：返工投递已确认 → 合法状态 → 固定候选 → commit 存在/后代 → 返工基线 → HEAD/干净 → 修复新 C → launch 交付事实 → 保存 submitted（`:3570`）。码含 `conflict_delivery_unconfirmed`、`invalid_state`、`candidate_conflict`、`invalid_commit`（`:1256`）、`not_descendant`、`rework_baseline_changed`、`conflict_candidate_unchanged`、`workspace_head_mismatch`、`dirty_worktree`、`repair_requires_new_candidate`、`delivery_facts_required`、`delivery_facts_unknown`。 | Q0 到 submitted，尚未验收，正确。图第 303 行是代表集，省略了这里部分返工/状态/事实缺失码。 |
| verify 前置、构造 M | 请求层 `core.ts:3376` 拒绝未完成返工为 `conflict_rework_required`，`:3379` 限 submitted/verifying。`verifyCandidate :1519` 先处理中断，`:1520` 起依次要求无 repair、已 submitted、无 pending intent、有质量快照，再取 G/C、建验证工作区和 M。码含 `quality_rejection_limit`、`repair_submission_required`、`not_submitted`、`needs_reconciliation`、`project_quality_snapshot_required`、`rework_baseline_changed`、`merge_conflict`（`:1614`）。 | Q1 在路径检查前构造 M，冲突转 E57，正确。部分前置码未列入图的代表表。 |
| Q2 路径边界 | 调用 `core.ts:1629`；实现 `:1858` 合并候选基线→C 与 G→M 的路径，`:1867` 为 `path_boundary_failed`。 | Q1 → Q2 → Q3、E40 正确。 |
| Q3 验收文件保护 | 紧接 `core.ts:1631`；实现 `:1881` 比冻结认领起点→C 及 G→M，`:1893` 为 `oracle_modified`。 | Q3/E41 正确；未把返工基线替换为新的保护起点。 |
| Q4 完成条件 | `core.ts:1644` 顺序执行 argv，`:1655` 首次非零即停止；非零最终 `oracle_failed`（`:1715`）并打回。执行结果未知在 `:1659` catch 保存 unknown/paused 并抛 `verification_unknown`。 | Q4/E42/E60 正确；E60 后不保证有 issue，见 P2-03。 |
| Q5 红态 | 完成条件全过才在 `core.ts:1679` 进入；`checkQuality :1921` 先逐个检查测试清单，再跑起点加测试（`:1952`）与候选（`:1953`）。已知码：`red_test_file_invalid`、`red_test_not_changed`、`red_test_symlink`、`red_state_failed`。无配置记 `red_not_applicable`（`:1961`）。 | Q4 → Q5 正确；E43 四码打回，E65 非已知错误暂停，均正确。 |
| Q6 规则式检查 | 红态循环后才到 `core.ts:1962`，非零为 `rule_check_failed`（`:1967`）；无规则记 `rules_not_applicable`（`:1969`）。 | Q5 → Q6，E44/E66 正确。 |
| Q13 质量证据核对 | `core.ts:1680` 在 `checkQuality` 返回后、尾注前调用；`core.ts:1973` 核对质量快照、数量、测试清单及通过结果，不符为 `quality_reverification_required`（`:1981`）。verify 的非五码错误分支在 `:1683` 转 unknown/paused，对外 `verification_unknown`（`:1696`）。 | 新增 Q13、E25/E26/E67 正确；图第 311 行也正确区分 review_submit/integrate 直接复核可原样拒收。 |
| Q7 提交尾注 | `core.ts:1698` 才调用。`:2000` 起按条件产生 `trailer_task_mismatch` → `invalid_trailers` → `trailer_identity_mismatch` / `trailer_launch_record_missing`。`:2009` 的 model=`unknown` 例外存在；完全无 A2A 尾注则 `:2017` 记人工介入。 | Q13 → Q7，E45 以及第 188/307 行正确。 |
| 请求 reviewer | 串通过并保存/清理验证工作区后，`core.ts:1717` 调 `requestReview`。新审查 `:2227` 先持久请求，再建目录/副本和启动；`:2135` 起核对 `review_launch_boundary`。同 C 的已结束合格审查可在 `:2206` 受限复用；缺 runtime 为 `review_runtime_required`。 | Q7 → A5 正确。主串须连同 E55 的复用例外读，不代表每次 CAS 重验都新开审查。 |
| Q8 审查协议与绑定 | `core.ts:3424`：reviewer/当前运行审查 → 身份/规格/卡 → C → verification/质量证据 → 活跃身份 → 独立性/未续接 → 报告与副本绑定。码含 `reviewer_required`、`stale_review`、`review_candidate_mismatch`、`review_verification_mismatch`、`stale_verification`、`quality_reverification_required`、`review_identity_unknown`、`review_launch_boundary`、`review_writer_conflict`、`review_native_session_reused`、`review_requirements_mismatch`、`invalid_review_result`（`:3735`）。 | Q8 成功关系正确；图第 309 行未列全部身份/复核码，但新增第 312 行格式码和 E68 暂停出口正确。有效“需修复”才在 `:3462` 经 `independent_review` 打回。 |
| Q9 结束核对 | `core.ts:2281`：有结果/runtime → live 身份/idle → stop/archive 读回 → 副本/共享 refs/审查及 worker worktree → 清理 → `review_reclaimed`。码含 `review_result_required`、`reviewer_not_idle`、`review_reclaim_unconfirmed`、`review_candidate_copy_missing`、`review_candidate_copy_identity_unknown`、`review_shared_refs_changed`、`review_worktree_changed`、`review_worker_workspace_changed`；清理另有 `review_cleanup_identity_unknown`、`dirty_review_worktree`、`review_cleanup_unconfirmed`。 | E30/Q9/E61 正确；图第 308 行为代表码。缺 `review_reclaimed` 在 `:2172` 为 `review_end_check_required`，不能只凭 verified 集成。 |
| Q10 打分、Q11 integrate | `core.ts:3575` 先读评分格式，`:3585` 起再核对 verified、verification、质量、有效审查和结束记录、交付来源、重放评分，才读引用。新意图 `:3656` 先保存，`:3659` 做 CAS，`:3671` 读回并核对内容后 accepted/记分。码含 `score_required`、`invalid_score`、`score_provenance_required`、`attempt_already_scored`、`not_verified`、`stale_verification`、`quality_reverification_required`、`review_required`、`stale_review`、`review_end_check_required`、`score_replay_mismatch`、`integration_compare_failed`、`integration_revalidation_limit`、`needs_reconciliation`；工作区另有 `integration_worktree_unknown/changed`、`integration_not_fast_forward`、`dirty_integration_worktree`。 | Q9 → 主观打分 → integrate 是正常工作流，支持成立；不是逐个内部谓词的时间顺序。E51–E56 的 G/M、CAS 重验与四次上限正确。 |
| Q12 reclaim/cleanup | `core.ts:3698` 拒绝未解决 intent → runtime/thread → 绑定身份 → 外部状态 → blocked/idle → 回收意图 → stop/archive 读回 → reclaimed → cleanup。码含 `needs_reconciliation`、`no_bound_thread`、`identity_conflict`、`run_external_unknown`、`run_blocked`、`worker_working`、`stop_unconfirmed`、`reclaim_unconfirmed`。`cleanupAttempt :1092` 的异常保留并上报，不冒充目录已删除。 | E32/Q12 正确。图只直接点出 worker_working，并未穷举回收接口码。 |

逐项汇总：

- **缺的**：未发现成功主串缺关；部分接口拒收码未列出，如上表。额外抽到的 Claim/派发未知支路未作为图形连接展开，见第 4 节；图第 298/364 行已限定代表性摘录，不据此要求穷举所有底层错误。
- **多的**：I10 对所有 R2 情形附加“issue 有记录”这一保证，来源不支持，见 P2-03；未发现凭空增加的成功检查。
- **顺序错的**：未发现。实际为路径 → 验收文件 → 完成条件 → 红态 → 规则 → 质量证据核对 → 提交尾注 → 请求审查 → 有效结果 → 结束核对 → 集成。
- **拒收码错的**：已展示字符串未发现拼错或虚构；“需修复”正确保留为业务结论。代表表不等于完整接口错误表。

## 2. 其他连接的来源语义抽查（14 条）

每项均打开对应文件与上下文；判断的是来源能否支持条件、方向和记录边界。行号不是仅靠生成物中的摘录读回。

| 类别 / 连接 / 图中位置 | 实际打开的来源与语义 | 结果 |
| --- | --- | --- |
| ticket E02，第 212 行 | `scripts/inbox:346` 排除非 open；`:357` 验 ready=yes、ready_by 为 ideation/executor、正 ready_rev；`:364` 排除错误类型/已认领；`:366` 要求所有 blocked_by 为 closed/superseded。规格 `controller-split-user-input-2026-10-09.md:245` 起说明这些字段。 | PASS：是只读筛选，字段合法不能证明授权含义。 |
| ticket E16，第 231 行 | 同脚本 `:351` 缺字段报不合规，`:355` ready=no 跳过，`:360` 验依赖列表，`:368` 返回 diagnostics。`taskCards.ts:104`、`:128` 仅要求来源 ready/rev 与绑定，未实现整套就绪筛选。 | PASS：图第 15 行保留了脚本与后台校验边界，没有说后台重验 blocked_by/ready_by。 |
| 收件箱 E03，第 213 行 | 交接规格 `:257` 是构思→执行的 assign；本批条目 `.project-map/inbox/20261016T082147Z-ideation-assign-001.md:2` 起的 from/to/kind/refs 包含 T-087。`scripts/inbox:149` 才是落盘函数。 | PASS：支持本批交接；不支持筛选器自动发 assign，图也没有这样声称。 |
| 收件箱 E07，第 218 行 | 规格 `:263` 是 worker/reviewer/monitor→triage；`scripts/inbox:211` 强制 issue 指向 triage。另追后台 `core.ts:626` 的 raiseIssue，`:671` 保留角色来源、`:672` 指 triage、`:694` appendIssue。图所引 qualityIssue 是 system 路径，单看它不足以证明 worker 路由；实际直接调用方补足该核对。 | PASS：方向和记录存在；不能把 system qualityIssue 当作 worker 身份证明。 |
| 收件箱 E10，第 222 行 | 规格 `:261`、`:262` 分别给 report、needs-decision 定方向；`:278` 要求逐字状态，`:285` 不上调；执行角色卡 `:21` 要求设计/目标/验收问题停该 ticket 并上交。 | PASS：支持条件与方向；条目种类不能证明其问题判断正确。 |
| 收件箱 E14，第 228 行 | `scripts/inbox:217` 起 ack 必须原收件人回原发送人，`:221` 禁止 ack 再 ack，`:223` 重复确认不再追加。规格 `:266` 只说确认收到/执行。 | PASS：确认不等于验收。 |
| 恢复 E48，第 255 行 | `core.ts:2053` 按原 attempt 计 delivery_rejected，`:2058` 第三次 paused，`:2061` 保存、`:2062` 同事务追加 blocking issue；`panes.ts:359` 停止时取消质量返工队列并记事件。 | PASS：这条支路确实有 issue，不能推广到所有 R2。 |
| 恢复 E53，第 260 行 | `core.ts:3594` 核对原 intent 的全部绑定及 actual=G/M；`:3610` 不符 needs_reconciliation。`:3333` 禁止 revoke/revise 绕过 pending intent。 | PASS：保留意图并拒绝绕过；并不创建 issue，I10 的统一保证 NO_GO。 |
| 恢复 E62，第 271 行 | `core.ts:3331` revoke/revise 先拒 accepted/pending intent，再按需升级 spec；`:3353` 调 invalidate。后者 `:1316` 撤销旧身份、`:1320` 清 current attempt、`:1321` 回 ready。新 claim `:1351` 生成新身份并 fence+1。 | PASS：就 R8 的操作而言，revoke/revise 可回认领；abandon 不会直接回 ready。 |
| 恢复 E64，第 273 行 | `core.ts:3410` 起 abandon 把未完成 review 标 cancelled，保存 attempt_ended/评分且明确 cleanup:not_performed（`:3422`）。历史 attempt reclaim `:3359` 另取原记录；`:3692` 的 ownsTask 控制失效操作，避免接管新执行。 | PASS：终结不等于回收，须按原 attempt 后续核对。 |
| 持久化 E04，第 215 行 | `core.ts:3227` 起事务内存 card snapshot/create_intent；claim `:1370` 快照绑定 attempt、`:1377` 存 intent，随后 `:1392` 才建 worktree。`save :985` 同事务更新状态并追加事件。 | PASS：身份先落库，再有外部副作用；不是 ticket 文件与数据库原子联动。 |
| 持久化 E06，第 217 行 | `core.ts:3570` 保存 submitted；拒收通过 `:3752` 追加 rejected。交付事实在 `:3542` 绑定 launch、CLI、model、effort 和 C。 | PASS：显式交付留记录，不能从提交说明推断已验收。 |
| 持久化 E30，第 243 行 | `core.ts:3461` 存 review_result 后可为 verified；reclaimReview 的 `:2301`、`:2302` 清理两处，`:2304` 才记 review_reclaimed。`requireReviewed :2170` 检查后者存在。 | PASS：两个记录分开，verified 不能绕过结束边界。 |
| 持久化 E31，第 245 行 | `core.ts:3633` 起 intent 含 G/C/M、verification、attempt clone、spec、snapshot、ref 和 score；`:3656` 持久，`:3659` 才推进 Git。`advanceWorkBranch :1815` prepare，`:1827` commit。 | PASS：支持先存意图再 CAS；没有 SQLite/Git 跨系统原子事务。 |

计数：ticket 字段 2 条、收件箱 4 条、恢复 4 条、持久化 4 条，共 14 条，四类均至少 2 条。

## 3. 隐式边抽查（4 条）

自行检索执行路径，采用以下实际命令；“没有机械来源”只指没有程序证明语义选择正确，不能理解为完全没有校验或记录。

```sh
rg -n 'ready_by|ready_rev|completion_conditions_sufficiency|mutation_checks|needs-decision|cancel|JSON.stringify\(score|executorScore|scoreData|finalScore|Disposition|disposition' workbench/src/gates workbench/src/daemon.ts scripts/inbox scripts/dispatch --glob '*.ts' --glob 'inbox' --glob 'dispatch'
rg -n 'source\.ready|source\.ticket|ready_rev' workbench/src scripts --glob '*.ts' --glob '*.py' --glob 'inbox'
rg -n 'lifecycleIssue\(|qualityIssue\(|verification_unknown|unknown_result|fail.closed|paused' workbench/src/gates/core.ts
```

| 隐式连接 / 图中位置 | 自行核对的机械边界 | T-081 / T-082 覆盖判断 |
| --- | --- | --- |
| I03 分级与处置，第 340 行 | `core.ts:704` 的 disposeIssue 机械禁止主控关闭 blocking（`:715`），close 要 reason/basis；但不判断自由文本是否涉及权限、范围或不可逆操作，也不判断理由是否充分。执行角色卡 `:13` 把这些语义判断交主控。 | PASS，须保留“有部分机械底线”的限定。T-081 `:18` 起的坏行为不含 triage 语义；T-082 `:18` 是完成条件与变异，`:31` 不保证模型判断正确；不能用两票证明问题处置正确。 |
| I07 何时 verify，第 345 行 | `core.ts:3570` submit 后返回；独立 verify 请求在 `:3573`。显式 run 则确有 `core.ts:2608` 的 submitted/无 repair 条件与 `:2611` 自动 verify。 | PASS：常规人工触发与显式 run 例外区分正确。T-081 `:21` 证明自报通过无效，不保证主控及时调用；T-082 的审查发生在 verify 后，不覆盖其触发时机。 |
| I09 主观打分，第 347 行 | `qualityProtocol.ts:64` 起只验结果、0～3 分与非空理由；`core.ts:2389` 的 finalScore 计算客观事实并记分，没有证明主观理由真实、尺度一致的实现。 | PASS：图没有否认 schema/客观事实检查。T-081 的正负例和 T-082 的审查边界均不保证打分质量。 |
| I10 暂停后选处置，第 348 行 | 质量未知（`core.ts:1683`）、审查协议失败（`:2260`）等机械出口存在；如何在权限内继续、撤销或升级仍靠判断。`core.ts:3379` 会拒绝把 paused 直接当 submitted 重跑，`:3333` 也保护 pending intent；没有统一自动解锁成功路径。 | “后续选择仍靠判断”与两票未覆盖全部人工作法的判断 PASS；连接持久化列的“issue 有记录”NO_GO，见 P2-03。T-081 `:30` 的 CAS 特定样本不覆盖全部未知恢复；T-082 `:21` 保护结束边界，`:31` 排除判断正确性保证。 |

未把 grep 的“无匹配”单独当作全仓库不存在功能的证明；以上均继续打开命令路由、校验实现和角色卡。T-081/T-082 的历史统计没有重跑，覆盖判断只按两票列出的范围和限制成立。

## 4. 第一轮三项回核与新增恢复/暂停路径

| 第一轮问题 | 本候选位置与独立来源 | 本轮结果 |
| --- | --- | --- |
| P2-01 未知结果暂停 | 图新增 Q13（第 187 行）、E65–E67（第 158～160/274～276 行）及第 311/327 行。`core.ts:1679`、`:1680` 为质量串后复核，`:1683` 仅五个已知失败码打回，其余 `:1684` unknown、`:1685` paused、`:1690` 保存、`:1695` 上报、`:1696` verification_unknown，不调 rejectDelivery。 | PASS，按来源补齐。命令错误来源 `core.ts:1230`，未把质量证据不符误算成 worker 打回。 |
| P2-02 审查协议暂停 | 图第 137/253 行限定 E46 为有效需修复，新增 E68（第 161/277 行）、格式码（第 312 行）。`daemon.ts:102` 解析，失败在 `:106` 调 failReviewProtocol；门禁回执失败在 `:135` 调同函数；`core.ts:2271` unknown/paused，`:2274` 保存，`:2275` 上报，不加 delivery_rejected。`qualityProtocol.ts:33`、`core.ts:3735` 支持 invalid_review_result。 | PASS，补齐并区分业务结论与协议失败；已 cancelled 仅记 review_after_termination（`core.ts:2267`），图也保留此例外。 |
| P3-01 model unknown 例外 | 图 Q7 第 188 行及码表第 307 行明确字面量 unknown 例外；`core.ts:2009` 仅在既非 unknown 又不等于交付模型时拒收。`:2001` 仍要求所有必需字段齐全、唯一、非空。 | PASS，没有把例外扩大到 launch/tool/effort 或不完整尾注。 |

另外自行选了第一轮报告未专门抽查的三条路径，而不是仅重走第一轮的 E49/E52/E55/E58：

| 新抽路径 | 来源实际内容 | 与图关系及结论 |
| --- | --- | --- |
| Claim 建 worktree 失败 → paused | `core.ts:1392` 的 Git worktree add 失败，`:1401` task paused，`:1402` attempt worktree_failed，`:1403` 保存，`:1404` 返回 worktree_failed。旧 attempt/current/fence 已由 `:1377` 持久化；重发 claim 会在 `:1340` already_claimed，不能当无事发生直接重试。 | 图 L3/E04 的成功绑定正确，但没有单画 L3→暂停或列此码。这是当前代表性摘录未展开的机械支路；不能把它算入“靠主控判断是否暂停”。此处同样不保证自动 issue。 |
| 后台派发写入结果未知 → pane unknown | `panes.ts:389` 先存 paste_intent，`:390` 写 PTY，`:394` 存 turn_submit_intent；异常在 `:398` 设 pane unknown/failed，`:399` 存 dispatch_unknown。`:379` failed 不 drain，`:405` 的 release 要求无 failed，因此不能盲目 release 重送。 | E05 持久派发、图第 330 行“未知不能凭重发补齐”的方向成立；该行直接引用的是 Herdr `scripts/dispatch:86`，后台这条机械冻结没有单独图边。注意这里是 pane unknown，并不等于 task.paused。 |
| abandon 后未完成 reviewer 的迟到协议结果 | `core.ts:3410` 将 requested/running/unknown review 标 cancelled，`:3416` 保存终结并 `:3418` 上报仍待回收；`failReviewProtocol :2267` 对 cancelled 只记 review_after_termination 并返回，不再把终结 attempt 拉回 paused。 | E64 的终结后仍须回收、第 312 行 cancelled 例外支持成立。不能把这一迟到路径算成 E68 的运行中审查暂停。 |

这些支路的状态与恢复限制均由源码明确规定；“机械暂停/冻结”与“之后如何处置的语义判断”已区分。未把图未展开的所有外围支路都要求补成一个通用执行图。

## 5. 重生成、反例及检查的实际能力

实际运行 `python3 -B findings/generate_t087_graph.py`，捕获 stdout/stderr，在 `/tmp/t087-spot-check-02-bk5ye1rh/regenerated.md` 保存临时输出并与提交文档按 UTF-8 解码后的完整文本直接比较。未计算哈希、校验和或指纹。

可复现的同类命令：

```sh
python3 -B - <<'PY'
from pathlib import Path
import subprocess
p = Path('findings/ticket-gates-graph-2026-10-16.zh-CN.md')
r = subprocess.run(['python3', '-B', 'findings/generate_t087_graph.py'],
                   text=True, capture_output=True, check=True)
assert r.stdout == p.read_text(encoding='utf-8')
print(len(r.stdout.splitlines()), repr(r.stderr))
PY
python3 -B findings/generate_t087_graph.py --check findings/ticket-gates-graph-2026-10-16.zh-CN.md
```

实际结果：生成退出 0、stderr 为空；提交与生成均 **594 行，全文一致**。`--check` 退出 0，返回 35 个点、68 条连接、221 行来源索引、546 次来源使用；它明确表示未执行 semantic_audit。这些数字来自此次命令，不是作者报告。

在同一临时目录构造 3 个文档级错误实现，逐个运行 `python3 -B findings/generate_t087_graph.py --check <反例绝对路径>`，另与刚生成的原文比较：

| 变异 | 具体改动 | `--check` 实际结果 | 文本比较及独立 oracle |
| --- | --- | --- | --- |
| M1-protocol-to-rejection | 将 Mermaid 的 E68 终点 R2 改 R1，同步连接表 Q8→R2 为 Q8→R1，保留引用。 | 退出 0。 | 与重生成文本不同，被文本比较拒绝；`core.ts:2271`/`:2274` 是 unknown/paused，不调用 rejectDelivery，来源语义也拒绝该变异。 |
| M2-cas-limit-three | 将图与连接表 E56 的 misses≥4 同步改为 misses≥3。 | 退出 0。 | 文本不同，被比较拒绝；`core.ts:1736`/`:1741` 明确阈值为 4，独立来源拒绝该变异。 |
| M3-model-no-exception | 把 Q7 和码表的 model unknown 例外改成 unknown 也必须等于交付模型。 | 退出 0。 | 文本不同，被比较拒绝；`core.ts:2009` 的双重不等条件拒绝该变异。 |

这证明引用/ID 检查本身不能证明语义；文本比较能发现单独改坏生成物，但若生成脚本与文档一起写错，仍可能一致。此次 P2-03 正是文本一致而来源不支持的例子。T-087 把独立来源抽查列入完成条件，因此没有将 `--check` 单独视为最终验收，也不把其有限能力另报为新产品缺陷。

三份反例和生成临时文件随 TemporaryDirectory 清理，最终读回 `exists=False`。未在候选或共享 checkout 做变异；未运行产品测试、服务、真实 CLI/模型、图形渲染或 T-081/T-082 全套回归。这些未做项不宣称 PASS。

## 6. 术语与收尾

术语检查结果：**PASS**。图第 9～11 行和类别表继续使用确定性步骤/门禁检查、agent 会话、人工决定点；task/attempt、Claim/Submit/Acceptance/Integration 均可追溯到 CONTEXT。生成脚本 `point`/`edge`、`points`/`edges` 是图表构造与编号变量，没有新增持久业务对象、公开执行 API 或新的业务总称；文档“点/连接”也没有定义成跨产品领域术语。不将这些普通作图用语扩大解释为已完成“节点/边”的术语决定。`Graph Engineering` 未写入 CONTEXT，图未驱动派发。

开始和写报告前实际运行：

```sh
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
git rev-parse HEAD
git branch --show-current
git status --short
```

本次地图检查均退出 0：`Problems (0)`、`Stale living docs (0)`。报告回读确认 UTF-8 无 BOM、LF、无替换字符，末行标记正确；临时目录不存在。冻结 HEAD 与 `exec/t087` 相符。唯一新增文件为本报告；未改图、生成脚本、产品、票据、地图或全局配置，未 commit/checkout/reset，未调模型 API、发送外部消息或请求沙箱升级。

最终结论：**NO_GO**。第一轮三项已补正；本轮仍须修正 P2-03 对恢复分支持久记录的过强保证。其他列明抽查项通过不替这处来源差异背书。

T-087 SPOT-CHECK 02 DONE
