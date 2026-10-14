# T-077 独立只读审查

STATUS: INCOMPLETE

TARGET:

- 产品：`5d0bf1e84c02fbcb4b7699cdd9a48c4f6582c6b4`
- 夹具：`be91b3c047195e23fff0e1d6fd68e82ab63bf72f`
- base：`5e057109e15fba82b89582ad54bab410433be89e`
- 审查 HEAD：`abab4b785899fb1790a2c2cc8120ba93af726a61`。开始及末次只读核对均相同；夹具版本至 HEAD 的 `workbench/src`、`workbench/tests`、`acceptance`、`workbench/README.md` 无差异，以上工作区文件也无未提交差异。

确认发现 1 项，属于反事实验收证据缺口。候选的三条联合路径、四条审查目录生命周期路径及保存的回归均有受控入口通过证据；没有确认产品代码违反这些路径的发现。但冲突反事实第 6、7 条均在重交前置条件失败，未命中各自的路径、尾注断言，因此不将本次审查上调为 PASS。

以下 `E/` 统一指 `evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/`。文件行号指上述冻结版本。本次只读取任务文件白名单、Git 与原始证据；没有运行新测试、模型、后台、PTY、进程观察或信号操作，没有修复或提交。

## EVIDENCE

### (a) T-076 质量串与 T-077 的合流

预期独立取自 T-077 What to build / Acceptance、T-076 What to build，以及 spec 第 3、4、8 节：机械检查必须重跑，审查绑定完整候选身份，同 C 可复用，新 C 必须新审查；未知结果暂停；第四次连续失配停止自动重验。

产品的 `core.ts` 把原验收串移入 `verifyCandidate`，公开 verify 和 R8 都调用它。`requireReviewed` 继续核对 task、attempt、session、fence、spec、卡快照及 C，并将当前 review 与持久化 `review_result` 作完整比较。`requestReview` 仅在已通过且 C 相同时进入该核对并复用；新 C 走新的 reviewer。质量未知仍为 `verification_unknown` / paused，review 创建、协议、重启、回收未知仍有原暂停与上报路径。

三条组合路径的 `joint-proof.json`、`database-readback.json`、`git-readback.json` 相互一致：

| 场景与原始目录 | 关键读回 |
| --- | --- |
| `E/joint-candidate/same_candidate_reuses_review/` | C=`645db732499ee858a122d29fb3fe4d59e3ab8b63`；新 G=`58b09d8d7b19ea8ee4abe5739879aa44d1e03ef2`；main/M=`188df65ef4afa21e3fdcc139ec8e506f015228a2`。SQLite 为 accepted、2 次 verification、1 次 review_result、1 次 review_reused；同一 review id=`7b1ddc7f-4327-4061-bc3c-52a5061fce7f`。完成条件与规则记录分别读取 base host、external G；Git 状态为空。 |
| `E/joint-candidate/changed_candidate_starts_fresh_review/` | C1=`9c5ad89c5bffe59d36859d85a4706f86833c4a22`，C2=`6e58bf423f08649b41a37f1f360cf5f0f7e1ae21`；新 G 上 C1 完成条件失败后修复。两个不同 review id、session、launch、native，分别绑定 C1/C2；无 review_reused；main/M=`d290cd4b525779297f8d18aacd201479a2726f26`，accepted，唯一 score_recorded。 |
| `E/joint-candidate/conflict_then_quality_repair_submits_again/` | C1=`e6f9d05abb42bacfe3895c3173b98f4252170d04` 文本冲突；C2=`7fc4a907f15dfaabdee72729df0710686433ec7f` 显式重交后完成条件失败；C3=`674090b300a7289ceaf858478e91a142fd375b1a` 再交、重验、新审查并集成，main=C3。始终为 attempt=`7981d36d-4583-42a9-b271-56d86f0d395a`；rework.base_commit 始终为 G=`a8b501fe9812a9b575f92de65c47508a81f84e6c`；原 claim base 为另一独立值。完成条件两次 `[false,true]`，path_check 两次，review_result 一次，score_recorded 一次。 |

