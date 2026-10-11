# T-075-5 计划（2026-10-11，待执行主控批准）

状态：**INCOMPLETE**。本轮只完成源码与既有证据核对、逐项迁移计划；尚未实现适配器、启动测试后台或运行新验收。批准前停止。

## 依据、目标与边界

- 任务：T-075-5，Herdr agent `s12-t075-5`；来源 T-075 当前 `ready_rev: 4`，ticket 保持 open。
- 开工 HEAD：`1b522e92aa3944ebc0caca78c62553d8de386ed0`。此前最终产品候选：`7bcfe7d9f91cc4dd10ccdb3155cb15312526e91f`；执行主控验收：`be3ca531fac4be688cd4317b16cf38ec939ffc30`。
- 启动记录：`launch-e2dfb51e50404371bb95e477b46bbac6`，attempt `a1`，session `f82c11a2-4410-42fc-b9f9-24b0ad037050`；记录请求模型 `gpt-6.1-sol`、xhigh、Fast，不把请求 tier 当实际供应商 tier 证明。
- 已读：AGENTS.md、CONTEXT.md、intent.md、MAP.md、T-075、native-cli-orchestration spec 第 1、3、5、9、12 节及 Test seam；另外核对 managed/recovery/run 测试和恢复、自动运行契约。
- **小目标**：同一最终 CLI → Unix socket → 常驻后台 → 门禁 → 独立 oracle／真实 Git 路径上，重新取得 8/8、9/9、18/18 的当前证据，并杀死 fence、CAS 期望旧值、操作锁三个变异体。
- **非目标**：不改三份 `acceptance/test_*.py` 的任何字节；不改门禁业务契约、产品自动启动行为、S2～S5、界面、scripts、spec、fork 或全局配置；不运行真实 Codex 被测回合。
- **验收条件**：三套完整通过，三个变异体因业务断言失败，断言文件相对 `7bcfe7d9` 的 diff 为空，地图 0 problems；未知或未运行项不记 PASS。
- **Tracer bullet**：批准后先跑一项普通交付、一项真实后台中断、一项受控线程完整 run，三条入口走通后再跑各套全量。
- **Deep modules**：门禁核心继续拥有状态、锁和恢复；适配器只拥有隔离夹具、进程生命周期及外部线程服务，不复制后台调度器或门禁实现。
- **Ubiquitous language**：沿用 task、attempt、session、fence、门禁入口、编排后台；CLI 客户端退出与后台门禁执行者中断分别记录。

## 事实、推断与待决事项

| 类型 | 核对结果与来源 |
| --- | --- |
| observed | 开工地图检查退出 0，0 problems、0 stale；已有脏文件只有 `evidence/2026-10-09-batch11/controller-poll.log`，保留，不纳入本卡提交 |
| observed | 三套主控红态均绑定 `7bcfe7d9`，分别执行 8、9、18 项，全部在入口失败；coop 因 subTest 有 9 个 failure 记录，不能把 failure 数当用例数；见 `../card-4/executor-final-{coop,recovery,run}-01/run.json` 和 stderr |
| observed | `workbench/src/transport.ts` 将 socket 固定为 `state/control.sock`，按字节拒绝超过 103；`daemon_start` 对 state 作 realpath。只缩短 artifact 总目录还不够，旧测试的长方法名前缀也须缩短 |
| observed | `RecoveryCLI.wait_barrier` 以 CLI PID 匹配 oracle/Git 的 ppid；`kill_owned_cli` 核对 CLI argv 后杀 CLI，要求 CLI 返回 -SIGKILL。这是旧进程形态的夹具检查，不是恢复业务断言 |
| observed | 后台 `serve` 未导出，硬编码 `new A2AGates(root, panes)`；`Panes.createThread` 只接受 workspace-write 真实 Codex，与旧受控线程夹具的 approval-required 不相容 |
| observed | `acceptance/entry/native-entry.ts:9–27` 的 submit 直接构造 A2AGates 开库；末尾向当前 `main` 传 runtime 的额外参数已不起作用。该入口不能用作最终后台证据 |
| observed | `test_daemon_recovery_e2e.py` 已有真实后台五项：杀自己的后台、核对退出、清掉自己的残留 endpoint、显式重启；可复用方法，不复用旧 PASS 结论 |
| inferred | 交付 8 项和恢复 9 项可通过短夹具根、明确启动／重启后台与生命周期适配，保留全部原业务断言；尚未实跑，不能宣布可通过 |
| inferred | 编排 18 项中 13 项依赖受控线程服务；若批准下文的内部 host 注入边界，可继续使用现有线程夹具及原断言，不需要真实模型 |
| unknown | 单后台内并发、恢复屏障、run 与 submit 的时序在新适配器上是否满足原契约，须用下文三个最小探针决定；实际业务失败时停下交主控，不自行修产品 |

