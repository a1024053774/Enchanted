# T-087 独立来源抽查 01

结论：**NO_GO**。冻结图的成功主串顺序正确，重生成文本一致；恢复图漏了两类已实现的暂停路径，另有一处尾注规则描述过强。需修改生成脚本和文档后再审。本结论针对图文档，不是对产品门禁运行结果的判定。

- 审查日期：2026-10-16。
- 仓库：`/Users/luckye/Documents/Code/a2a-wt-t087`。
- 冻结候选：`aba81b52ca5e91aaafd44b15b5bf4b4c0ad8b3c4`；开始与结束写报告前的 `git rev-parse HEAD` 均一致，工作区均干净。
- 对象：`findings/ticket-gates-graph-2026-10-16.zh-CN.md` 与 `findings/generate_t087_graph.py`。
- 已读指定的共享 checkout reviewer 角色卡、本 checkout 的 T-087、MAP、CONTEXT 和 intent；未读作图会话历史，也未读取作者的 RESULTS、生成日志、反例报告等证据正文。下述来源均自行打开并检查上下文。
- 目标：核对门禁顺序与拒收码、其他连接的语义、隐式边及两票覆盖、再生成一致性和术语。非目标：改产品、修图、运行服务/模型、复验 T-081/T-082 的历史通过结论。
- 证据方式：源码静态分析、只读命令、文档级反例。没有把“引用存在”当成“引用支持”。本次没有门禁提供的一次性候选副本，未做产品代码变异；文档反例仅在新建 `/tmp` 目录中构造并已删除。

## 按严重度列出的问题

### P2-01：红态、规则和质量证据核对的未知结果出口缺失

**图中位置**：文档第 130–133 行仅有 Q5/Q6 → R1 的已知失败连接；第 148 行及第 258 行的 E60 只画 Q4 → R2。第 91–94 行的主串及第 229–231 行的连接表也未说明红态、规则之后还有一次质量证据核对。

**来源实际内容**：

- `workbench/src/gates/core.ts:1679` 调 `checkQuality`，`:1680` 随即调 `checkQualityEvidence`。
- `core.ts:1683` 只把 `red_state_failed`、`red_test_file_invalid`、`red_test_not_changed`、`red_test_symlink`、`rule_check_failed` 归入已知质量失败。
- 其余错误走 `core.ts:1684` 的 `v.state="unknown"`、`:1685` 的 `task.state="paused"`，在 `:1690` 保存结果，`:1695` 上报，`:1696` 对外变成 `verification_unknown`，不走 `rejectDelivery`。
- 红态和规则命令都经 `qualityCommand` → `execute`（`core.ts:1909`、`:1952`、`:1963`）。例如命令无法启动或超时会在 `core.ts:1230` 产生 `command_unavailable`/`command_timeout`，随后走上述未知分支。`checkQualityEvidence` 的 `quality_reverification_required`（`core.ts:1981`）在这里也走未知分支。

**影响**：按恢复图追查一次红态或规则命令未知结果时，没有来源到 R2；还可能把它误读成会增加打回次数的 worker 交付失败。文档第 293 行虽然泛称“未知结果暂停”，没有补齐实际连接和质量证据核对的位置。

**最小修正**：补 Q5/Q6 及质量证据核对到 R2 的 `verification_unknown` 路径，标明未知结果不增加 `delivery_rejected` 计数；把 `checkQualityEvidence` 放在红态/规则之后、提交尾注之前的说明中。无需改产品。

### P2-02：审查协议失败的机械暂停路径没有画出

**图中位置**：第 134 行、第 244 行 E46 把 Q8 的出口笼统写成“已知失败 / 需修复”→ R1；第 153 行、第 263 行 E63 只有创建失败或重启无法接管。第 296 行的审查协议拒收码表也没有 `invalid_review_result`。

**来源实际内容**：

