# T-082 独立审查 01（最终）

STATUS: NO_GO

TARGET: `f589d19387c2dcc5eeda6505423d794f2b3be1f3`；产品代码检查点 `7f2bd40611e920cb962ba20f17b58bb12a9acab0`；起点 `451be8462c85fd08b997cb85453188a8e5751c9d`。

最终结论为 **NO_GO，需修复**。第 14 段复现了结束边界核对前仍可集成的 P1：审查目录已有外部改动，但报告刚入库就使任务成为 verified，integrate 成功前移 main；事后回收报错时任务仍是 accepted。第 15 段另确认 review_requirements 的副本路径可以被改写后正常入库，是 P2 元数据契约缺陷，没有证明沙箱越界写入成功。

独立脚本第三次运行的第 01～13 段均符合预期：指定回归通过，5 个错误实现都在对应业务断言处被检出。第 14、15 段是 contract_failure，不是探针超时、依赖错误或脚本清理错误。被试的两项现有结束测试仍放过 M3，且既有完成条件漏掉了上述两种真实失败场景，故完成条件充分性判断为“需修复”。

本次最终原始输出为 `/private/tmp/r82-review01-UnlqXU`（下文简称 R），完整终端输出为 R/controller-run.log。报告内只保存核对后的摘要及原件路径，没有复制大块原始证据；前两次脚本缺陷现场继续保留。脚本的总状态字符串 INCOMPLETE 是其对未满足预期用例的统一标记；本审查依据已确认业务反例给出 NO_GO。

## 范围与独立性

- 已读主 checkout 的 reviewer 角色卡、T-082 ready_rev 1、D3 决定、任务卡 T-082-1、两份主控决定记录；未读作者会话历史。
- 目标：核对七条 Acceptance、产品边界与报告契约、T-076 断言变更，以及完成条件能否拒绝明显错误实现。非目标：修复、提交、集成、真实模型复验、改变验收条件。
- Ubiquitous language：`review.workspace` 为门禁拥有的审查 Git worktree；`review.candidate_workspace` 为 reviewer 可写的一次性候选副本；worker worktree 和共享仓库是其他受保护对象，不能混称“审查副本”。
- Tracer bullet：已有薄切片经过 CLI→daemon→门禁→Panes→Stop/relay→持久化→回收；真实权限效果另按真实原生工具回执核对，受控 PTY 不代替沙箱证明。
- Deep modules：复用现有门禁和 Panes，未另建变异平台或平行集成入口；下面单列为变异锚点而增加的无效条件表达式。
- 开始时 `git status --short` 无输出；HEAD 与指定候选一致。`git diff --quiet 7f2bd4061..f589d1938 -- workbench/src` exit 0。检查点之后新增了父版本红态测试与证据，不能说测试文件也完全未变。
- 会话开始与最终核对时运行指定 `project_map.py status --root .`，均 exit 0、Problems (0)、Stale living docs (0)。HEAD 始终为冻结候选；独立运行使用的 core、Panes、qualityProtocol、daemon、relay 五份源文件已与冻结提交逐字核对一致。未改地图、票据、源码或全局配置。

## Acceptance 七条核对

以下 PASS 仅指对应具体检查，不能覆盖第 4 条已复现的提前集成缺陷；整票 NO_GO。

