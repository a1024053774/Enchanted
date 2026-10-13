# T-076-2：F05起的夹具迁移清单（待批准）

状态：**INCOMPLETE／等待清单批准**。依据主控 #50 与[决定02](controller-decision-02.md)，本轮仅列清单，未修改下列测试、适配器或产品。核对HEAD为`07c596fe6561ccd7b3f0c3cc5bc3bf94490a3230`；相对上一轮HEAD，workbench/acceptance没有已提交变化。真实回合仍0/8。

`outside-reviewer-green-01/run.json`已逐案读回：三个分组3/3、3/3、2/2，exit均0，全部passed、cleanup_failures为空、无超大文件。reviewer修复diff获主控认可。

## 共同边界

W01–W06、F01–F04继续有效，以下只把新增准备步骤落到准确位置。所有新helper名是拟新增名，不是声称代码已经存在。

- 真正的claim入口不整体替换；不按`command == claim`全局转成dispatch。
- 受控dispatch必须经真实CLI和门禁，再由外部运行时夹具实际创建受控执行者，交付由真实submit保存来源。允许的是可审计的受控运行时创建事实，不是假CLI/真实模型证明；不直接写生产库中的launch、delivery、review或passed。
- reviewer由实际创建的独立受控运行时启动，通过B结论及真实relay/身份检查交付。fixture不能在verify的返回值里补verified或伪造review_result。
- 执行主控评分文件按场景显式准备、记录来源和绑定attempt。只在已登记的集成动作传`--score-file`，缺分及手工来源反例走原始CLI，不通过补分helper。异步run的执行主控driver固定原attempt。
- 每例报告准备步骤序列：`手工 claim`、`受控 dispatch`或二者各自对应的attempt；不只给文件一个笼统标签。全部属“真实后台/Git/门禁＋受控外部会话”，真实模型仍另验。

## F05：交付8项的准备步骤

文件：`workbench/tests/daemon_acceptance_adapter.py`的`DaemonDelivery`，新增`dispatch_candidate_attempt(task=None)`；必要的显式调用位置在`acceptance/test_coop_e2e.py`，属于本次请求批准的准备hunk。

| method | 原准备 | 拟准备／保留 |
| --- | --- | --- |
| `test_good_candidate_uses_oracle_snapshot_and_integrates_once` | create→claim | create→显式受控dispatch；原候选、独立分页输入、oracle/card快照、一次Git写及重放断言保留；按W03增加review/score前置 |
| `test_baseline_change_after_verification_rejects_integration` | create→claim；合法候选后注入G变化 | create→受控dispatch，提供合法review/score后再注入原G变化；保留`integration_conflict`及全部Git不变断言。这是为到达原CAS反例而补齐成功前置，需明确批准纳入决定02的迁移范围 |
| `test_identity_gates_and_revocation_reject_old_verified_attempt` | 原attempt与replacement均claim | 两次真实claim都保留；只按F03完成review，使原verified观察继续，撤销后拒绝集成不需要评分来源 |
| `test_concurrent_claim_is_unique_persistent_and_task_specific` | 并发真实claim、另task claim | 原入口与全部竞争/持久化/任务隔离检查不变 |
| `test_unverified_and_oracle_failed_candidate_never_changes_ref`、`test_oracle_rejects_candidate_missing_limit_upper_bound`、`test_spec_revision_invalidates_candidate_and_old_identity` | 真实claim | 原准备不变；不补分使错误变成别的错误 |
| `test_submit_requires_clean_head_and_cannot_replace_frozen_candidate` | claim、冻结反例、末尾成功集成 | 有直接合同冲突，见下文F12，不能默认为已批准迁移 |

`ManagedDeliveryCLI.claim()`本身不改成dispatch。F05不改变候选生成器的独立参考实现，不改任何oracle预期。

## F06：Recovery9项，原业务方法与断言逐字保留

文件：`workbench/tests/daemon_acceptance_adapter.py`的`DaemonRecovery`；新增受控`claim`准备适配，只允许以下明确的method＋owner匹配。`acceptance/test_recovery_e2e.py`不编辑。

