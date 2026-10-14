# T-077 执行主控决定 03：真实冲突场景第 1 次启动

时间：2026-10-11 16:45 左右；审阅对象：exec/t077 `93094e7b` 的 `evidence/2026-10-11-batch13/T-077/REAL-APPROVAL-01.md` 与 `real-plan-01.json`。

## 批准范围（只此一次）

- Launch 1：`9906fa57-4877-48f9-afb4-c1aceef3edd4`，worktree `/private/tmp/t077-cf-20261011/state/worktrees/T077-real/T-077-9-a1`，Codex CLI 0.162.1，`gpt-6.1-sol`、xhigh、Fast 请求，argv 与三个 Codex hook（UserPromptSubmit/Stop/PermissionRequest → 本 launch 的 `cli.ts signal`）及 Git `core.hooksPath` 环境变量按材料原文。
- 预算：本次最多 2 个主 turn（工作、回执），计入本卡 4 turn 上限。
- 隔离 home `/private/tmp/t077-cf-20261011/codex-home`：只复制 auth.json（0600、不归档）；只信任 `/private/tmp/t077-cf-20261011/repo`；只有 git add、git commit 两条 allow 规则；不复制用户配置、hook、skills、rollout。
- 两回合完成、窗格空闲、领导者身份核对后，向该自建 Codex 领导者发 SIGTERM，并在第二次审批前暂停，保留后台、原 shell 与 home。
- 测试 host 在 createThread 异步上下文内预分配 launch UUID 以提前固定 hook 命令：认可，仅限本测试 host，能力 token 独立随机，attempt/session/fence/原生 UUID 仍由真实门禁与 CLI 产生。

不批准：第 2 次启动（另行审批）、任何权限窗口的代批、重试、补 Enter、额外回合。

依据：ticket T-077 真实冲突验收与任务卡 4 turn 预算；AGENTS.md 真实 Codex 验收的隔离 CODEX_HOME 规则。批准引用：`T-077 controller-decision-03 launch-1`。

## 第 1 次启动读回与第 2 次启动批准（2026-10-11 16:5x）

读回 `real-conflict-01/attempt-1`：run.json stage=awaiting_second_launch_approval、observed_root_turns=2；根 rollout 的 turn_context 两回合均为 cwd=a1、workspace-write、network_access=false，model 记录全部为 gpt-6.1-sol、effort xhigh；relay 交付已处理一次（relay_processed=1，另一次为回执重放）；SIGTERM 前领导进程 51348 为 0.162.1 Codex，之后 native-ended 只剩原 shell 51345、session_ended=true；无权限请求、无人工介入事件。

批准第 2 次启动（只此一次）：Launch 2 `7cb79cbe-a73d-49ce-836a-c43d23f1572c`，worktree `.../T-077-9-a2`，argv、三个 hook 与 Git hook 环境按 REAL-APPROVAL-01.md 原文；最多 2 个主 turn，本卡累计不超过 4；同一隔离 home，历史 rollout 逐字节核对不变；结束后按隔离规则归档并删除整个自建 home（auth.json 不入归档）。不批准重试、额外回合或第三个 attempt。批准引用：`T-077 controller-decision-03 launch-2`。

## 复验实例 r2：第 1 次启动批准（2026-10-11 22:1x）

依据：用户授权 answer `20261012T015257Z-ideation-answer-001`（额外 2～4 真实回合；Codex 一律 gpt-6.1-sol xhigh、普通速度、不传 Fast）。审阅 exec/t077 `f6bc3ed9` 的 `REAL-APPROVAL-02.md`：与已批准的 01 相比只换了实例根 `/private/tmp/t077-cf-20261012-r2`、任务号与 worktree，并去掉 `service_tier="fast"`；隔离 home、信任项、两条 allow 规则、三个 hook、Git hook 环境、停止条件与清理不变。

批准第 1 次启动（只此一次）：Launch 1 `8ee0b73a-c031-46ed-8dd6-5e6490029781`，最多 2 个主 turn（本次新增预算 4 之内），完成后 SIGTERM 自建领导者并在第 2 次审批前暂停。周额度只剩约 1%：额度用尽即停下保存现场，不换账号或模型。批准引用：`T-077 controller-decision-03 r2-launch-1`。

## 复验实例 r3：第 1 次启动批准（2026-10-13 11:0x 本地）