- 有效业务结论“需修复”才在 `core.ts:3459` 设 `needs_fix`，并在 `:3462` 调 `rejectDelivery(..., "independent_review", ...)`。这支持 E46 的“需修复”部分。
- 格式错误是另一条路。`workbench/src/gates/qualityProtocol.ts:33` 的 `reviewEvidence` 检查容器、固定要求和报告节；`core.ts:3735` 将其错误映射为 `invalid_review_result`。
- 真实 Stop 信号入口 `workbench/src/daemon.ts:102` 先解析 reviewer 最后消息。解析失败在 `:106` 调 `failReviewProtocol`；转交到门禁后若回执失败，在 `daemon.ts:135` 同样调用它。
- `core.ts:2271` 明确设 `review.state="unknown"`、`task.state="paused"`；`:2274` 保存 `review_protocol_failed`；`:2275` 上报“审查结论协议无效，已停止”。该函数没有调用 `rejectDelivery`。

**影响**：无效报告、身份/候选等协议拒收，与 reviewer 正常判“需修复”的后续处置和计数不同。现有 E63 的创建/重启条件以及 Q9 的结束核对失败均不能代替这条路径。这也是仅检查 `core.ts` 中已选锚点会漏掉的直接调用方。

**最小修正**：增加审查协议失败 → R2 的连接，引用 `daemon.ts:102`、`:135` 和 `core.ts:2260`；将 E46 限定为有效的“需修复”业务结论，并补 `invalid_review_result` 的格式错误说明。

### P3-01：提交尾注的 model 匹配描述遗漏 `unknown` 例外

**图中位置**：第 180 行 Q7 写“完整匹配……交付 launch/tool/model/effort”；生成脚本对应 `findings/generate_t087_graph.py:231`。

**来源实际内容**：`core.ts:2009` 的条件是 `trailers.model[0] !== "unknown" && trailers.model[0] !== attempt.delivery.model` 才产生 `trailer_identity_mismatch`。因此 model 尾注为字面量 `unknown` 时，不要求与已知交付模型相等。其他必需尾注仍须存在且非空（`core.ts:1985`、`:2001`）。

**影响与修正**：图比实际规则更严格，容易对 model=unknown 的交付产生错误预期。明确这个例外即可；不建议借本票改变门禁契约。

## 1. 从源码独立读出的顺序与拒收码

以下是本次所读业务检查及关键分支，不是所有 Schema、文件系统、进程和 Git 底层错误的穷举。先读源码，再对照图；主串由 `verifyCandidate` 的实际调用次序确定。