| 条款 | 当前核对 | 证据与限度 |
| --- | --- | --- |
| 1. 起点红态 | PASS（起点行为） | `git show 451be8462:workbench/src/gates/core.ts` 与 `panes.ts` 确无完成条件充分性/2～5 个变异要求，仍在审查 worktree 用 read-only；[static-red.json](red-state/static-red.json) 五项为 true。历史只读事实见下文原件核对。 |
| 2. 新边界及四种启动拒收 | PASS（当前行为及旧版本反事实）；时间顺序有保留 | [outside-command-02-02/controlled/run.json](outside-command-02-02/controlled/run.json) 的 tracer 和四种变体均 PASS。[outside-command-10-01/run.json](outside-command-10-01/run.json) 三案均为 `contract_failure / T082-LAUNCH-REFUSED`、verify `ok:true`、task `reviewing`，不是依赖或夹具失败。readonly 起点红为旧启动及真实只读事实，候选绿为对应拒收。补证明确写明是修复后的旧版本重建，不能改称时间上先运行的红态。 |
| 3. 真实 Codex 权限边界 | PASS（已记录真实边界；结束核对另用 round-2） | 第 1 回合原始原生工具输出证明副本写入及测试 exit 0、外部三处拒写 exit 1、共享 update-ref exit 128、域名与直连 IP 请求失败；已只读扫描外置原始 rollout 的 context 和工具标记。第 1 回合最终协议失败，不能称完整门禁通过。 |
| 4. 结束核对作废与正常删除 | NO_GO（存在提前集成窗口）；正常回收正例 PASS | 已有脏目录作废与 round-2 正常删除均成立；R 的 01、03、04 段还通过脏目录/改 HEAD/共享 refs 反例。第 14 段则证明结论尚未完成结束核对就可被集成使用，后置报警未撤销 accepted。不能据普通顺序正例宣称这一条完整满足。 |
| 5. 偏弱任务卡真实交付审查 | PASS | round-2 的 `verify.json` 保存目标“两项都必需”，完成条件仅执行 `acceptance/weak.py`。`report-readback.json` 含独立节和 5 个变异：value 错内容/缺 LF 被拒；details 缺失/错内容/缺 LF 均逃逸。reviewer 判需修复并准确指出缺 details 的验收。模型判断如实记录，不据此要求门禁评价内容。 |
| 6. 真实回合 ≤4、argv、home 删除 | PASS（已记录 2/4） | 两个实际 reviewer 各 turn_limit=1，完整 argv 与 shell argv 在各回合 `launch-readback.json`。前两次 round-1 前置失败未释放有效任务回合。两个 home 删除收据为 absent；本次只读确认 launch 所记 CODEX_HOME 当前均不存在。未复制凭据、未新增真实回合。 |
| 7. T-076 三性质、T-077、地图 | PASS（指定性质与四案独立复验）；完整旧 runner INCOMPLETE | R 的 02 段独立通过 wrong_candidate/reused_native/writer_cannot_review 和 strict JSON，03 段独立通过 T-077 四案；均使用冻结候选源文件。既有历史记录亦一致。旧质量/launch-policy runner 的拒收见下文；不称旧 runner 全绿。地图 0 problems、0 stale。 |

### 旧版本红态的范围

`outside-command-10-01` 的起点为完整 `451be8462c85fd08b997cb85453188a8e5751c9d`：wrong-workspace 不改旧产品；network-enabled/tmp-writable 只改变临时 `panes.ts` 的相应启动输入，旧 gates 不改。三项均确认释放并到达受控 busy reviewer 后，才执行拒收断言。因此能证明旧门禁没有新限制，不能证明旧 read-only 沙箱实际允许网络或 tmp 写入。

该补证的 `counterfactual_timing` 原文是“reconstructed after the fix on the starting revision; not an earlier chronological run”。任务卡写“红态先于修复、各先见红”；若按字面时间顺序验收，这三项仍不能标成已满足。它们提供的是有效旧版本反事实。这里不替主控豁免或改写时间要求。

`RESULTS.md` 早于 `f589d1938` 的补证，仍把三项红态列为缺口。主控记录 02 的 #49/#50 和新增红态目录补齐了反事实证据；应合并阅读，不能只转述旧 RESULTS 的缺口，也不能抹去补证发生的时间。

### 历史只读原件与真实边界原文

历史原件位于主 checkout 的 `evidence/2026-10-11-batch13/T-076/card-2/outside-p-review-02/`。本次读取了 `run.json`、`sentinel-result.json`、`launch-before-spawn.json`，并直接从 `fixture-artifacts.tar.gz` 读出哨兵内容；与 [t076-readonly-readback.json](red-state/t076-readonly-readback.json) 保存的内容逐字相同。原始记录为 write_attempts=1、denied=true、errno=1，launch 为 `aae6f34a-072c-4740-9ba6-5c4452fe110e`；历史 product_status=INCOMPLETE 保持原义。这里只继承“旧 reviewer 拒写”事实。

第 1 个真实新回合使用产品 `0dd00d09d`，launch 为 `4f1c53ae-5d54-4cfe-b248-46608d94d171`，候选为 `1ff3965e716e3709e0a0749420fb1f7176010359`。已读 [原报告](real-boundary-readback-01/report-from-rejected-stop.json)，它含充分性判断、三个实际失败变异和全部边界探针。实际工具原文分别在：