这些不是仅有计数：同 C 的库事件次序为 review_result #89 → 目录删除 #104 → review_reclaimed #105 → compare_failed #110 → 新 completion_check #137 → review_reused #163 → integrated #202；冲突组合为 conflict_rework_submitted #109 → 完成条件失败 #133 → delivery_rejected #147 → 再交 #162 → 完成条件通过 #186 → 新审查 #214/#220 → integrated #275。

R8 原始 SQLite 导出保存在 `E/s3-all/fixtures.tar.gz` 的 `s3-60xwa278/c-6tjnwg47/s3-state-readback.json.gz`：原 attempt=`a280eab0-876c-446d-8b88-91ef0073089f`，最终 paused、misses=4；compare_failed 的 seq 为 #105/#160/#215/#270，misses 依次 1/2/3/4，4 个 verification、4 个 completion_check、1 个 review_result、3 个 review_reused，#271 产生绑定原 attempt 的 issue；没有 integrated。`E/s3-all/11-test_r8_stops_at_fourth_cas_miss/result.json` 和原测试还核对：只发生初验加三次重验，重复 integrate 不增加写入或 issue。前三次失配与第四次停止没有被同一计数标签混淆。

`E/t076-final-tracer/` 13 案、`t076-final-wide/` 15 案、`t076-final-review-faults/` 3 案、`t076-final-controls/` 8 案、`t076-final-provenance/` 2 案的子案均 passed，cleanup_failures 均为空。未知 review 创建、后台重启、回收场景分别命中其暂停断言。此处是新候选的受控本地依赖验证，不引用 T-076 旧审查的 PASS 替代它。

### (b) 两处新增衔接

- **worker 名额**：`workbench/src/panes.ts:114` 的计数集合先过滤 `record.role === "worker"`，只要求这些 worker 全部 stopped 且 archived；reviewer 不在集合内。`E/panes.json` 的 archived/live worker 名额、原生记录归属、领导者替换和反馈队列四案均通过，进程读数明确为受控输入；`E/relay-conflict/` 还经真实 CLI/Panes/relay/门禁创建 fence=2 的新 worker。保存的名额单测未单独制造“仍活跃 reviewer 加新 worker”组合，因此该具体组合的结论依据是直接代码条件，不冒称已有独立运行。
- **质量打回后的 rework 基线**：`core.ts:3313` 识别同一 rework 候选的质量修复，`core.ts:3327` 从门禁保存的 `attempt.rework.base_commit` 读取基线并检查祖先关系；只有首次冲突整理可从真实 integration ref 延长该基线，worker 没有输入基线的参数。上述冲突组合的 C2→C3 读回证明基线仍为 G，并重跑路径、完成条件、质量、尾注、新审查。去掉该识别的 joint 变体在 `JOINT-CONFLICT-QUALITY-SUBMIT` 失败，见 (f)。

### (c) 审查 worktree 命名、结果与清理

`core.ts:2087` 用该 attempt 的 `review_requested` 记录数生成序号，目录为项目命名空间下 `<task>-a<N>-review-<K>`，`worktree add --detach`。同 C 复用在此之前返回，不新建目录或增加序号。

`reclaimReview` 从持久化 review_result 读取审查对象，核对 reviewer idle、原身份、stop/archive 读回后才调用 `cleanupReviewWorktree`。后者核对 task/attempt、路径/序号、非链接、Git 登记、detached HEAD=C、干净状态，追加 intent，删除，再读回不存在和未登记；清理事件不修改绑定对象。任何失败沿原 review 生命周期失败路径保留、暂停与上报。

`E/review-lifecycle-candidate/` 四个子案均 passed、无 cleanup_failures：

- `cleanup_after_persisted_result/review-lifecycle-proof.json`：directory_exists=false、git_registered=false；结果 #84 → cleanup_intent → removed #99 → reclaimed #100；task.review 与持久化 review_result 相同，随后可带分集成。
- `names_and_ordinals/review-names-proof.json`：两个不同 C 对应 review-1、review-2，ordinal=[1,2]；needs_fix 和 passed 的两个目录均清理；SQLite 中两个独立结果仍在。
- `dirty_review_is_preserved_and_reported/`：外部写入字节保留，Git 登记保留；库为 paused、review unknown，#94 lifecycle_failed 并上报；没有 removed/reclaimed 或集成。
- `changed_review_head_is_preserved_and_reported/`：C=`3b82e596e55c5c5efbc435794270e1e37527d6d9`，外部干净 HEAD=`99a29bb8b0af9bd61a718eccdc0ede690f705f06` 原样保留；库为 paused、review unknown，#92 lifecycle_failed；没有删除或集成。