**待批准 D1：仅增加后台内部的可注入构造边界。** 建议只改 `workbench/src/daemon.ts`：导出当前 `serve`，增加一个内部 gate 构造函数参数，默认仍是 `new A2AGates(root, panes)`。测试启动器可传入使用现有 GateRuntime 的真实门禁对象，或加载隔离变异体的对象。后台的 socket、请求处理、事件、调用 `gates.call` 和关闭流程仍是同一份生产代码；不增加 CLI 选项、环境测试开关、第二个 server 或产品入口。产品 `daemon_start` 继续调用默认构造。本文件在原修改边界外，**批准前不改**；无需改 socket 位置、transport、Panes 或门禁核心。

**待批准 D2：将恢复的进程夹具检查迁为后台所有权检查。** 保留原测试方法、check/finish_checks、cli_result、snapshot 和每一项业务预期，只在新测试适配器中替换启动、屏障 PID 定位、故障注入和清理。SIGKILL 的真实对象是自己的后台；客户端记录真实断连退出，不伪造 -9。旧 helper 中 CLI PID／-9 条件不能原封不动用于后台，需主控认可这是生命周期适配。若“任何预期不改”也包含这种夹具进程条件，则下文恢复 7 项不能完成，交主控决定，不硬改。

**待批准 D3：编排证据仍标隔离线程服务。** 13 项替换的边界仅是 GateRuntime 和测试 submit 的 active-turn caller；请求照常经产品 CLI 和后台，真实门禁、Git、SQLite、oracle 不替换。这不是实际 PTY／真实 Codex 或 B 转交通道的新证据；本卡不据此重宣称那些边界已验收。默认 Panes 的五项编排场景另跑，避免把全部编排证据都写成测试 host。

## 1. 适配方式与生命周期

预计新增文件只在 `workbench/tests/`：

- `daemon_acceptance_adapter.py`：三套原 TestCase 的生命周期适配；测试方法继承原文件，不重新写断言。
- `run_daemon_acceptance.py`：显式选择原类中 8／9／18 项，运行、记录版本和逐项结果、归档；新增 CAS 补充场景单列，不能凑进 35 项计数。
- `daemon_acceptance_host.ts`：仅测试使用，调用批准后的生产 `serve`，传入受控线程运行时或隔离变异体；没有自建 server。
- 新变异体生成器：从最终冻结候选复制源码，只改指定单点，保存 patch 和清单。

入口使用 `acceptance/entry/a2a_gates.py`，所有业务请求执行 `node workbench/src/gates/cli.ts`。`COOP_SCRIPT` 显式选择此入口；create 的适配只补原线程入口已经补过的 `--project <task>`。不使用 `native-entry.ts` 的直接开库 submit 分支。原则上不需改 `acceptance/entry/`；若需要，仅调入口选择或参数传递。