- [line-39](real-boundary-readback-01/native-tool-output-line-39.txt)：副本创建文件和运行 `./test-command.sh` exit 0。系统 Python 启动器有 tmp 缓存拒写诊断，但测试实际执行并 exit 0。
- [line-46](real-boundary-readback-01/native-tool-output-line-46.txt)：审查目录、worker worktree、共享 `.git` 新建文件各 exit 1，原文均为 `Operation not permitted`；共享 `git update-ref` exit 128，原文 `cannot lock ref`；curl 域名 exit 6。
- [line-53](real-boundary-readback-01/native-tool-output-line-53.txt)：完成条件基线 exit 0、三项错误变异各 AssertionError/exit 1、恢复后 exit 0。
- [line-62](real-boundary-readback-01/native-tool-output-line-62.txt)：curl 直连 `1.1.1.1:443` exit 7，`Failed to connect`。

外置原始压缩 rollout 路径为 `boundary-readback.json` 的 `sources.rollout`，本次确认文件存在并只读扫描：原生 context 的 cwd 为该副本，model/effort 为 gpt-6.1-sol/xhigh，sandbox_policy 为 workspace-write、network_access=false、两个 tmp 排除开关 true。不是只相信模型报告中的 PASS。

第 1 回合在 review_submit 模板/严格解析契约处失败，未正常回收。`0dd00d09d..7f2bd4061` 的 panes 无差异，core 的后续改动是报告模板及 reviewEvidence 接入；边界检查未再改。第 2 回合在 `7f2bd4061` 上经 Stop→严格解析→relay→review_result→回收→结束核对→删除完成。

round-2 的 `end-readback.json` 保存实际 Git 回执，生命周期顺序为 seq 94 review_result、115 review_candidate_copy_removed、129 review_worktree_removed、130 review_reclaimed，候选 `af586aed2709b46768f90e334156cf9197d0115e`。worker 与共享 `.git` 哨兵直接前后相同；审查目录删除后无直接 after 哨兵，使用删除前 HEAD=C、clean 与受控文件内容证明，不声称有删除后的直接读回。

两次 `launch-readback.json` 记录 codex-cli 0.162.1、gpt-6.1-sol、xhigh、service_tier=default、`-a never`、副本 `-C`、workspace-write、关闭网络/proxy、排除 `/tmp` 与 `$TMPDIR`。请求 tier 不是供应商实际 tier 的证明。home 的规则、信任文件及删除收据已读；不把文件清单当作读取过 auth 内容的证明，本次没有读取 auth。

## 产品差异与结构核对

核对命令：`git diff 451be8462..7f2bd4061 -- workbench/src`。范围为 core、Panes、qualityProtocol、relay、contracts 五个文件。

| 位置 | 已核实的实现 | 审查判断 |
| --- | --- | --- |
| `core.ts:2085` 起的副本建立 | 新副本位于 state/review-copies/review_id，拒绝已存在目标；从候选 detached worktree 复制，省略 `.git`；内部 symlink 解引用复制为普通内容，外部/失效链接拒收；复制后再次拒绝 symlink | 单一副本路径，不是 worker worktree 或审查目录本身；未引入 Git 兼容路径。链接策略与 D3 边界一致。已有 copy probe 的 `outside-command-04` 成功记录及实现均已读。 |
| `core.ts:2134` 启动核对 | launch 的 role/review/verification/session/thread/attempt 绑定，workspace、实际 argv `-C`、workspace-write、network/proxy false、两个 tmp 排除标志、独立空 home、无 GIT_CONFIG_*、无 resume/fork | 不是仅改启动文本；核对在创建后和收报告时均调用。参数检查是自有生成 argv 的精确成员检查，不应扩大声称能解析任意冲突重复配置。 |
| `core.ts:2309` 结束核对 | 独立副本身份、共享 refs 快照、审查 detached HEAD=C/clean/登记、worker 固定路径/分支/HEAD=C/clean/登记 | 普通回收顺序可拒绝异常；第 14 段确认这些检查晚于可用的集成机会，且已经 accepted 后不会作废任务，见 P1。 |
| `core.ts:2337` 清理 | 核对边界后记 intent，rmSync(force:false)，独立确认不存在，再记 removed；随后移除 Git 审查 worktree | 不吞删除错误，不用“发出事件”等同实际删除。本次 M5 删除实际操作和确认后，外部路径断言已检出假 removed。 |
| `qualityProtocol.ts:33`、`relay.ts:74`、`core.ts:3448` | 模板、严格 parser、relay allowlist、gate、结果类型均接上 review_requirements/report；report 必须是非空对象，且含“完成条件与变异检查”键 | 修复了第 1 回合实际协议错配。键值允许 null 是已明确的只查键存在契约，不评价模型判断。第 15 段确认 workspace 只查非空，未与本次副本绑定，见 P2。 |