同 C R8 组合已在目录被删除后复用原结果并通过，因而有直接证据说明清理没有破坏绑定。未知边界另有 T-076 review-faults 三案；不从这些受控场景推断真实沙箱权限有效性。

### (d) 夹具与历史 acceptance 改动

分别评估结果如下，未发现合流夹具放宽业务断言：

| 改动 | 独立判断 |
| --- | --- |
| T-076 `test_quality_chain_e2e.py:268` 的 relay_result | 从全局旧 key 改成 relay_requests/results JOIN，以 launch 与 request_id 限定真实 SQLite 行；缺结果仍抛 HarnessFailure，返回原 data。与产品作用域变化一致，没有制造成功值。 |
| adapter 的 overlap_reason 签名 | fixture diff 将参数传到 dispatch 的 `--overlap-reason`，非 dispatch 分支传给父 claim；父 claim 同样传给真实 CLI。产品 CLI 再映射为 overlap_reason，claim 会记录冲突集合与理由。`run` 的历史 reclaim 用例另核对三个理由各自的精确冲突集合，参数没有吞掉。 |
| relay managed_trailers | 从本 attempt launch 的 env、原生 runtime 和最后 turn_context 读取 Tool/Model/Effort/Native-Session/Launch，仍走正常提交及门禁验证；不是改断言接受 unknown。该层的原生输入明确受控。 |
| cwd 元数据修正 | controlled_quality_pty、startup_shutdown_host、native-final、dispatch-state 仅补 session_meta.cwd，后三者原断言未变；用于适配生产按 worktree 筛选 rollout。 |
| legacy_quality_driver readiness | 仅在 reviewing 且 review 尚未建立时沿现有期限等待；记录一旦存在仍检查候选、attempt、review id、launch/native，未知仍拒收。driver-readiness 的五项检查通过，不替代产品验收。 |
| 完整 run 18 项 runner | `run_s3_rebased_regression.py` 保留原 test 方法身份与成员数，failfast=false，记录 executed_methods，要求其与原列表相同；保存 run.json 的 tests_run=18、failures/errors/skipped=0、unexecuted_methods=[]，unittest 原文为 Ran 18 tests / OK。 |
| 历史 acceptance | revoke/reclaim 的“保留目录”改成“删除干净目录并核对准确隐藏引用”；候选内容在删除前保存再比对。Git 全引用比对只允许精确新增的保留引用，工作分支与 reflog 仍核对。旧“G 变化就拒收”按本票 R8 改成新 G/C 绑定、完整重验、保留两方祖先与内容、一次集成和重放不再写。路径、fence、旧 attempt、外来线程等拒收断言仍在；recovery 文件无 diff。 |

`E/coop/` 8、`E/recovery/` 9、`E/run/` 18、`E/cards/` 15、`E/cas/` 1 项，保存的完整执行列表与原成员一致，全部 0 failures/errors/skipped；collection_errors 为空，各 unittest 原文均 OK。CAS 仍使用实际 Git prepare 竞争，要求新 G 重验并保留外部提交与内容。

`E/s3-all/sources.tar.gz` 中 21 个 `workbench/src/*.ts` 文件经不写文件的逐字节比较，与产品提交全部一致；未使用摘要或旧候选通过结论来推定版本一致。

### (e) 三组小测试的原始结果