1. 运行器在 `/tmp` 建一个短 artifact 根；将原 helper 的临时根分配调用定向到短编号目录（仅精确匹配本轮 artifact 根的那次 `mkdtemp`，保留原函数用于其他分配），记录编号与完整 test id。原 `self.repo`、`self.state` 的定义和关系不改。真实路径例如 `/private/tmp/a5-XXXXXX/t01/isolated state/control.sock`；启动前核对 realpath 后 UTF-8 字节数小于等于 103，超长立即报夹具错误。
2. 每个测试的完整原 setUp 结束后，由适配器**显式**启动一次独立后台，再发任何业务命令。普通交付、恢复以及编排五项用产品 `daemon_start`；受控线程 13 项用测试启动器调用同一个 `serve`。测试启动器以 `start_new_session=True` 脱离调用者进程组；产品后台继续使用已有 detached。
3. 起后台、业务调用、停止、崩溃与重启分别记命令和 PID。启动等待只观察 ready／daemon_status，有限期限；不重放失败的启动或业务修改命令。产品 CLI 未运行后台的负例仍应返回失败，不自动启动。
4. 测试仍直接检查 `self.state/state.sqlite3` 是否存在，并用原 `snapshot` 的只读 SQLite 查询保存全表；原 status/events/Git refs/reflog/worktree 读回不动。不搬 state、不做长路径到短路径的 socket 代理，也不手工写门禁库。
5. 后台在启动时固定 PATH，不能靠后来 CLI 的 PATH 注入 Git。测试开始先创建一个明确的 Git 路由夹具；非注入阶段调用已核对的 REAL_GIT，原 `install_git_wrapper` 创建 wrapper 后，只把这个精确 wrapper 当注入工具。记录每次目标选择和真实 argv。该路由只解决启动时机，不捕获失败后换工具、不重试 Git。
6. `start_cli` 给异步 handle 附当时后台代次、PID、state、命令与屏障起点。`wait_barrier` 用该代次后台 PID 匹配 ppid，同时核对所属 control、候选 worktree／Git argv 和等待中的真实 CLI。保存原屏障文件，不修改其中 ppid。
7. 故障窗口：核对记录、daemon_status、daemon.pid、ps 和屏障 ppid 一致，只 SIGKILL 本轮后台；不杀进程组、不杀 oracle、Git、线程身份、Herdr 或其他后台。保存后台真实信号结果和客户端真实断连结果。核对后台已退出后，仅清理该后台自己创建的 socket/PID；随后由测试适配器**明确重启一次**，同一 state，既有 pending 状态不改。继续的 verify/integrate 才执行恢复。恢复不能被重启或锁释放当作通过。
8. `busy_probe` 的 2 秒拒绝、operation_busy 和其余业务 check 原文保留；只适配超时时“第二个请求的外部屏障”定位。按本请求开始后的屏障集合识别新增屏障并释放，不能杀仍工作的原后台。清理分支只收尾自己的客户端与外部屏障；不会把所有超时都解释为需要重启。
9. cleanup 先释放本测试的线程观察与 oracle/Git 屏障、收齐异步 CLI，再显式 daemon_stop。停止响应后等 endpoint/PID 消失并核对进程退出，才能归档。不覆盖老输出，不删除测试 repo；完整现场 tar 归档，不把内嵌 Git 当 gitlink。

这不是产品隐式启动：后台所有生命周期动作由测试运行器的 setUp／故障处理／cleanup 发出且有独立证据；业务 CLI 自身的分支不变，后台未起时仍失败。测试入口没有“连不上就启动”的路径。

受控线程 host 使用原 `native-runtime.ts`／`thread-boundary.py`。仅测试中的 gate 对象在接到 submit 后，通过同一个门禁的只读 status 查 thread，按原夹具 submit-begin／submit-end 提供线程及 turn 的 SubmitCaller，再把**未经重写的请求**交给原 `A2AGates.call`。不生成成功结果、跳过身份检查或另开门禁实例；夹具状态不写产品 SQLite。该适配位于后台内，而不是 CLI 客户端直接开库。对没有绑定 thread 的 claim 场景不附 caller。

## 2. 三套逐项迁移表

表中的“原样”指在共通短路径、显式后台和 create 参数适配之后，业务方法及全部预期照原样运行；是否绿仍待执行。屏障和信号的改动只发生在新适配器。

### 交付：8 项