新增 symlink catch 将底层失败转为明确 Refusal 并带原因，没有吞异常或返回默认成功；已有 request/reclaim catch 保留失败并上报。未发现新增 fallback、重试、旧 read-only 兼容分支、双写或平行门禁 API。`realPathLeaf` 放宽的是父目录路径的真实化处理，仍要求叶节点不是被替换的链接；不据此声称消除了所有文件系统并发变更。

## 已确认发现（按严重度）

1. **[P1] `workbench/src/gates/core.ts:3452`、`:2158`、`:3580`：审查结束边界未完成就允许集成，事后失败不能使已接受的结论作废。** 收到有效报告时立即变为 verified，requireReviewed 仅检查报告及身份绑定，不要求结束核对完成。直接调用者 `workbench/src/daemon.ts:187` 在 signal 连接 close 后才安排 reclaimReview；在这之前操作锁已释放。第 14 段通过真实 socket 延迟客户端关闭，在审查目录已有外部改动的条件下，使用原 integrate 入口取得 ok:true、task accepted，并实际前移 main。关闭连接后才产生 review_lifecycle_failed；`core.ts:2174` 排除 accepted 状态，所以 current:false，任务仍 accepted/review passed。**这是本候选的阻断项。** 最小纠正方向是在现有唯一门禁中，把本 review 的结束核对完成设为可集成的必要前置条件，持锁核对；收下模型报告本身不能使这份结论提前获得集成资格。无须引入平行 API 或后置自动回滚。
2. **[P2] `workbench/src/gates/qualityProtocol.ts:38`、`core.ts:3448`：review_requirements 的副本路径未与门禁请求绑定。** 实际请求明确要求该字段原样返回，但 parser/gate 对 workspace 只查非空。第 15 段只把 workspace 改成夹具的 wrong-copy，其余身份、候选、结论与 report 形状合法；gate 正常保存错误路径，task verified、review passed，并正常回收。建议 gate 将机械请求元数据与本 review.candidate_workspace 比较后再保存，不评价模型报告中的判断。此缺陷影响审查元数据与可追溯性；没有发生沙箱外写入，也不说明真实启动 cwd 已改变。
3. **[P2] `workbench/tests/test_t082_review_boundary_e2e.py:74` 的结束核对负例覆盖不足，完成条件需补生产门禁反例。** 第 10 段把共享 refs 比较移除，候选现有的 tracer_review_copy 和 external_review_boundary_invalidated 两案仍全部通过；第 11 段使用独立 refs_changed 才在 REVIEW-REFS-INVALIDATE 检出该错误实现。另两个原候选反例（第 14、15 段）也不在现有检查中。`test_t082_real_readback.py` 的 shared_refs_changed 是合成读回分析器输入，未调用生产门禁，不能补称它已检出 M3。应把共享引用变化、核对完成前调用 integrate、请求元数据被改写的场景接进现有真实 CLI/daemon 门禁用例，以相应单点错误实现验证它们能失败。本审查不修改测试或实现。
4. **[P2] `workbench/tests/run_t076_launch_policy.py:77`：将默认 tier 负例换成副本边界失败点，不能继续证明该负例。** 父版本预期为 TRACER-REVIEWER-DEFAULT-ARGV，候选改为 TRACER-REVIEW-COPY-ARGV。旧快照即使补上 default tier，仍可能先在 D3 边界断言失败。因此这行不是被 D3 取代的“只读断言”；它改变了另一个要求的观测点。[T076-D3-ASSERTION-MAP.md](T076-D3-ASSERTION-MAP.md) 对“父快照不含 D3”的解释成立，但不能推导出默认 tier 负例已重新证明。当前 runner 本就 INCOMPLETE，没有将它写成已发生的假绿或产品 tier 缺陷；未来应让该负例只缺 default override、其余 D3 边界有效，仍在默认 tier 断言处失败。
5. **[P3] `workbench/src/panes.ts:156`：相同分支的条件表达式不应只为字符串变异锚点保留。** sandboxMode、networkAccess、networkProxy 两侧完全相同，没有产品决策，却让生产代码表达出并不存在的差异。`run_t082_boundary.py` 和两个 T-076 runner 依赖这些精确源码字符串。建议生产路径写真实常量，变异夹具改真实参数或限定在测试输入层；两个真实不同的 tmp 排除分支可保留。此项是维护成本，不是已发生的权限失效。