| 实际阶段 | 来源与实际顺序/拒收码 | 与图对照 |
| --- | --- | --- |
| 公共操作锁 | `core.ts:3127` 进入操作锁；锁在 `core.ts:238`，占用时报 `operation_busy`（`:250`） | 文档第 289 行正确；锁释放不证明验收通过 |
| Claim | `core.ts:1333`：检查 ready/无当前 attempt → 全局路径预留锁 → 路径交集 → 读取集成起点 → 验收文件存在性 → 写快照/attempt/session/fence/intent → 建工作区/会话。业务码有 `already_claimed`（`:1340`）、`path_overlap`（`:1082`）、`oracle_not_found`（`:1879`）、`worktree_failed`（`:1404`）；dispatch 另要求 runtime/runtimeMode | L3、E04/E05 的顺序支持成立。图列出 oracle_not_found；其余 Claim 码未列 |
| Submit 身份 | `core.ts:3466` 起依次检查 attempt、session、fence、spec、thread/实时身份、turn。对应 `stale_attempt`、`stale_session`、`stale_fence`、`stale_spec`、`stale_thread`、`identity_conflict`、`stale_turn` | Q0 和第 290 行正确 |
| Submit 候选 | `core.ts:3491` 起检查返工交付状态、task.state、候选冲突、commit 存在/祖先关系、返工基线、HEAD、干净工作区、修复须新 C、交付事实；成功到 `core.ts:3570` 的 submitted。关键码含 `conflict_delivery_unconfirmed`、`invalid_state`、`candidate_conflict`、`invalid_commit`、`not_descendant`、`rework_baseline_changed`、`conflict_candidate_unchanged`、`workspace_head_mismatch`、`dirty_worktree`、`repair_requires_new_candidate`、`delivery_facts_required`、`delivery_facts_unknown` | 图已列主要身份/候选码；这里列出的返工/状态/交付事实缺失码并未全部列出，不能把第 290 行当完整接口表 |
| verify 前置与构造 M | `core.ts:3376` 拒绝未完成冲突返工（`conflict_rework_required`）；`:3379` 要求 submitted/verifying。`core.ts:1519` 保留中断验证，随后依次检查 repair、submitted、无旧 integration intent、质量快照，再取 G/C 并构造 M。码含 `quality_rejection_limit`、`repair_submission_required`、`not_submitted`、`needs_reconciliation`、`project_quality_snapshot_required`、`rework_baseline_changed`、`merge_conflict`（`:1614`） | Q1/E20 的合并在路径检查之前，正确。图未列前述部分前置码 |
| 路径边界 | `core.ts:1629` → `:1858`，检查候选差异与 G→M 差异；`path_boundary_failed`（`:1867`） | Q2/E20–E21、E40 正确 |
| 验收文件保护 | 紧接着 `core.ts:1631` → `:1881`；认领起点保持冻结，差异命中 oracle_paths 则 `oracle_modified`（`:1893`） | Q3/E21–E22、E41 正确 |
| 完成条件 | `core.ts:1644` 按 argv 顺序执行，第一项非零即停止；最终 `oracle_failed`（`:1715`）并打回。命令结果未知则 `verification_unknown`（`:1674`）并 paused | Q4/E22–E23、E42/E60 正确 |
| 红态 | 完成条件全过后 `core.ts:1679` 调质量串；`core.ts:1921` 起先验证测试清单，再运行起点加测试与候选。码为 `red_test_file_invalid`、`red_test_not_changed`、`red_test_symlink`、`red_state_failed`；无配置记 red_not_applicable（`:1961`） | Q5 位置正确，已知失败 E43 正确；未知出口遗漏，见 P2-01 |
| 规则式检查与质量证据 | 红态循环之后 `core.ts:1962` 才运行规则，非零 `rule_check_failed`（`:1967`），无规则记 rules_not_applicable。返回后 `core.ts:1680` 核对质量证据，内部码 `quality_reverification_required`（`:1981`）；在 verify 内被转换成 verification_unknown，在 integrate 的直接复核中可原样返回 | Q6 的红态后顺序正确；质量证据复核与未知出口需补说明 |
| 提交尾注 | `core.ts:1698` 在质量串之后调用；`:2000` 起依次决定 `trailer_task_mismatch`、`invalid_trailers`、`trailer_identity_mismatch`、`trailer_launch_record_missing`。全无尾注在 `:2017` 记人工介入，不拒收 | Q7/E25 位置正确，所列码正确；model 例外见 P3-01 |
| 请求独立审查 | `core.ts:1717` 在上述串通过后调用 requestReview。新请求 `core.ts:2227` 先持久，后建目录和启动；启动边界核对可报 `review_launch_boundary`。同一 C 的已结束有效审查可以在 `core.ts:2206` 复用 | E26 正确；E55 的复用例外与主串须一起读，不能理解成每次 CAS 重验都新开 reviewer |
| 审查结果协议 | `core.ts:3424` 起检查 reviewer、attempt/session/fence/spec、C、verification、质量证据、实时身份、独立性、未续接及报告。码含 `reviewer_required`、`stale_review`、`review_candidate_mismatch`、`review_verification_mismatch`、`review_identity_unknown`、`review_writer_conflict`、`review_native_session_reused`、`review_requirements_mismatch`；格式错误为 `invalid_review_result`（`:3735`） | Q8 的绑定次序支持成立；review_identity_unknown、invalid_review_result 未列。业务需修复与协议失败必须分开，见 P2-02 |
| 审查结束核对 | `core.ts:2281`：要求 review_result/runtime → 读实时身份及 idle → stop/archive 后读回 → 核对副本/共享 refs/审查及 worker 工作区 → 清理 → 写 review_reclaimed。码含 `review_result_required`、`reviewer_not_idle`、`review_reclaim_unconfirmed`、`review_candidate_copy_missing`、`review_candidate_copy_identity_unknown`、`review_shared_refs_changed`、`review_worktree_changed`、`review_worker_workspace_changed`，以及清理阶段错误 | Q9/E30 正确；第 295 行只是其中代表码 |
| integrate | `core.ts:3575` 先读评分格式；`:3585` 起复核 verified、verification、质量证据、有效审查及结束记录、交付评分来源、重放评分，才读当前集成引用。无旧意图且引用变化时重验；否则先保存 intent（`:3656`），再 CAS（`:1815`、`:1827`），读回内容后 accepted/打分（`:3671` 起） | Q10/Q11/E31 作为正常工作流程支持成立。实际 integrate 内评分格式校验先于其余复核，图没有穷举每个内部谓词次序。码含 `score_required`、`invalid_score`、`score_provenance_required`、`attempt_already_scored`、`not_verified`、`stale_verification`、`review_required`、`stale_review`、`review_end_check_required`、`score_replay_mismatch`、`integration_compare_failed`、`integration_revalidation_limit`、`needs_reconciliation`；另有集成工作区/快进校验码 |
| reclaim/cleanup | `core.ts:3698` 先拒绝未解决集成意图，再核对绑定、身份、外部状态、blocked、idle，持久回收意图，stop/archive 读回，保存 reclaimed，最后 cleanup。主要码为 `needs_reconciliation`、`no_bound_thread`、`identity_conflict`、`run_external_unknown`、`run_blocked`、`worker_working`、`stop_unconfirmed`、`reclaim_unconfirmed`；清理异常保留目录并上报（`core.ts:1092`） | Q12/E32 的顺序和保存边界支持成立；仅 worker_working 不足以代表全部回收拒收原因 |