| 原method/helper调用 | 准备选择 |
| --- | --- |
| `test_live_verify_excludes_verify_and_integrate`→`setup_candidate()` | 保留手工claim；只补真实review前置，原live operation lock和ref不变断言不动 |
| `test_interrupted_verify_gets_new_id_worktree_and_full_oracle`→`setup_candidate()` | 保留手工claim；原/新oracle屏障、旧输入保留、worktree及verified观察不动 |
| `test_live_integrate_excludes_verify_and_integrate`→`setup_candidate(verified=True)` | 此次`owner=independent-check`准备改为受控dispatch |
| `test_before_CAS_recovers_same_intent_once`、`test_after_CAS_recovers_bookkeeping_without_Git_write`→`recover_integration()`→`setup_candidate(verified=True)` | 仅setup中的这一次准备改为受控dispatch |
| `test_after_CAS_external_X_requires_reconciliation`、`test_after_CAS_deleted_ref_requires_reconciliation`→`unknown_reference()`→`setup_candidate(verified=True)` | 仅setup改为受控dispatch，先具备原合法integration intent，再执行原未知引用反例；需一并批准这两项成功前置 |
| `test_interrupted_verify_revoke_reclaim_rejects_old_identity`、`test_interrupted_verify_spec_change_rejects_old_candidate`→`stale_after_interruption()` | 被中断/撤销/改版的旧attempt仍由真实claim产生；仅后面的`claim(owner="replacement-after-interruption")`准备改为受控dispatch，原stale拒绝、原attempt/verification保留与replacement集成断言不动 |

拟新增`DaemonLifecycle.complete_review(attempt, candidate)`和`prepare_executor_score(attempt)`；`complete(handle)`只在成功verify已结束后触发外部review交付，再让原断言继续，不改客户端原返回字节。对同步verify路径在`cli()`成功后做同一明确前置。异常/拒绝/忙锁路径不启动review。

`cli_argv()`只在上述明确已准备评分的attempt集成动作中添加已固定的score文件；`start_cli()`、`process(cli_argv(...))`、恢复与重放均保存真实argv，同一个pending intent使用同一个score。没有`ok`推测、忽略失败或额外CAS。原`install_git_wrapper`、`wait_barrier`、`kill_owned_cli`、`same_intent`、CAS计数和9项断言不改。

## F07：Run18项的准确选择

文件：`workbench/tests/daemon_acceptance_adapter.py`的`DaemonRun`；`acceptance/test_run_e2e.py`仅在已批准W01/W02处及下列准备位置添加显式helper调用，原业务断言不顺带改。

| method | 拟变动 |
| --- | --- |
| `test_integrate_expected_attempt_uses_real_git_gate`、`test_attempt_guards_preserve_existing_live_operation_lock` | `setup_candidate()`中的执行准备改受控dispatch；guard、原屏障和集成后断言不变 |
| `test_stale_verify_integrate_guards_preserve_current_and_accepted_state` | `old-guard-owner`仍真实claim后真实revoke；仅`current-guard-owner`准备改受控dispatch，原旧attempt guard拒绝、匹配guard成功、accepted后旧guard拒绝及重放检查不变 |
| `test_verify_expected_attempt_uses_real_gate` | 仍手工claim，成功机械检查后经F03补独立review；原guard/ref/verified断言保留 |
| `test_reclaim_guard_targets_history_and_rejects_foreign_and_unknown_attempt` | 原dispatch/手工current claim/外task dispatch/替换dispatch均保留；不为当前仅submit的手工attempt补来源 |
| `test_run_entry_point_completes_registered_task`、`test_transient_tool_activity_keeps_same_thread_owner`、`test_concurrent_duplicate_run_has_one_prompt_and_one_attempt`、`test_matching_reclaim_guard_is_idempotent_after_automatic_success` | 原run/dispatch不变；新增`drive_executor_finalize(handle, attempt, candidate)`，外部review通过后CLI带分集成，再取原run结果。helper-joins沿主正例；duplicate-run仍只有一个worker prompt/attempt |
| `test_fixture_existing_dispatch_submit_oracle_integration_and_reclaim` | 原dispatch不变，原verify后明确review、integrate加固定评分，沿W02 |
| `test_oracle_failure_is_not_success_and_reclaims_only_owned_thread` | 沿W01；保留原失败oracle/ref/workspace，首拒保留原worker/attempt，核对登记的修复消息；不运行集成driver |
| 其余7项：`test_new_native_turn_is_not_owned_even_with_old_thread_present`、`test_done_without_submit_hits_deadline_and_cannot_accept_committed_candidate`、`test_invalid_wait_values_have_no_worker_or_business_side_effect`、`test_replacement_attempt_is_not_verified_integrated_or_closed_by_old_run`、`test_startup_blocked_preserves_scene_without_prompt_or_close`、`test_post_prompt_blocked_preserves_scene_without_answer_or_reprompt`、`test_unknown_identity_cannot_succeed_or_close_replaced_worktree` | 全部保留原准备与反例，不运行最终集成driver；leader-changed那一段不改 |

上表合计18项。不通过删方法、skip或改变suite计数消除失败。

## F08：T-075任务卡回归的准确选择

文件：`workbench/tests/test_task_cards_e2e.py`的`TaskCardsCLI`及`workbench/tests/test_daemon_gates_e2e.py`的`DaemonCards`。