## 第 14 段：结束核对前集成的证据摘要

原件为 R/14-结束核对前集成窗口/result/integration_before_end_check/ 下的 `integration-before-end-check.json`、`after-release.json`、`case.json`、`database-readback.json`、`git-readback.json`、`cleanup.json`。

未改门禁、daemon 或其回调，也未伪造 gate 返回；受控边界只替换 PTY/process/native 事实。探针先在审查 worktree 写入 independent-external-change.txt，发送身份有效的 Stop 报告并读到 ok:true/completedReview，保持自己的 socket 写半边打开。产品以 connection.close 为回收触发条件，故此时明确尚无 review_reclaimed。探针随后通过正常 executor CLI 调用 integrate，评分文件是合法夹具输入。这个暂停点用于确定性暴露产品允许的状态窗口，不是超时或测试分支。

| 观察点 | 实际记录 |
| --- | --- |
| task / attempt / review | fixture-20261016-1 / 74aeeb57-3a32-4d3d-a777-bf8eb9f72bd7 / 3da99167-5722-493d-a6b0-349691552864 |
| 集成前 | task verified、review passed、verdict 可合并；审查目录的外部改动仍存在 |
| 原 main G | `f99ab1df6f4c0b587afbfa7fb015904016a717da` |
| 候选 C / 集成结果 M | `e70e8adfdf0f0f493d467ee834deaf86e411dfaa` |
| integrate 回执 | command-0032.stdout.bin，exit 0、ok:true、task accepted；integration_intent completed；Git update-ref transaction 的 start/prepare/commit 均 ok |
| Git 独立读回 | refs/heads/main 实际为 M；不是只观察 task 字段 |
| 关闭连接后的失败 | review_lifecycle_failed，phase reclaim，error review_shared_refs_changed，current:false；task accepted、review passed 未作废 |
| 失败点和清理 | contract_failure / REVIEW-END-BEFORE-INTEGRATE；cleanup_failures=[]、host_exit=0 |

事件顺序为 seq 95 review_result（03:57:44.991Z）→100 integration_intent→134 integrated（03:57:45.343Z）→139 review_lifecycle_failed（03:57:45.531Z）→140 issue_issue。结束核对先看 refs，所以这次事后首先发现的是集成自身造成的 main 前移；还没走到脏审查目录检查。不能把事后报警解释成已成功挡住该次集成。

精确 integrate argv 在原件 case.json 的 command 32；入口为冻结 source/workbench/src/gates/cli.ts，state 为 `/private/tmp/q76-s3vxldvj/c-g_u4mc3m/state`，带上述 task/attempt 及该夹具 executor-score.json。全部 Git 副作用仅发生在这份新建的隔离夹具仓库；项目 main 和候选未被修改。

## 第 15 段：请求元数据改写的证据摘要

原件为 R/15-review_requirements副本绑定/result/requirements_workspace_changed/ 下的 `requirements-workspace-readback.json`、`command-0030.stdin.json`、`command-0030.stdout.bin`、`database-readback.json`、`cleanup.json`。

实际产品 dispatch 中的模板 workspace 为 `/private/tmp/q76-emo4err0/c-ohmdc2ta/state/review-copies/7bc8ef7a-7173-4f23-8ce7-62d562d0f725`，同一实际提示明确写“身份字段和 review_requirements 原样返回”。探针只将该字段替换为 `/private/tmp/q76-emo4err0/c-ohmdc2ta/wrong-copy`。Stop signal command 30 exit 0、stdout 为产品成功形状 `{}`；随后状态 task verified/review passed。持久事件 seq 95 review_result 的 result.review_requirements 仍保存 wrong-copy，seq 129 正常 review_reclaimed。