逐项汇总：

- **缺的**：P2-01 的质量未知出口、P2-02 的审查协议失败出口；部分业务拒收码见上表。并非所有未列码都单独构成阻断缺陷，原文第 285 行已声明其码表只是代表集。
- **多的**：未发现完全没有来源的成功主串检查或虚构拒收码。E46 的“需修复”有来源，但“已知失败”若覆盖协议拒收，则范围过宽。
- **顺序错的**：未发现成功主串的顺序颠倒。实际是路径 → 验收文件 → 完成条件 → 红态 → 规则 → 质量证据复核 → 提交尾注 → 请求审查；不能沿用较早规格中把独立审查放在尾注之前的文字顺序。
- **拒收码错的**：已展示的码字面量未发现拼错或虚构。需要修正的是拒收之后的路由与部分条件说明，不是把真实源码码改名。

## 2. 其他连接的语义抽查（15 条）

以下不以链接可打开为结论；每项都读取了所引函数、规则或条目上下文。表中行号均指冻结候选。

| 类别 / 连接及图中位置 | 打开的来源与实际支持内容 | 判定 |
| --- | --- | --- |
| ticket 字段 E02，第 204 行 | `scripts/inbox:334` 的 ready 只读票据；`:346` 排除非 open；`:351` 检查字段齐全；`:357` 限定 ready=yes、ready_by=ideation/executor、正 ready_rev；`:364` 排除类型不符/已认领；`:366` 逐一读依赖状态 closed/superseded。规格 `.project-map/specs/controller-split-user-input-2026-10-09.md:249` 同样要求 | PASS，支持 blocked_by、ready、ready_by 的筛选连接，不支持自动授权含义判断 |
| ticket 字段 E16，第 223 行 | 同一函数的 continue/diagnostics 分支，尤其 `scripts/inbox:355`、`:358`、`:364`、`:366`。实际样本 T-080 的 `:5` 为 closed、`:6` 依赖 T-077、`:9` 仍为 ready=yes；T-077 的 `:5` 为 closed | PASS，closed 即使保留 ready 也不会进入当前可执行列表；依赖允许 superseded，不要求一律 closed |
| 收件箱 E03，第 205 行 | 规格 `:257` 明确 assign 方向与本批 refs；`.project-map/inbox/20261016T082147Z-ideation-assign-001.md:2`–`:6` 是 ideation→executor、assign、ticket:T-087；`:13` 记 ready_rev。`scripts/inbox:149` 实现追加发布 | PASS，支持本批实际交接；ready 筛选器自身未发 assign，也未建后台 task |
| 收件箱 E11，第 215 行 | 规格 `:265` 指明构思主控逐字转录 answer、refs 带 issue/worker、交执行主控；`.project-map/roles/executor.md:14` 规定投递后 delivered/ack | PASS，支持原文转述与后续确认，ack 不能替代业务验收 |
| 收件箱 E12，第 216 行 | executor 角色卡 `:14` 明确经 scripts/dispatch 原样发给 refs 内 worker；结束会话改 forward(session-ended)。`scripts/dispatch:51` 读正文，`:61` 加来源标记、首次附角色卡，`:70` 起记派发记录 | PASS，“原文”指正文内容；传输仍有已规定的标记与首次角色卡，并非字节串完全无包装 |
| 收件箱 E13，第 219 行 | 规格 `:292` 规定下一工具轮次执行 stop 并 ack；`:293` 限制 2 分钟 break-glass 且用户仍要求；executor 卡 `:15` 一致 | PASS，支持条件与方向，不等于构思主控拥有常设回收权限 |
| 收件箱 E14，第 220 行 | `scripts/inbox:217` 检查 ack 由原收件人发给原发送人，`:221` 禁止 ack 再 ack，`:223` 重放已确认不重复写；规格 `:266` 为收到/执行确认 | PASS，支持确认终结，不支持“已验收”的含义 |
| 恢复 E49，第 247 行 | `core.ts:1519` 重进 verify 先调用 interruptVerification；`:1295` 只处理中断时仍为 verifying 的记录；`:1298` 检查 running 且无集成意图，`:1299` 旧记录 interrupted，缺结果保持 unknown，`:1311` 持久 | PASS，支持中断后重验；不能据此直接重跑已经 paused 的未知结果，后者会被 `core.ts:3379` 拒绝 |
| 恢复 E52，第 250 行 | `core.ts:3594`–`:3610` 核对原意图全部绑定及 actual=G/M；`:3613` 的 M 分支核对内容、补 integrated_reconciled/打分后返回；G 分支继续原意图到 CAS | PASS，支持 G 继续、M 补账，且不会在 M 分支再做同一次 Git 更新 |
| 恢复 E55，第 253 行 | `core.ts:1727` 判断同 C/卡/spec 的 misses 连续计数，`:1736` 第四次暂停；前三次 `:1748` 重新 verify。`core.ts:2206` 的复用还须 requireReviewed，后者 `:2160`–`:2172` 验身份/版本/C/结束记录 | PASS，支持受限复用；没有复用旧机械检查通过结果 |
| 恢复 E58，第 256 行 | `core.ts:1468` 检测 stopped/session_ended；`:1472`–`:1489` 停止/归档读回、reclaimed、撤销与清理，再走同一 claim；否则 `:1498` 给原 worker 送冲突信息。`:3563` 记录新候选需要 fresh review | PASS，支持原 worker 与替换 attempt 两条路径；不是直接接管旧身份 |
| 持久化 E04，第 207 行 | `core.ts:3186` 起 create 验卡与仓库；claim 中 `:1351`–`:1377` 生成 attempt/session/fence、快照并保存 intent；随后 `:1392` 才建工作区。`core.ts:985`–`:1019` 同事务保存状态与事件 | PASS，支持先持久绑定再外部建工作区；不意味着 ticket 文件与 SQLite 原子联动 |
| 持久化 E05，第 208 行 | `core.ts:1435` 记录 prompt intent，`:1437` 启动、`:1441` 保存 dispatched。`workbench/src/store.ts:9`–`:16` 同库有 launch/dispatch/events 表及防 UPDATE/DELETE 触发器。Herdr 入口 `scripts/launch-worker:61`、`:73` 先保存 prepared 启动记录；`scripts/dispatch:53`、`:70` 保存另一份派发日志 | PASS，支持两个载体分别记录；没有把 Herdr 文件说成后台数据库行 |
| 持久化 E31，第 236 行 | `core.ts:3633`–`:3656` 的 integration_intent 保存 G/C/M、verification、attempt clone、spec、卡快照、集成 ref、score；然后 `:3659` 才执行分支更新；CAS prepare/commit 分别在 `:1815`、`:1827` | PASS，支持 SQLite intent 先于 Git 副作用；两者不是同一事务 |
| 持久化 E47，第 245 行 | `core.ts:2053` 按原 attempt 统计打回次数，`:2061` 先保存 delivery_rejected；`:2070` 再确认原 attempt。`panes.ts:356` 验 attempt/session/fence/launch，`:365` 反馈经 dispatch，`:372` 先登记再入队；停止反馈分支 `:359`–`:363` 取消质量返工队列并留事件 | PASS，支持少于三次的原 attempt 回写；反馈成功不等于新交付已验收 |