- 将`TaskCardsCLI.create()`中的注册步骤提成`register_task()`，原`create()`仍调用真实claim；另加`create_managed()`显式dispatch。修改调用点仅为以下6项：`test_tracer_merges_G_and_C_and_integrates_once`、`test_missing_trailer_records_one_inferred_action_and_integrates`、`test_dirty_target_rejects_without_losing_staged_unstaged_or_untracked`、`test_linked_and_unchecked_branch_and_nonconflicting_dirty_changes`、`test_missing_trailer_reverification_deduplicates_action`，以及`test_ticket_revision_and_template_source`末段原直接claim的位置。dirty三种模式仍逐项验证原内容/index/ref/reflog，需批准其合法集成前置使用dispatch。
- 其余8个test method保留原claim；尤其`test_stale_fence_and_attempt_rejected`、`test_card_validation_versions_and_claim_snapshot`不迁移，注册/claim快照及改版旧身份检查都在原入口上做。
- `commit()`只在受控dispatch时从该受控创建事实取得对应尾注字段；手工claim仍保留原独立fixture尾注。恶意尾注的四种模式、外来middle commit、无尾注人工介入预期不改。
- 增加显式`complete_review()`/`score_file()`，调用点沿W04。`DaemonCards.setUp/stop_daemon`改为具备受控worker/reviewer的测试host生命周期；保留现有Git router及non-fast-forward故障注入，不运行真实provider。`test_new_tables_are_append_only`断言不改。
- 直接执行旧`test_task_cards_e2e.py`已不是daemon入口，本次以`test_daemon_gates_e2e.py`继承运行14项原业务method＋1项追加式表测试，不重复跑已失效的旧独立入口。

## F09：运行时与review交付边界（F01的落实位置）

文件/拟改位置：

1. `daemon_acceptance_host.ts`：`controlledRuntime.createThread/readThread`补可持久读回的受控创建事实；新增`sessionFacts/qualityFeedback/createReview`，`stopThread/archiveThread`分清worker与reviewer。`ControlledThreadGates.call`保留真实门禁调用，仅在原测试外部会话边界提供绑定caller，不能覆盖检查方法或结果。重启从外部夹具创建账本核对既有worker，不按新PID/随机新launch替旧所有者背书。
2. `multiturn_identity_host.ts`：同样增加受控创建事实、`sessionFacts`及reviewer边界；`ControlledGates.call`保持原活动turn核对。`test_multiturn_identity_e2e.py`仅在`test_reclaim_after_receipt_turn`与`test_run_after_receipt_turn`加独立review/主控评分前置（W05），`delivery-A`、receipt-B、两个伪造身份反例和只关闭原worker的断言不改。
3. reviewer使用已有`Panes.createReview`及受控PTY，不伪造`review_submit`结果；必要时将`quality_chain_host.ts`的PTY/进程观察夹具提取到测试模块`controlled_quality_pty.ts`的`installControlledPTY()`供两个host复用。只提取这两个外部边界，生产门禁/队列/relay/身份检查不替换。reviewer的prompt/close记录与旧worker store分开；原worker数量/归属断言仍读取原store。
4. 新增测试driver `legacy_quality_driver.py`：`complete_review()`从明确review_id/C启动输入生成合法外部JSON，经匹配Stop/B/relay送达；`drive_executor_finalize()`在观察到同C的review_result后经CLI评分集成；`write_case_preparation()`逐attempt记准备方式、外部创建记录路径、命令及证据层。JSON内容由fixture固定oracle给出，不能从产品`passed`字段反推审查结论。

受控运行时的CLI/model/effort明确标为fixture事实；不能当作真实Codex运行、Fast实获或只读沙箱证明。不向生产库预填launch/delivery/passed；这些界限若无法用当前接口做到，交回，不补test mode。

## F10：手工claim来源反例与已知坏变异体

文件：拟新增`workbench/tests/test_quality_legacy_e2e.py`中的`manual_claim_reviewed_score_refused`，复用现有QualityCase真实后台。准备为真实claim→候选→真实submit→机械通过→独立reviewer合法B结论→完整合法评分文件。检查手工attempt仍无受管启动来源、review已通过且绑定同C，然后调用原始integrate。

预期来自决定02/PLAN §5.2：`score_provenance_required`拒绝，新的rejected事件指向该integrate；task/attempt/candidate不被接受，ref/reflog/检出内容不动，没有score_recorded。完整输入及原始返回保留。新增编号`MANUAL-CLAIM-SOURCE`。