| 项 | 原测试方法 | 在新入口上的做法 |
| --- | --- | --- |
| C1 | `test_concurrent_claim_is_unique_persistent_and_task_specific` | 原样；4 个并发 CLI 连接同一个本测试后台，两 task 的唯一赢家、持久状态与拒绝事件原断言 |
| C2 | `test_identity_gates_and_revocation_reject_old_verified_attempt` | 原样；错 session/fence/spec、撤销与旧 attempt 被拒；作为 fence 变异体信号 |
| C3 | `test_unverified_and_oracle_failed_candidate_never_changes_ref` | 原样；坏候选 oracle 及未经验证不得改引用 |
| C4 | `test_oracle_rejects_candidate_missing_limit_upper_bound` | 原样；保留既有分页业务 known-bad，不把 fixture 正常启动当业务红态 |
| C5 | `test_good_candidate_uses_oracle_snapshot_and_integrates_once` | 原样；冻结卡与 oracle、一次集成、幂等及 accepted 后拒绝 |
| C6 | `test_baseline_change_after_verification_rejects_integration` | 原样；原外部提交发生在后台验收后；此项不能单独杀死 CAS 旧值变异体 |
| C7 | `test_submit_requires_clean_head_and_cannot_replace_frozen_candidate` | 原样；干净 HEAD、候选冻结、后续坏提交不替代 |
| C8 | `test_spec_revision_invalidates_candidate_and_old_identity` | 原样；revise 后旧候选与身份失效 |

### 恢复：9 项

| 项 | 原测试方法 | 在新入口上的做法 |
| --- | --- | --- |
| V1 | `test_live_verify_excludes_verify_and_integrate` | oracle 屏障父 PID 换为后台；不杀进程；原客户端仍等待；第二 verify/integrate 必须及时 operation_busy、无第二 oracle；锁变异体信号 |
| V2 | `test_live_integrate_excludes_verify_and_integrate` | 冻结 oracle 和 before-CAS wrapper 均来自后台；不杀进程；后台 PATH 路由覆盖晚装 wrapper；原排他与 intent 断言 |
| V3 | `test_interrupted_verify_gets_new_id_worktree_and_full_oracle` | oracle 中途 SIGKILL 后台、显式重启；新 verify 的屏障绑定新后台，旧 oracle 只自行 release；新 id/worktree、旧 interrupted/unknown 与完整新 oracle 原断言 |
| V4 | `test_before_CAS_recovers_same_intent_once` | 原 before 屏障、信号对象换后台；释放原 wrapper 为 abort；同 state 重启、原 integrate 重放；原 intent 与恰好一个 Git 效果断言 |
| V5 | `test_after_CAS_recovers_bookkeeping_without_Git_write` | 先确认真实 Git commit 成功，再杀后台；重启、integrate；M 只补记账、reflog 和 CAS 次数不增加 |
| V6 | `test_after_CAS_external_X_requires_reconciliation` | after-CAS 杀后台，外部真实提交 X，重启；needs_reconciliation、原 intent/事件/引用不变 |
| V7 | `test_after_CAS_deleted_ref_requires_reconciliation` | after-CAS 杀后台，原真实 delete-ref，重启；原拒绝、无重写、无 accepted 断言 |
| V8 | `test_interrupted_verify_revoke_reclaim_rejects_old_identity` | oracle 杀后台并重启，原 revoke/claim；旧 submit 与候选拒绝，新候选走新后台 oracle；保留全部旧目录 |
| V9 | `test_interrupted_verify_spec_change_rejects_old_candidate` | oracle 杀后台并重启，原 revise/claim；原新 spec、旧身份与候选不复活断言 |

V3～V9 需要 D2。V1/V2 只改屏障进程定位和并发探针的收尾定位，不改业务预期。

### 编排：18 项

“受控 host”需要 D1/D3，保持原 approval-required 请求及线程服务场景；“默认后台”保持正常产品 daemon_start。