覆盖计数：ticket 字段 2 条，收件箱 5 条，恢复 4 条，持久化 4 条；共 15 条，四类均不少于 2 条。

## 3. 隐式边独立抽查（4 条）

这里的“没有机械来源”按图第 318 行的限定解释：没有机械保证该语义判断正确，不是没有任何脚本或记录。四项都自行检索实现路径；没有把“搜不到一个关键词”当作全仓库不存在功能的证明。

检索命令（只读）：

```sh
rg -n 'cancel|revoke|ready_by|ready_rev|## 授权|用户原话' scripts/inbox workbench/src/gates/taskCards.ts workbench/src/gates/core.ts
rg -n 'completion_conditions|sufficiency|mutation_checks|reviewEvidence|invalid_review_result' workbench/src/gates/taskCards.ts workbench/src/gates/qualityProtocol.ts workbench/src/gates/core.ts
rg -n 'ready_by|ready_rev|授权引用|completion_conditions_sufficiency|mutation_checks|failReviewProtocol|kind === "cancel"|kind == "cancel"' workbench/src scripts --glob '*.ts' --glob 'inbox' --glob 'dispatch' --glob 'launch-worker'
```

| 隐式边 / 图中位置 | 自行检索后核对的机械边界 | T-081 / T-082 覆盖判断 |
| --- | --- | --- |
| I01 授权是否覆盖再标 ready，第 322 行 | `scripts/inbox:357` 只验字段；`taskCards.ts:104`–`:107` 只要求 ready=yes/正 rev，`:128` 只比版本。构思卡 `:8` 要求“用户已决定”；交接规格 `:287` 要求授权原话。所读执行路径没有判断原话是否足以授权的实现 | PASS。T-081 的样本范围是列明坏行为/正确交付（该票 `:18`–`:31`），不证明用户授权含义；T-082 的 `:16`–`:22` 是完成条件审查及副本边界，也不覆盖授权语义 |
| I02 拆卡与完成条件，第 323 行 | `taskCards.ts:151`–`:156` 只验命令数组非空/argv 等格式；`core.ts:1644` 只执行给定命令。executor 卡 `:9` 负责写卡。无从用户目标自动判定卡是否遗漏目标的校验 | PASS。T-081 对已列进卡的越界、改验收文件、自报通过、正例误拒有证据范围（票 `:20`–`:31`、`:48`）；不能推出卡覆盖用户目标。T-082 `:18` 直接增加充分性审查及 2～5 个变异，`:31` 明确不保证 reviewer 判断正确 |
| I05 cancel 到结束实际执行，第 326 行 | `scripts/inbox` 的 cancel 只在 KINDS 中；后台 `core.ts:2892`–`:2901` 给 cancel 验方向，后续保存/投递条目；真正撤销身份是独立 revoke/revise 分支 `core.ts:3331` → invalidate `:1313`。未发现 cancel 条目自动调用 invalidate 的连接 | PASS。T-081 旧 attempt 拒收样本（票 `:22`）不是 cancel→revoke 路由；T-082 的审查取消/生命周期保护不是用户取消任务的决策。两票“不覆盖”判断成立 |
| I08 reviewer 判断完成条件/变异是否足够，第 330 行 | `qualityProtocol.ts:31` 注释与 `:33`–`:42` 实现一致：只验布尔要求、2/5、workspace/报告节及容器；不会运行报告所称的变异或判定其语义。`core.ts:3454` 另验副本绑定；机械路径存在，但不证明判断正确 | PASS。T-082 `:31` 明文把判断正确排除出门禁条件，`:43`–`:44` 只记录该日期两次真实回合和边界。T-081 `:48` 的坏行为/正例不是任意 reviewer 判断正确的证明 |