| 组 | 子结果、事件及命令收据 |
| --- | --- |
| relay-core | `E/relay-core/results.json` 的 failure=null；effects 是实际记录的 submit、submit、status、issue、submit 共 5 次调用。事件 #2 处理首次 submit、#3 只重放；错误 fence、缺 commit、坏 JSON、同编号改内容均拒收；#20 pending 重放返回 relay_outcome_unknown，没有追加调用，#21 才是原调用完成。stdout 同样 failure=null，receipt exit=0。 |
| native-final | `E/native-final/results.json` 九项 failure 均 null；逐读 exit/terminate/shutdown/reclaim/missing/truncated/malformed/partial/unbound 的原始 JSON，observerFailures 均为空。前四项保存 turn_context 后 native_final_read；后五项明确 native_final_read_failed，再 pane_exit，符合各自拒绝丢失/损坏尾部的预期。receipt exit=0。 |
| dispatch-state | `E/dispatch-state/results.json` failure=null；四次 write 为两次 bracketed paste 与各自单独 CR。登记数/submit intent 为 [1/0,1/1,2/1,2/2]；不匹配 Stop 有 stop_not_matched，正确 idle #21 后才出现第二条 paste #22、submit intent #24。stdout failure=null，receipt exit=0。 |

以上通过判断使用原始 failure、逐场景事件和调用记录，不以顶层缺失 status 时的默认值判绿。

### (f) 现成反事实实际命中位置

四条审查 preimage 与三条 joint 变体：

| E 下目录 | 真实失败断言 | 失败类别 |
| --- | --- | --- |
| review-lifecycle-red-01 | REVIEW-DIRECTORY-REMOVED | contract_failure；目录仍存在/仍登记 |
| review-lifecycle-red-02 | REVIEW-S3-NAMES | contract_failure；用途/序号命名不符 |
| review-lifecycle-red-03 | REVIEW-DIRTY-PRESERVED | contract_failure；未满足脏审查现场的暂停与上报 |
| review-lifecycle-red-04 | REVIEW-UNKNOWN-HEAD-PRESERVED | contract_failure；未满足未知 HEAD 的暂停与上报 |
| joint-red-same-c-new-review | JOINT-SAME-C-REUSE | contract_failure；禁用复用后失去同 C 复用行为 |
| joint-red-new-c-old-review | JOINT-NEW-C-REVIEW | contract_failure；新 C 沿用旧审查 |
| joint-red-rework-quality-not-authorized | JOINT-CONFLICT-QUALITY-SUBMIT | contract_failure；C3 重交被拒 |

七份原始 run.json 的 planned_cases 与已执行子案各为指定一案，traceback 指向上述断言，cleanup_failures 均为空；没有用 setup error 或清理异常替代红态。

冲突七次运行的 unittest 原文与 result.json 则为：

| E 下目录 | 真实失败位置 | failures/errors/skipped |
| --- | --- | --- |
| conflict-red-01 | 原 worker 回写缺失、重发计数、显式重交接受断言 | 3/0/0 |
| conflict-red-02 | Confirmed ended worker is replaced by one new attempt | 1/0/0 |
| conflict-red-03 | Unknown native session keeps the conflict scene and reports to the executor | 1/0/0 |
| conflict-red-04 | Unknown writeback has exactly one recorded delivery attempt | 1/0/0 |
| conflict-red-05 | Git failure without unmerged index entries is not a repairable text conflict；实际误报 merge_conflict，原 Git exit=73 | 1/0/0 |
| conflict-red-06 | **前置** Conflict rework accepts a new explicit candidate from its bound worker；实际 candidate_conflict | 1/0/0 |
| conflict-red-07 | **前置** 同上一行；实际 candidate_conflict | 1/0/0 |

前五次命中其所述冲突行为。最后两次的目标 verify 尚未执行，不能证明对应守卫的反事实，详见发现 F1。

`E/relay-global-mutant/global-lookup/run.json` 不是只看父报告：两个失败子案分别为 new_attempt_same_id_is_new_delivery、another_task_same_id_is_independent，failure.assertion=true；各只有首次 submit 的 effect，第二个 owner 被错误返回 relay_request_id_reused。其余三个子案通过；父记录 expected_failures 与 actual_failures 完全相同、errors=[]，故该变体确实被独立请求作用域断言抓住。

## FINDINGS

### P2 — F1：禁止路径与外来尾注的两条冲突反事实没有到达目标断言

**位置**：`workbench/tests/test_worktree_lifecycle_e2e.py:896` 的 business_red 分类；直接路径为该文件 `:734` / `:744` → `repair():604`，目标拒收断言分别在 `:737` 与 `:747`。

**原始证据**：