依据：用户授权 answer `20261013T144758Z-ideation-answer-001`（原话"A 再批 2 回合，完整重演 (Recommended)"；r3 共 4 回合）与 `20261013T142903Z-ideation-answer-001`（显式 `service_tier="default"`）。审阅 exec/t077 `2e2291ac` 上的 `REAL-APPROVAL-03-LAUNCH-1.md` 与 `real-plan-03-approved.json`（turn_limit=4）：实例根 `/private/tmp/t077-cf-20261013-r3`（运行前不存在），隔离 home、信任项、两条 allow 规则、三个 hook、Git hook 环境同 r2；argv 含 `--no-daemon` 与 `-c service_tier="default"`；新增 runner 守卫：turn_context/thread_settings 出现非 sol/xhigh/default 立即退出。

批准第 1 次启动（只此一次）：Launch 1 `e9cf7727-772d-41db-bd76-e71ffc2d7e93`，最多 2 个主回合，完成后 SIGTERM 自建领导者并在第 2 次审批前暂停。不批准重试或追加；再不过即停下报告。批准引用：`T-077 controller-decision-03 r3-launch-1`。

## r3 第 1 次启动读回与第 2 次启动批准（2026-10-13 本地 11:1x）

读回 `real-conflict-03/attempt-1`：stage=awaiting_second_launch_approval、observed_root_turns=2；根 rollout 中 model 全为 gpt-6.1-sol、effort xhigh、service_tier "default"；relay_processed=1；SIGTERM 前领导进程 99885 为 0.162.1 Codex，之后 native-ended 只剩原 shell 99883、session_ended=true；无权限请求、无人工介入事件。

批准第 2 次启动（只此一次）：Launch 2 `9b06963e-5718-4286-9dd3-921591a3b339`，worktree `.../T077-real-r3/T-077-12-a2`，argv 按 REAL-APPROVAL-03.md（含 `--no-daemon`、`-c service_tier="default"`）；最多 2 个主回合，r3 累计不超过 4；同一隔离 home，历史 rollout 逐字节核对；结束后归档并删除整个自建 home。再不过即停下报告，不追加。批准引用：`T-077 controller-decision-03 r3-launch-2`。

## 用户决定：选 C，两条受控证明后关票（2026-10-14 UTC 01:16 收到）

依据 answer `20261014T011612Z-ideation-answer-001`（用户原话逐字："C 受控证明后关票，并改角色卡 (Recommended)"，见该条目"## 授权"）。不再跑真实回合（累计 9/10 停在 9）。worker 在真实门禁入口上补：(a) 带不支持尾注（A2A-Fence、A2A-Spec-Rev）的重交被 verify 拒收；(b) 同一重交尾注正确时验收并集成。先有红态：断言须在已知坏实现（放过多余尾注的变体）上失败。之后独立审查、合并（含 R8 与 T-076 审查联合核对），通过即关票，Resolution 按 answer 第 2 条。

## controlled-trailer-proofs-01 运行与读回（2026-10-14 UTC 01:4x）

执行主控在沙箱外运行 `outside-sandbox.sh controlled-trailer-proofs-01`（真实模型 0）：顶层 PASS。known-bad（删去 verify 尾注数量检查的 /tmp 变体）red_confirmed=true，verify ok=true；候选 2/0/0：(a) 多余 A2A-Fence/A2A-Spec-Rev → invalid_trailers、两条 rejected 事件、task 仍 submitted；(b) 同一 C2 源码、钩子生成九项 → accepted，夹具 main 快进到 C2。两例 C2 源码一致，无超 5 MB 文件。

worker 非阻塞问题 ISSUE-dispatch-tier-record（dispatch_intent 速度标签为 fast）：main 的 core.ts 已是 `requested_service_tier: "default"`（随 T-076-2 合入），T-077 变基到 main 时随之解决，合流时核对；不另开 ticket。其 inbox 投递失败源于本分支既有悬空 reply_to，变基后由 main 的收件箱为准。

## rebase 完成与 rebase-final-01 批准（2026-10-14 UTC 03:0x）

变基：worker 逐停解决冲突（停 1：5 文件；停 4：3 文件取 main 侧；停 5：panes.ts），执行主控在沙箱外运行 rebase-continue-01/03/05；第 3 个提交的 add/add 冲突是我自己的 controller-decision-03.md，取 main 侧超集。之后再变基到 main 5e057109（只多 T-078 决策日志）。冻结 c3eb705c。批准运行 `rebase-final-01`（33 个子阶段，含三条合流组合路径的变体红态、T-076-2 最终入口联合核对，模型 0）。