覆盖判断只对照两票的要求与 Resolution 范围，不读取其作者证据报告、不继承历史 PASS 为本图背书，也没有重跑这些实验。T-081 的能力限制仍按该票 `:49` 保留。

## 4. 重生成、反例与完成条件充分性

实际执行了 `python3 -B findings/generate_t087_graph.py`，在 Python 包装中捕获 stdout/stderr，再与提交文档按解码后的完整文本直接比较；未计算哈希。

可复现的同类文本检查命令：

```sh
python3 -B - <<'PY'
from pathlib import Path
import subprocess
p = Path('findings/ticket-gates-graph-2026-10-16.zh-CN.md')
r = subprocess.run(['python3', '-B', 'findings/generate_t087_graph.py'], text=True, capture_output=True, check=True)
assert r.stdout == p.read_text(encoding='utf-8')
print(len(r.stdout.splitlines()), '行；文本完全一致；stderr=', repr(r.stderr))
PY
python3 -B findings/generate_t087_graph.py --check findings/ticket-gates-graph-2026-10-16.zh-CN.md
```

已取得的读回：生成退出码 0、stderr 为空；提交与生成均 564 行，完整文本相等。原文 `--check` 退出码 0，返回 34 个点、63 条连接、207 行来源索引、477 次来源使用；其输出明确写 `semantic_audit` 未执行。第一次包装调用未取回完整 stdout，已用可读回的执行重新取得上述结果；未把缺失输出当通过证据。