结果为 contract_failure / REVIEW-REQUIREMENTS-WORKSPACE，cleanup_failures=[]、host_exit=0。判断依据是错误元数据实际入库，而非仅要求必须采用 paused 这种特定拒收方式；实现即使用另一种明确拒收状态也应通过本契约。这里承认的缺陷范围是请求元数据与副本绑定不一致，不据此声称原 ticket 要求平台判断变异内容真伪。

## 完成条件与变异检查

**变异检查执行 PASS（5/5 在正确失败点检出）；完成条件充分性需修复。** 五个错误实现只在独立脚本创建的 `/tmp/r82-review01-UnlqXU` 副本中构造，没有修改冻结候选。对照和变异使用冻结的原测试；共享 refs 的额外独立预期直接来自票据结束核对要求。只把 contract_failure/预期业务断言计为检出，未把脚本失败、缺依赖或清理失败计入。

| 错误实现 | 对应检查/命令（完整 argv 由脚本记录） | 预期业务失败点 | 当前结果 |
| --- | --- | --- | --- |
| M1：门禁不核对 argv `-C`；外部输入为错误 `-C`，其余 launch 元数据正确 | 第 06 段正确门禁对照；第 07 段 `test_t082_review_boundary_e2e.py --case launch_boundary_refused` | `T082-LAUNCH-REFUSED`，必须是 contract_failure | PASS：对照 exit 0；M1 exit 1，恰在该断言失败，cleanup_failures=[] |
| M2：门禁不核对 exclude_slash_tmp；外部输入放开 tmp | 第 08 段正确门禁对照；第 09 段同一启动拒收用例 | `T082-LAUNCH-REFUSED` | PASS：对照 exit 0；M2 exit 1，恰在该断言失败，cleanup_failures=[] |
| M3：结束核对漏掉共享 refs 比较 | 第 10 段运行候选现有 tracer/脏目录用例；第 11 段运行独立 `refs_changed` | `REVIEW-REFS-INVALIDATE`；原实现第 04 段通过相同独立检查 | PASS（独立反例检出）：04 exit 0，11 exit 1/对应 contract_failure；10 的两项原用例仍 exit 0，是明确的覆盖缺口 |
| M4：report 缺少必需节仍接收 | 第 12 段原 `test_t082_review_protocol.ts`，输入为已记录真实报告的派生缺节对象 | `Missing expected exception: T082-REPORT-SECTION`；候选第 05 段通过 | PASS：05 exit 0；12 exit 1，原五项前置检查先通过，恰在缺节应抛错断言失败 |
| M5：副本不删且伪记 removed | 第 13 段原 `test_t082_review_boundary_e2e.py --case tracer_review_copy` | `T082-COPY-REMOVED`；观察真实路径，不能只信事件 | PASS：候选 01 段同案通过；13 exit 1/对应 contract_failure，cleanup_failures=[] |

脚本完整入口：`bash /Users/luckye/Documents/Code/a2a-wt-t082/evidence/2026-10-15-batch15/T-082/REVIEW-OUTSIDE-01.sh`。每次创建新输出目录，各段打印段名、输出路径和退出码；保留 exact argv、stdout/stderr、run.json、assertion 与 Git/SQLite 读回。成功停止后只清理本次凭据列明的请求目录；测试仓库及失败现场保留原路径，避免移动破坏 worktree 指针。脚本不安装依赖、不构建、不使用用户 auth、不调用真实 CLI 模型；受控 executable 只回版本号。

每个错误实现的精确 before/after 记录在 R 下对应 M1～M5 的 `.changes.json`，其实际 argv、exit、失败 ID、状态和读回在各段 command.json、assessment.json、result/run.json 中。所有五个 source 变异都已检查到预期失败点。第 10 段绿而第 11 段红，结论必须是“被试的原结束测试漏检 M3，独立反例检出”；不能混称原测试本身足够。

第 14、15 段使用未修改的冻结产品，各增加一个外部输入/时序变化，均失败于具体业务契约。它们加上 M3 的逃逸证明现有完成条件仍需补充，不能因五个选定错误实现可由原测试或本次新增独立预期检出，就宣布所有验收条件充分。

## T-076 旧 runner 证据审计