变异体仅在候选副本删除integrate的`requireGate(attempt.delivery, "score_provenance_required")`。即使后续finalScore仍会拒绝，测试也必须因前置门禁被绕过导致Git已变而命中`MANUAL-CLAIM-SOURCE`；不能仅凭“返回非零”放过它，不补假delivery使变异体跑通。若未达到该预写业务断言，反事实为INCOMPLETE并交回。

## F11：回归运行器、产物与预算

- `run_daemon_acceptance.py`的`preflight/snapshot_sources/run_probe`：旧“三份acceptance diff必须为空”改为准确校验已批准hunk；Recovery仍逐字不变，两个受保护片段按批准范围核对。保存完整差异，仍拒绝业务method在adapter中被替换。每例增加F04及准备方式记录；不改8/9/18计数或成功标准。
- 新增`run_t076_legacy_green.py`：冻结候选、harness和批准清单，单阶段依次执行F10正/变异体及F12补充场景、完整coop8/recovery9/run18、T-075任务卡15项与`test_relay_core.ts`/`test_relay_cli.py`现有测试、T-076-1多回合4项。多回合组同时启用`--check-consistency`保留新交付的一致性诊断，全库已有“不一致/无法重建”如实报告，不修存储、不混称全库PASS。
- 五类变异体沿`prepare_workbench_mutants.py:prepare()`的原定义，以及`run_t076_green.py`的mutants分组所用`test_offline_trace_e2e.py`、`test_build_volume_contract.py`及其两项对照；不更换变异目标或预写失败含义。尾注/环境沿`test_hook_turn_facts.py`、`test_hook_environment.py`；启动/停止沿`test_initial_worker_release.py`、`test_startup_shutdown_e2e.py`原4＋4项及停止顺序变异体。新runner直接编排这些已有入口，避免重复执行`run_t076_startup_shutdown.py`末尾已包含的多回合组。
- `outside-sandbox.sh`批准实施后加`legacy-green`一个阶段。各组独立新目录，第一处异常就停；不重复wide-green 15项/13变异体、reviewer-green8项。大文件按既定外置盘规则处理。
- `run_worker_delivery.py`、`run_t076_real.py`本次不启动，不在此清单中扩真实预算；真实正反例另用本卡runner，在准确argv/home/hook获批准后才启动。当前计划真实仍0/8。

## F12：冻结候选方法末尾的冲突，须单独明确批准

`acceptance/test_coop_e2e.py:test_submit_requires_clean_head_and_cannot_replace_frozen_candidate`在`:476–509`保留真实claim并检查dirty/head/未打回换C/验收冻结C；`:509–511`随后要求同一手工attempt成功integrate、ref=C且不等later_bad。决定02拒绝无受管来源的手工claim，与这三行同时成立不了。原W03明确说冻结候选断言不改，因此不能把普通F05批准解释成改这三行。

建议追加断言白名单 **W07**，只处理该method的末尾：保留直到verified/candidate=C的全部原claim检查；最终改为带合法评分仍拒绝来源、ref不动。原“最终集成C、不集成later_bad”的证据移到`test_quality_legacy_e2e.py:managed_frozen_candidate_integrates_original`，以真实受控dispatch重放完整的dirty/head/冻结C/C2拒绝/verify冻结C/独立review/集成C场景，全部原保护预期照留；8项旧套件计数不变，新补充场景单列，不冒称未改原断言。

这不是本worker已作的决定。请主控明确批准W07及上述双场景保留方式，或指定另一个同时保留手工claim冻结检查与受管集成证据的方案；批准前不修改该method、不跳过它。F06旧manual→replacement dispatch和F07旧manual→current dispatch的精确选择也请一并确认，它们保留原撤销对象的真实claim并不改Recovery9业务断言。

## 本轮再生成／核对命令

```sh
git diff d3f2c2cf3b838d8f56e8a57629a19b9d282ea64f HEAD -- workbench acceptance
git diff a7f4cc3033c16d5888de50d8352da516c941f8e9 -- acceptance/test_coop_e2e.py acceptance/test_recovery_e2e.py acceptance/test_run_e2e.py workbench/tests/daemon_acceptance_adapter.py workbench/tests/daemon_acceptance_host.ts workbench/tests/test_task_cards_e2e.py workbench/tests/test_daemon_gates_e2e.py workbench/tests/test_multiturn_identity_e2e.py workbench/tests/multiturn_identity_host.ts
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

前两条当前应为空，证明本轮清单未先行实施。reviewer-green原结果只读，不重跑。批准之后再写新反例、迁移、更新assertion-hunks并交合并沙箱外脚本。

以上只读核对、8项旧结果读回、方法清单及UTF-8检查的收据再生成命令（换新output保留历史）：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/check-migration-list.py --output evidence/2026-10-11-batch13/T-076/card-2/migration-list-checks.json
```