## worker issue 20261014T023857Z（审查 worktree 未接 S3 命名与结束清理）

核对：spec 第 4 节要求验收/审查目录有用途与序号、结果存库后删除；main 的 requestReview 建 `review-<UUID>`，reclaimReview 不删 worktree。PLAN 将其交 T-076-2，T-076-2 关票时未接入——跨卡遗漏，属已批准 spec 内的缺陷，不是新目标。处置：并入 T-077 合流前完成（ready_by executor 级缺陷处理）：先受控红态（回收后 review worktree 与目录仍在），再修，重跑受影响检查，再独立审查。T-076 的 Known limits 需补记此项（转构思主控）。

## rebase-final-01 读回（2026-10-14 UTC 02:54）

INCOMPLETE，rc=1：3 条 joint 变体红态、7 条冲突红态、joint-candidate 通过；s3-all 24/25，test_integrated_run_cleanup ERROR（legacy_quality_driver finalize_run："Run review binding differs from the submitted candidate."），其后子阶段未跑。不重试；交 worker 诊断（夹具或产品），与审查 worktree 命名/清理缺陷一起修，准备 rebase-final-02。

## rebase-final-02 批准（2026-10-14 UTC 03:5x）

审阅 7b3463c4（夹具 driver 把 reviewing/null 误判为绑定不符；产品绑定正确，非产品缺陷）与 5d0bf1e8（审查 worktree 命名 `<task>-a<N>-review-<K>`，结果入库且 reviewer 停止归档后核对身份/HEAD/干净再删并读回，事件追加，不改 review 对象；脏/未知保留上报）。提交无超 5 MB 文件。批准运行 `rebase-final-02`（39 子阶段，含修前副本上四条审查清理反例，模型 0）。

## rebase-final-02 读回（2026-10-14 UTC 03:34）

INCOMPLETE，rc=1：driver-readiness 通过后，runner 重建修前产品副本时拒绝 git archive 中 workbench/hooks/ 的 26 个指向 hook.py 的符号链接（"Unexpected preimage archive entry"），业务阶段未运行。runner 缺陷，非产品；交 worker 只改 runner（仅放行同目录 hook.py 符号链接），候选不变，另起 rebase-final-03。

## rebase-final-03 读回（2026-10-14 UTC 04:02）

INCOMPLETE，rc=1（候选 5d0bf1e8，runner e5af8193）。审查清理 4 红态/候选绿、joint 3 红/候选、冲突 7 红、s3-all 25、coop、recovery 均按预期；run 套件 11/18 执行、1 error：acceptance/test_run_e2e.py:549 claim(overlap_reason=…) 与 daemon_acceptance_adapter.claim 签名不符（合流夹具缺口，非产品）。交 worker 修 adapter（overlap_reason 经真实 CLI 传门禁）并查明 11/18，另起 rebase-final-04。

## rebase-final-04 读回（2026-10-14 UTC 04:25）

INCOMPLETE，rc=1。新通过：run 18（无 failfast）、cas、cards。停在 relay-conflict：test_task_cards_e2e.commit 调 self.managed_trailers，RelayConflict 无此方法（合流夹具缺口，非产品）。要求 worker 先对其余未运行子阶段做静态/轻量预检一次找全同类缺口再起 rebase-final-05。

## rebase-final-05 读回（2026-10-14 UTC 04:56）

PASS（产品 5d0bf1e8，夹具 be91b3c0，checkout 79ef7b7f，模型 0）。39 子阶段全部按预期：审查清理 4 红 + 候选、joint 3 红 + 候选、冲突 7 红（red_confirmed）、s3 25、coop 8/8、recovery 9/9、run 18/18、cas 1、cards 15/15、relay-conflict、尾注候选 2、identity 4、shutdown 4、T-076-2 tracer/wide/审查故障/协议控制/来源冻结、relay core/cli/scope/全库去重变体、native-final、dispatch-state、panes 4。relay-core/native-final/dispatch-state 的子报告无 status 字段，仅 exit 0，交独立审查直接核对。下一步：fresh-context 只读独立审查（gpt-6.1-sol xhigh）。

## 独立审查 01 读回（2026-10-14 UTC 05:1x）