为检验检查范围，在 `/tmp/t087-source-spot-check-x6n5djxt` 构造 3 个文档反例，调用同一脚本的 `--check <临时文档绝对路径>`；候选源码与文档均未改：

| 反例 | 修改 | 引用/ID 检查的实际结果 | 与重新生成文本比较 / 独立来源判定 |
| --- | --- | --- | --- |
| M1 | 在 Mermaid 和连接表同步将 E23/E24/E25 改成完成条件→规则→红态→尾注，保留 ID 和引用 | 退出码 0，仍称引用/ID PASS | 文本不同，被比较拒绝；源码 `core.ts:1921`、`:1962` 独立证明这个顺序错误 |
| M2 | 删除整条“交付身份/候选”拒收码表行，保留来源索引 | 退出码 0，仍称引用/ID PASS；来源使用数降为 464 | 文本不同，被比较拒绝；`core.ts:3466` 起的真实拒收检查仍存在，删除属于遗漏 |
| M3 | 把 L1 说明中的“依赖 closed/superseded”改成“依赖 open” | 退出码 0，仍称引用/ID PASS | 文本不同，被比较拒绝；`scripts/inbox:366` 独立证明依赖条件错误 |

临时目录最终读回 `exists=False`，三份反例已删除。此类对比能抓改坏生成物，但若作者同时改错脚本和生成文档，文本一致性本身不能发现语义错；必须保留 T-087 要求的独立来源审查。`--check` 本来就明示只验引用/ID，因此上述 3 个 PASS 不单独作为新增产品缺陷；本次真正拒绝候选的证据是前述源码差异。

未执行门禁提供副本中的产品变异、真实 CLI/模型/服务运行、图形渲染或 T-081/T-082 全套回归；本次授权是来源抽查和文本比较，不宣称完成了那些验证。

## 5. 术语与收尾

未发现新增业务总称或执行器。三类仍是确定性步骤/门禁检查、agent 会话、人工决定点；Claim、Submit、Acceptance、Integration、task/attempt 均在现有 CONTEXT 中。生成脚本内部 `points`/`edges` 与文档“点/连接”用于图形编号和表格，并未宣称为新的业务对象；本次不将其视为新增统一术语。“Graph Engineering”没有写入 CONTEXT，也没有把图变成执行规则。需要纠正的 Q7 规则描述见 P3-01。

开始及写报告前均运行：

```sh
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
git rev-parse HEAD
git status --short
```

两次 project-map 均退出 0，`Problems (0)`、`Stale living docs (0)`。冻结 HEAD 未变化。只创建本报告；未修改图、生成脚本、产品、票据、地图或全局配置，未执行 Git 写操作、发消息或请求沙箱升级。

最终结论仍为 **NO_GO**：两项 P2 是已有机械路径在图中的遗漏/混淆，一项 P3 是规则例外遗漏。其余抽查范围有来源支持，不能据此把整份候选上调为 PASS。

T-087 SPOT-CHECK DONE