| 项 | 原测试方法 | 在新入口上的做法 |
| --- | --- | --- |
| R1 | `test_run_entry_point_completes_registered_task` | 受控 host；原 ensure/create/start/read/stop/archive，submit caller 在后台提供；原真实 C、oracle、G→M、事件与只回收本线程断言 |
| R2 | `test_transient_tool_activity_keeps_same_thread_owner` | 受控 host；原 helper-joins；同一 turn 正例与 R1 的原断言 |
| R3 | `test_new_native_turn_is_not_owned_even_with_old_thread_present` | 受控 host；原 leader-changed；旧 turn 不回收、不验收 |
| R4 | `test_verify_expected_attempt_uses_real_gate` | 默认后台；claim 无线程，matching --attempt 原 verify/SQLite/Git 断言 |
| R5 | `test_integrate_expected_attempt_uses_real_git_gate` | 默认后台；原匹配 attempt、真实 Git 与 reflog 断言 |
| R6 | `test_fixture_existing_dispatch_submit_oracle_integration_and_reclaim` | 受控 host；原夹具信任准备；CLI dispatch→submit→verify→integrate→reclaim，无直接开库 submit |
| R7 | `test_done_without_submit_hits_deadline_and_cannot_accept_committed_candidate` | 受控 host；原 done-no-submit，显式等待 2 秒；候选已 commit 也不接受、不 oracle，只回收自己 |
| R8 | `test_concurrent_duplicate_run_has_one_prompt_and_one_attempt` | 受控 host；两个真实 CLI 到同一后台；原 run_busy、单 prompt/attempt 和首 run 完成断言 |
| R9 | `test_invalid_wait_values_have_no_worker_or_business_side_effect` | 默认后台；原六种非法值及状态/引用/线程夹具不变；不规范化非法参数、不放宽退出码 |
| R10 | `test_replacement_attempt_is_not_verified_integrated_or_closed_by_old_run` | 受控 host；原 hold-observe 文件屏障，不杀后台；原 revoke、历史 reclaim、新 dispatch/submit，放行后 run_superseded；不接管 replacement |
| R11 | `test_oracle_failure_is_not_success_and_reclaims_only_owned_thread` | 受控 host；原坏候选、独立 oracle 非零及归属回收断言 |
| R12 | `test_startup_blocked_preserves_scene_without_prompt_or_close` | 受控 host；原 startup-blocked；不发任务、不批准、不回收 |
| R13 | `test_post_prompt_blocked_preserves_scene_without_answer_or_reprompt` | 受控 host；原 post-prompt-blocked；不答复、不重投、不回收 |
| R14 | `test_unknown_identity_cannot_succeed_or_close_replaced_worktree` | 受控 host；原 identity-changed；保持未知 workspace，无 oracle 或自动重试 |
| R15 | `test_stale_verify_integrate_guards_preserve_current_and_accepted_state` | 默认后台；原旧/current attempt、accepted 幂等前 ownership 检查及状态/refs/worktrees 不变 |
| R16 | `test_reclaim_guard_targets_history_and_rejects_foreign_and_unknown_attempt` | 受控 host；原两个 task、多历史 attempt 及跨任务拒绝；默认 Panes 的 single_worker_slice 不能满足此夹具，不修改它来凑通过 |
| R17 | `test_matching_reclaim_guard_is_idempotent_after_automatic_success` | 受控 host；完整 run 后原 matching reclaim 重放及一次归属关闭 |
| R18 | `test_attempt_guards_preserve_existing_live_operation_lock` | 默认后台；claim 无线程；原 oracle 屏障 ppid 记录来自后台，其原方法不依赖 CLI 父 PID；原 operation_busy、单 oracle、释放后原操作可用 |

不加载继承来的交付/恢复测试来增加 run 数。原文件的类内显式名称清单是套件成员来源，记录完整 test id 与执行数量，不能跳过或标 expectedFailure。

## 3. 不改断言且不批准边界时做不到的项

1. **V3～V9（7 项）**：保持旧 CLI SIGKILL 注入会留下仍工作的后台，锁不会释放，不构成门禁中断；伪造返回 -9 或把断连当已恢复都不可接受。需要 D2 的后台注入和真实结果记录。V1/V2 也需要屏障的 ppid 适配。
2. **R1、R2、R3、R6、R7、R8、R10、R11、R12、R13、R14、R16、R17（13 项）**：当前生产后台没有受控 GateRuntime 注入入口；其正常 Panes 要真实 workspace-write Codex，测试请求与 fixture 事实则是 approval-required 控制线程。只改 state 长度或启动后台不会满足它们。不能把请求改成 workspace-write、模拟一个实际 Codex TUI、继续客户端直接开库或另写测试 server。建议批准 D1/D3；若不批准，主控须决定例外或另切工作，结果明确 INCOMPLETE。
3. **CAS 变异体**：原 C6 在 CAS 启动前便改变基线，会被更早的读回挡住，旧三套通过本身不证明 CAS 的期望旧值有效。继续使用已有 `test_cas_race.py` 的独立外部写入场景，另建后台生命周期子类；原断言不改，作为 35 项之外的必跑补充证据。