- `E/conflict-red-06/01-test_conflict_rework_still_rejects_forbidden_path/unittest.txt`；
- `E/conflict-red-07/01-test_conflict_rework_still_rejects_foreign_trailer/unittest.txt`；
- 对应两个 result.json、run.json、receipt.json；顶层 run.json 的 mutation_recipes 说明两案都只去掉 writeConflict。

两案均在 repair() 的提交成功断言收到 candidate_conflict 后结束；随后 request('verify')、path_boundary_failed、trailer_task_mismatch 等目标断言完全没有执行。当前分类只要“任意已登记 contract 失败且无 error”就标 business_red=true，因此两案均 red_confirmed=true，并被父收据计作 business-red。零 errors 不能补齐这个缺口：这里是成功制造了另一种业务失败，而非证明目标守卫可被测试检出。

**影响**：现成七条冲突红态中有两条重复证明“没有冲突回写就不能重交”；它们不提供“冲突重交后仍拒禁止路径/外来尾注”的独立反事实。候选正常反例确实拒收这两种输入，但当前证据不能完成这两项的已知坏实现验证；这限制的是验收证据，没有据此声称产品已经放过这些输入。

**最小修正**：保留现有失败原文；另用保持冲突回写与显式重交成功、只破坏对应路径守卫或尾注守卫的定向变体，分别要求失败在各自的 verify 拒收断言。为目标断言保存稳定标识，并将红态收据与该标识绑定；前置 submit/场景准备失败应记录为该目标未覆盖，不能计为其已验证反事实。本审查没有运行或实现该修正。

P0/P1/P3：无确认发现。产品行为的未覆盖边界列在 LIMITATIONS，不以推测增加发现。

## COUNTEREXAMPLE

F1 本身由保存的 no-conflict-feedback 两案直接证明：同一缺失回写的变体导致两个不同名义目标都停在 repair():604，均实际 candidate_conflict，目标 verify 未执行，分类器仍给 business_red。完整反事实命中表见 (f)。四条清理、三条 joint、relay 全局去重反事实未见错误、跳过或清理异常冒充其指定失败。

## LIMITATIONS

- 本次没有新运行；对版本、保存的代码与记录做一次只读独立审查。受控窗口/进程/原生记录和显式 worker/reviewer 判断不证明模型理解、审查准确率或当前只读沙箱的实际拒写效果。
- 最新 `outside-rebase-final-05` 的 real_codex_turns=0。历史 `real-conflict-03-evidence.tar.gz` 的原始命令显示运行源码为 `2e2291acfee0e9b4f20c7ff952a5484c4262e20b`，不属于本次冻结产品；不把它移用为最新合流版本的真实模型通过证据。
- 历史 r3 的原始事件确有原生会话结束 #644；fence=1 与 fence=2 的两个 delivery 都由不同 launch 显式转交成功。原始 Git show 显示真实 C2=`8b94d92812d0f8667f7d44dcbc178d9b343e2f8c` 额外携带 A2A-Fence/A2A-Spec-Rev，共十一项尾注。它没有完成合法尾注下的真实模型整串闭环。最终版本 `E/controlled-trailer-candidate/` 的两个场景通过实际 CLI/门禁/Git/生产 hook 证明十一项拒收、九项集成，仍明确是受控运行，不将真实模型失败改记为通过。
- 全库事件重建一致性、正式工作台切换及收益改善不在本次证明范围；T-076 Resolution 已明确的存储缺口不因这些空表或受控正例变成已覆盖。
- 请求配置为 gpt-6.1-sol / xhigh；本次 spawn 接口无 service_tier 选择，实际供应商 tier 未观察。产品或历史启动 argv 中的 default 同样只是请求值，不能充作实际档位证明。

## RULE

本次唯一确认发现 F1 属于重复失败类别。机械检查可在红态 runner 写 receipt 前执行：按 case 核对目标 failure id，要求已保存“冲突已投递、显式重交成功、目标 verify 已执行”的前置凭据；只有目标断言失败、无 errors/skipped/cleanup_failures 才计入该项反事实。当前 `test_worktree_lifecycle_e2e.py:896` 的“任意 contract 失败”不足以完成这项检查。