**断言替换：部分成立，不能一概说全部是只读断言。** tracer 的旧 read-only argv 断言反转为副本 workspace-write/network/tmp，新副本实际 `-C`、无 `.git`、session/thread/home 分离、无 GIT_CONFIG_* 等检查并存；旧 reviewer-writable 变异反转为 reviewer-readonly，这两类是 D3 的直接替换。review_packet 与 legacy driver 补协议字段，是新 report 契约的必要夹具适配。默认 tier 负例改观测点的问题见 P2；worker/default tier/priority 的其余显式断言未被删除。

**质量 runner 拒收：证据成立，实际原因不是 D3 tracer diff。** `run_t076_quality_green.py` 的 a7f4cc30 锚点及审计分支未改。读回 `outside-command-06-01/t076-quality-source-audit/commands.jsonl`：命令 1～4 均 exit 0；命令 3 的当前工作区源码 diff 非空只被记录；真正拒收条件是命令 4 的 acceptance diff stdout 非空（23,638 字节，涉及 test_coop_e2e.py、test_run_e2e.py）。run.json 在任何业务 step 前以 `Source audit failed or original acceptance assertions changed.` 结束。主控记录 02 的早期“D3 必须替换只读断言、属预期后果”不是本次实际触发条件；RESULTS 和对应表后续纠正了这一点。本审查不迁移锚点、不豁免审计、不把旧 runner 标 PASS。

**launch-policy 的 main 既有夹具问题：证据成立，业务结论仍 INCOMPLETE。** `outside-command-08-01/command.json` 记录实际运行主 checkout 的 runner、exit 1；其 run.json 无 source changes。子用例 `worker-missing-override-red/run.json` 为 harness_error：旧快照的 card_save 返回 invalid_task_card/card/Fields do not match schema，当前夹具含 oracle_paths，未到 TRACER-WORKER-DEFAULT-ARGV。旧快照确无该字段；当前 T-080 夹具有该字段。它证明该旧 runner 在未包含 T-082 的 main 上也失败，不证明任一启动策略负例成功。不能借此免除候选指定三性质的回归；那些性质已有单独本候选路径证据，本次独立脚本亦已复验通过。

## 限制与后续判定

- 独立 5 个变异、共享 refs 生产反例、提前集成及 requirements 路径输入探针均已执行并读回；第 14、15 段确认产品问题，不得集成本候选。修复与新增回归由执行主控另行派发，本 reviewer 不实现或复用这次结论替修后候选背书。
- 已记录的真实新边界失败/成功只覆盖两次真实会话，不支持可靠性、成本、吞吐改善结论。真实权限结果与受控逻辑结果分别记账。
- 对“时间先红”的字面要求保留事实；不能用修复后重建旧版本冒充当时已运行。旧 runner 的待决锚点及夹具问题保持 INCOMPLETE。
- 本次只写此报告和配套脚本。未创建子 agent、未请求沙箱升级、未启动真实 Codex、未改主控/作者工作区、未发送收件箱消息。发现直接交本次派发主控处理。

## 独立脚本运行记录：主控 #51

首次执行 exit 1，输出保留于 `/private/tmp/r82-review01-ZCfQvT`；完整终端输出为该目录 `controller-run.log`。`review-run.json` 的 steps、mutations 均为空，real_codex_turns=0，错误为 `归档含未授权成员：workbench/hooks/applypatch-msg`。这是 reviewer 脚本自身的前置缺陷，不是候选红态或任何变异被检出的证据。

根因是脚本拒绝所有 symlink，而冻结产品的 hooksPath 含 26 个已登记的 Git 钩子入口，全部为同目录 `hook.py` 的链接。修复仅限脚本的成员/类型白名单：逐个列明这 26 个名称，只接受其目标文本严格为 `hook.py` 的符号链接；实现文件 `hook.py` 必须是普通文件，hooks 下其他成员、其他位置的链接、硬链接和特殊文件继续拒收。未改候选、归档路径范围或任何业务断言。

已在内存中对冻结候选同一组必要路径生成的实际归档执行修后验证循环：69 个成员通过，其中恰有上述 26 个链接；10 个明确的未授权/越界/错误目标/硬链接/特殊文件反例全部拒收。原谓词确会拒收同一个合法 `applypatch-msg -> hook.py`，与保留的首次失败一致。`bash -n`、主 Python 与内嵌探针的语法检查通过。只读检查没有解包、启动 daemon 或运行业务用例。