目前未发现必须改业务断言才能完成的项目；这里的可行性是源码推断，不是实跑结论。任一真正业务失败或 spec 冲突先保留现场并交主控，不把测试 host 扩成产品兼容路径。

## 4. 红态、绿态、变异体与最小探针

### 红态分开记

- **入口红态（已存在，已回读）**：在 `7bcfe7d9` 的三套主控记录，共 35 项失败于 socket 路径。重现命令为 `python3 evidence/2026-10-10-batch12/T-075/run-acceptance.py <coop|recovery|run> <新的证据目录名>`。这是环境／生命周期红态，不能记成业务红态。原目录和归档不改写。若 D1 改产品，会在冻结的起点副本先记录缺少内部 host 入口；同样仅归类入口红态。
- **业务红态**：适配完整走通之后，使用同一最终候选的隔离变异体，分别由下表独立合同预期拒绝。包括原 C4 的分页坏候选反例，但不以该反例代替三个门禁变异体。
- 先保留各项坏版本证据，再运行未变异候选的相同 focused signal 得绿态；最后才跑当前候选全量 8/9/18 与 CAS 补充。失败原样保留，每次新 label，不兜底重试。

### 最小可证伪探针

| 探针 | 输入与方法 | 通过／失败／停止条件 | 证据与负责人 |
| --- | --- | --- | --- |
| P1：普通交付 | 原 C5，短 state、产品 daemon_start、真实 CLI | 原断言全过且请求事件属于所记后台；入口失败先只修适配，业务失败停止交主控 | worker 准备、执行主控沙箱外运行；`probe-delivery-01/` |
| P2：后台中断 | 原 V3，真实 oracle 屏障、SIGKILL 自有后台、同 state 显式重启 | 原 interrupted/新 ID/新 worktree/孤儿不能满足/新 oracle 全过；所有权不能核对时绝不信号，停止 | 同上；`probe-recovery-01/` |
| P3：编排 host | 原 R6 后原 R1，同一个生产 serve 加受控线程边界 | request_received/result、线程边界日志及真实 Git/SQLite 全链一致；任何客户端开门禁库或 fixture-error 为失败；需要真实模型则停止询问 | 同上；`probe-run-fixture-01/`、`probe-run-01/` |

REALITY GATE：**INCOMPLETE**。D1/D2/D3 和上述实跑未完成。批准后先做探针，不直接以静态可行性宣布 35 项通过。

### 三个变异体

从**同一最终冻结候选**复制完整源码，在隔离副本改以下单点；不改共享 checkout、不切换正式后台、不使用旧变异体源码。保存完整源码、唯一替换命中检查、mutation.patch、启动 argv、实际 loaded core 路径、请求与原断言结果。变异体仅替换后台里的 gate 构造，客户端仍用未变异的最终产品 CLI，生产 server／transport 不变。

| 变异体 | 单点修改 | 必须击中的业务信号 |
| --- | --- | --- |
| fence | 删除 submit 的 `args.fence === attempt.fence` 检查，其余身份检查保留 | 原 C2 的错误 fence 请求不得通过、业务状态与引用不得变化；变异体应在这项合同断言失败，不能在启动／import／socket 阶段失败 |
| CAS 期望旧值 | 只从真实 Git stdin 的 `update <ref> <M> <G>` 去掉 `<G>`，不是移除前置读回或更改最终 CLI | 已有 CASRace：after-read/before-CAS 外部 writer 提交 X，真实 Git 无旧值写入覆盖 X；原“拒绝／保留 X／不能 accepted”断言必须失败；未变异候选同场景通过 |
| 操作锁 | 只删除 `operationLock` 中的 `BEGIN IMMEDIATE`，保留 run 锁、busy_timeout、数据库与门禁行为 | 原 V1 的及时 operation_busy、无第二 oracle、正常 owner 不误中断等断言；原 V2、R18 同类检查可补充。第二请求屏障收尾不得杀掉原后台或把 fixture-error 当杀死变异体 |