reviewer（fresh-context，请求 gpt-6.1-sol/xhigh，tier 未观察）：INCOMPLETE。确认 (a) 合流保留两卡语义、(b) 两处衔接、(c) 审查 worktree 命名清理、(d) 夹具未放宽断言、(e) relay-core/native-final/dispatch-state 原始结果确为通过、(f) 审查清理 4 与 joint 3 与 relay 全局变体命中目标断言。唯一发现 P2 F1：conflict-red-06/07 停在重交前置（candidate_conflict），未到达禁止路径/外来尾注的目标断言，分类器误计红态。无产品缺陷。接受；交 worker 绑定目标断言标识、为 06/07 写定向变体、重跑 7 条冲突红态（conflict-red-final-01），之后对差异做 fresh-context 复审。

## conflict-red-final-01 被系统中止（2026-10-14 UTC 06:2x）

执行主控在沙箱外运行 `conflict-red-final-01`（产品不变，夹具 fba6ebb5）。Claude Code 因系统内存严重不足回收了该后台命令；已完成 red-01/02/03（均 TARGET_FAILED，按各自前置清单），其余未运行。部分输出原样保留在 outside-conflict-red-final-01/，未发现残留测试进程。该结果不完整，不计入验收；是否及何时重跑等用户指示（同名输出目录已存在，重跑须用新目录）。T-078 的轮询器同时被回收，worker 本身不受影响。

## 第二次重启后（2026-10-14 本地 08:3x）与 conflict-red-final-02 批准

用户原话（经构思主控逐字转述）："刚刚重启了，继续，不要并行太多，不知道是终端内存泄露了还是并发太多了。" 并发上限：同一时刻 1 个 worker、1 个重型测试，不同时开 reviewer 与 worker，不开 monitor；先 T-077，T-078 待 T-077 合并后再起。Herdr 又把 08:15 的两个新会话以裸 resume 恢复（wF:p3M 01a13a55-d655…，wF:p3N 01a13a55-da30…，均显示 "Conversation interrupted"）；核对无未提交产品改动（T-077 已提交 628234b7 = conflict-red-final-02 阶段；T-078 留有未提交的 BLOCKED 报告与 issue，原样保留）后关闭两窗格，15 秒内无再拉起。另两个裸 resume（01a13800…、01a138b2…）属用户其他工作区，未动。空闲内存 59%，无 worker 在跑。依 answer 20261014T121326Z（"重跑 (Recommended)"）批准并运行 `conflict-red-final-02`（产品 5d0bf1e8 不变，模型 0）。

## conflict-red-final-02 读回与复审安排（2026-10-14 UTC 12:3x）

PASS，rc=0（产品 5d0bf1e8、夹具 178d15f3、checkout 628234b7，模型 0）。red-01～07 全部 TARGET_FAILED；06/07 分别失败于 "Conflict rework still rejects the forbidden path at verify"/"...foreign trailer at verify"，前置清单含 conflict_delivered、explicit_resubmitted、target_verify_executed；候选 PASS。F1 证据缺口已补。开一个全新 worker s13-t077r（wF:p3P，launch-a85f0cb6…，空闲内存 68%）提交结果并以 spawn_agent 做 F1 差异的 fresh-context 只读复审（同一 Codex 进程，worker 复审期间不作业）。

## 复审 02 读回（2026-10-14 UTC 13:2x）

reviewer（fresh-context）：本次限定复审 NO_GO，原 F1 已解决（七条红态各命中目标、前置齐全且在目标前；06/07 定向变体只破坏对应守卫、分别在 :886/:897 失败；候选七项通过；产品与夹具冻结身份一致）。唯一新发现 P2：目标通过后普通断言失败时分类器标 TARGET_PASSED 而非 NOT_COVERED；不影响已记录红态与候选结论。接受；交 worker 先红后绿修分类器，并对已保存原始结果离线重分类，证明结论不变，无需重跑沙箱外阶段。

## 验收与关闭（2026-10-14 UTC 13:2x）

分类器修正（65f441e5，红：修前 TARGET_PASSED≠NOT_COVERED；绿：9/9；14 份原始结果离线重分类不变）与其审查 PASS 0 发现（baf5e769）。执行主控亲跑分类器检查 9/9 OK。分支变基到 main（25 个提交，无冲突，产品/验收文件与 5d0bf1e8 逐字一致），main 快进至 60eb6ac5。T-077 ticket 标 closed、验收 7 项勾选、Resolution 补写；打分 score-ac5390d8…（边界 3、工程 2）。issue 20261014T023857Z 关闭（disposition 带依据）；blocking issue 20261011T134711Z 转构思主控待用户关闭（20261014T131942Z）。project_map status：Problems 0、Stale 0。