该次收尾时，整票及五个变异检查记为 INCOMPLETE/NOT_RUN，等待主控再次运行。后续运行由 `mktemp -d /tmp/r82-review01-XXXXXX` 创建新目录，首次输出未被覆盖。

## 独立脚本运行记录：主控 #52

第二次执行 exit 1，输出保留于 `/private/tmp/r82-review01-RcJHII`，终端输出为该目录 `controller-run.log`；夹具原路径 `/private/tmp/q76-jf2wyt2l` 保留。第 1 段 exit 0、verified=true：`tracer_review_copy`、`external_review_boundary_invalidated`、`real_payload_report_roundtrip` 三案均 passed，cleanup_failures 为空。可认定这三案通过，不能将整批或尚未执行的变异记为通过。mutations 仍为 0。

脚本随后在 classify 清理请求目录的辅助逻辑中抛 `sqlite3.OperationalError('unable to open database file')`。本次现场确认三份 `state/state.sqlite3` 都存在、为普通文件，路径均为绝对路径，并非已删除或相对路径错误。数据库头为 WAL 读写版本，停止后无 WAL/SHM 侧文件；只读重开失败已复现，诊断性的 immutable 只读查询能读取两条 launch 记录。没有把该诊断参数加进脚本，也没有采用失败后的替代重试路径。

修复只改 classify 的数据来源：直接使用 close_fixture 在停止前已经保存的 `database-readback.json` 中的 launch_records，另核对 `phase=before-host-stop`、对应 `cleanup.json` 的 host_exit=0、无失败以及夹具路径归属。凭据缺失或不符就报错停止；不再重开停止后的数据库。清理范围仍只包括对应 launch 明确列出的 `/private/tmp/a2a-requests-*` 请求目录，且 A2A_STATE 必须匹配该夹具。

用第二次运行同一现场对修后 classify 做了定点验证：它正确判定三案 passed，并规划出六个有明确归属的请求目录。验证时仅将 save/rmtree 设为记录器，实际没有写报告或删除这些旧目录，原数据库与现场未修改；该验证证明读回及清理规划逻辑，不冒充真实删除效果或后续业务通过。Shell 与两段 Python 语法检查通过。

该次收尾时，整票为 INCOMPLETE，后续段及五个变异待第三次运行。前两次记录及夹具均保留，未用后续成功覆盖这些脚本缺陷。

## 独立脚本运行记录：主控 #53 与最终裁决

命令：`bash /Users/luckye/Documents/Code/a2a-wt-t082/evidence/2026-10-15-batch15/T-082/REVIEW-OUTSIDE-01.sh`。第三次输出 R=`/private/tmp/r82-review01-UnlqXU`，运行时间 2026-10-16 03:55:54～03:57:50 UTC，脚本 exit 1。readback 的 candidate 与 head_after 均为 `f589d19387c2dcc5eeda6505423d794f2b3be1f3`，real_codex_turns=0。没有移动、覆盖前两次现场。

第 01～13 段全部 verified=true。其中 T-076 指定三性质及严格协议、T-077 四案、请求/副本生命周期、实际报告 roundtrip、协议容器校验、坏 -C/tmp 拒收、独立共享 refs 生产反例均通过；M1～M5 各自 exit 1 是预期业务红，不能误读为基础设施失败。第 10 段“verified”只表示按计划观察到原测试继续通过，恰好证明它们漏检 M3，不是宣布 M3 正确。

第 14 段为 contract_failure / REVIEW-END-BEFORE-INTEGRATE；第 15 段为 contract_failure / REVIEW-REQUIREMENTS-WORKSPACE。两者均无 harness_error、无 cleanup_failures，host_exit=0。已核对实际启动边界正例断言通过、原生信号传输有效、实际 CLI 回执、持久事件和 Git 读回；没有为凑红态改动这两段所用的产品源码。它们是候选缺陷，不再列为待复现风险。

**最终 NO_GO，需修复。** 阻断依据是 P1 的门禁顺序反例；P2 的错误请求元数据入库、生产门禁负例覆盖缺口另列。T-076 旧 runner、字面时间先红的保留事项不被上调为 PASS，也不拿来掩盖已复现的 P1。未实现或修复产品候选，未提交、submit 或集成项目变更；报告与摘要交执行主控处理。

T-082 REVIEW DONE