每个反事实至少满足：先成功注册、认领/提交并到达目标业务边界；有对应原业务断言失败；没有夹具、import 或入口 errors。若变异体存活或只导致环境错误，记录 INCOMPLETE，先修注入器，不加第二个业务突变凑数。特别记录操作锁变异体在单后台并发中的实际失败，不只检查错误字符串。

### 计划运行命令

下列运行器尚未写入，命令是拟定接口，批准后实现并在 RESULTS 附实际 argv：

```sh
python3 -B workbench/tests/run_daemon_acceptance.py --suite coop --label green-coop-01
python3 -B workbench/tests/run_daemon_acceptance.py --suite recovery --label green-recovery-01
python3 -B workbench/tests/run_daemon_acceptance.py --suite run --label green-run-01
python3 -B workbench/tests/run_daemon_acceptance.py --suite cas --label green-cas-01
python3 -B workbench/tests/run_daemon_acceptance.py --suite coop --test test_identity_gates_and_revocation_reject_old_verified_attempt --mutant fence --label mutant-fence-01
python3 -B workbench/tests/run_daemon_acceptance.py --suite cas --mutant cas --label mutant-cas-01
python3 -B workbench/tests/run_daemon_acceptance.py --suite recovery --test test_live_verify_excludes_verify_and_integrate --mutant lock --label mutant-lock-01
git diff 7bcfe7d9 -- acceptance/test_coop_e2e.py acceptance/test_recovery_e2e.py acceptance/test_run_e2e.py
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

运行收据保存 task/attempt/session、ready_rev、完整候选版本与必要 diff、CLI/Node/Python/Git 版本、依赖位置、技能路径、测试输入、原始命令输出、PID/代次、注入/人工操作、旧/新 state 只读快照和 Git 读回。元数据 task 写 T-075-5；原套件的 T-006/007/008 字段保留原意，不混写为本卡结果。判定来自 unittest 和结构化断言，不能靠正则／关键词猜状态。

## 5. 沙箱外部分、审查与交付

- 本轮只读核对与写计划在沙箱内完成，不请求沙箱外执行。
- 批准后准备 `card-5/outside-sandbox.sh`，它串行运行探针、红态／绿态、35 项与三个变异体，记录每条命令、输出及退出码；以新的运行标签保留全部失败。回复 `T-075 OUTSIDE-SANDBOX READY`，由执行主控运行，不自行升级执行。
- 需要沙箱外：Unix socket listen/connect、后台 node-pty helper 核对、ps 存活观察、自建隔离 repo/worktree 的 Git 元数据写入、自有后台 SIGKILL 与重启。原套件的 git config 仅操作它新建的隔离 repo，绝不写共享仓库或全局配置。
- 启动前核对 `/Volumes/WD-Elements` 是真实挂载、Node 为锁定的 26.5 系列且已有依赖可加载。没有盘／缺依赖就报错，不安装新依赖、不回退内置缓存；本卡不构建 Electron。
- 一次 fresh-context 只读独立审查放在候选冻结、证据齐全后进行，核对实际候选、继承的原断言、三个业务反事实以及后台路径。审查会话不执行被测真实 Codex 回合、不 submit、不集成。按 behavioral-acceptance-review 检查独立 oracle 和 known-bad。审查发现问题先保留红态再修，产品修复仍须主控批准，修复 diff 交主控审，不自行多轮追审。
- 最终 RESULTS 用中文，逐项注明 PASS/INCOMPLETE、原始失败、批准例外、重现命令与证据版本；ticket 只补 Resolution 第 4 条当前证据，保持 open，写“待主控关闭”。地图/README 若因批准的产品边界变化需同步，按范围外 issue 交主控，不自行改。
- a2a git 写操作分别独立执行，只提交自己的文件与获准的 daemon 变更、ticket Resolution，带本 worker 九项尾注；不 push。提交前后保存地图和断言 diff；完成阶段才回复 `T-075 DONE <PASS|INCOMPLETE|BLOCKED> <a2a commit>`。

下一动作：执行主控决定 D1/D2/D3。worker 在 `T-075 PLAN READY` 后停止，不提前实现。
