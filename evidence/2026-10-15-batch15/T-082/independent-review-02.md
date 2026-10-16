# T-082 独立审查 02（最终）

STATUS: INCOMPLETE

TARGET: `5f7f9816eb9a996377c5b255695244d99c0259e7`；第一轮候选 `f589d19387c2dcc5eeda6505423d794f2b3be1f3`；起点 `451be8462c85fd08b997cb85453188a8e5751c9d`。规格为 T-082 ready_rev 1、D3。

第一轮五条发现均已解决；本轮四个错误实现都在指定业务断言处被拒，当前候选的对应正例和指定回归通过。未发现新的产品放行路径或锁死。**整票保持 INCOMPLETE**：Acceptance 2 的三项红态是修复后在起点版本重建的有效反事实，仍不能证明字面要求“每种先见红”的实际时间顺序。另有一个既存的 runner 状态字段不同步问题，见发现清单。本 reviewer 不替主控豁免或改写验收条件。

原始输出根为 `/private/tmp/r82r2-bCfvVo`，下文简称 **R**。主控 #57 返回总退出码 0；本次已读 [controller-run.log](/private/tmp/r82r2-bCfvVo/controller-run.log)、01～11 段 assessment、相关 case 原始断言、Git 回执和数据库读回。各段外层 exit 0 表示取得预期证据；四个错误实现内部测试实际均 exit 1，不能表述为错误实现通过。

## 范围与独立性

本 session 是第二轮 fresh-context reviewer，未读取作者或第一轮 reviewer 的会话历史；只读角色卡、票据、正式审查报告、返工文档、冻结代码和保存证据。目标是复核五条发现、七条 Acceptance、完成条件充分性和结构风险；非目标是实现、修复、改变验收、集成或新增真实模型回合。

开始及结束核对的 HEAD 均为目标候选；初始工作树干净，收尾仅有授权新增的本报告与 `REVIEW-OUTSIDE-02.sh`。未改产品、测试、地图或全局配置，未提交、派发子 agent、调用模型、启动真实 Codex、读取或复制 auth，也未请求沙箱升级。脚本仅由主控在沙箱外执行；副本来自冻结 Git 归档的必要路径白名单，含实际 Git hook 脚本与 `hook.py` 链接，依赖只引用已有目录，不安装或构建。

按 `project-map`、`behavioral-acceptance-review`、`evidence-first-testing` 核对，文档按 `document-writing` 保存；结构检查并入验收审查。会话开始、接收输出后与最终保存后的 `project_map.py status --root .` 均 exit 0、Problems (0)、Stale living docs (0)。

Ubiquitous language：`review.workspace` 是门禁管理的 detached Git 审查 worktree；`review.candidate_workspace` 是 reviewer 可写的一次性内容副本。Tracer bullet 经过 CLI、daemon、门禁、Panes、Stop/relay、SQLite 与清理；受控 PTY 只替换进程/原生事实，不替代门禁判定，也不证明真实 Codex 沙箱。Deep modules：沿用唯一门禁和既有操作锁，没有增加变异平台或平行集成 API。

核对 `git diff f589d1938..5f7f9816e -- workbench/src workbench/tests`，并检查 `451be8462..5f7f9816e` 产品 diff、直接调用者和相关测试。R/01-source 保存源码归档及成员清单；R/11-final-receipts 逐字核对未变异副本与冻结 Git 内容，未发现变化。数据库使用用例在 host 停止前保存的读回，没有在清理后重开 WAL 数据库；26 份数据库读回都有 host_exit=0、cleanup failures=[] 的对应收据。全部现场留在 R，旧红态未覆盖。

## 第一轮五条发现逐项复核

| 第一轮发现 | 结论 | 产品与独立证据 |
| --- | --- | --- |
| P1 结束核对前可集成 | PASS，已解决 | `core.ts:2170` 按 task、attempt、review_id 查本 review 的 review_reclaimed，缺少则 review_end_check_required。R/02 的脏、干净 held-socket 两案在报告已入库、回收未完成时都拒绝 integrate，main 不变；干净案结束后同一候选成功集成。M1 只查报告时在 REVIEW-END-BEFORE-INTEGRATE 失败。 |
| P2 workspace 未绑定 | PASS，已解决 | `core.ts:3454` 在保存 result 前精确比较请求 workspace 与本 review.candidate_workspace。R/02 错路径案 paused/unknown 且无 review_result；M2 退化为只查非空时在 REVIEW-REQUIREMENTS-WORKSPACE 失败。 |
| P2 结束核对负例不足 | PASS，已解决 | 新测试直接覆盖共享 refs、提前集成及路径改写，均经过 CLI/daemon/生产门禁。R/02 对应检查通过，M1～M3 分别在对应断言失败；M4 另证明假发 removed/reclaimed 事件骗不过实际路径不存在的断言。 |
| P2 默认 tier 负例换观测点 | PASS，已解决 | runner 从当前 D3 候选分别只移除 worker/reviewer 的显式 default override，仍要求原两个 DEFAULT-ARGV id。OUTSIDE-12 两项实际均在该断言 contract_failure，reviewer 的启动边界和身份此前已通过。R/10 逐字比较归档中的 27 份生产源码/直接驱动与冻结候选，均相同；R/07 当前候选两种 default 正例通过。runner 状态字段遗留问题单列，不改变该业务证据。 |
| P3 同值条件式 | PASS，已解决 | `panes.ts:156` 的 sandboxMode、networkAccess、networkProxy 已改为常量，真实不同的 tmp 排除分支保留。R/09 当前四种启动参数拒收全部通过。 |

### P1 的锁、顺序与正常活性

`call` 在 `core.ts:3127` 取得任务操作锁，覆盖 integrate 及 verify→requestReview→requireReviewed；finally 释放。`reclaimReview` 在 `:2282` 取得同一个任务锁，顺序为 stop/archive 确认、checkReviewBoundary、删除副本并核对不存在、移除审查 worktree 并核对登记消失，最后在 `:2304` 记录 review_reclaimed。完成记录与报告绑定同一 task/attempt/review。accepted 分支只重放已完成集成；首次集成及 intent 恢复仍经过 requireReviewed，没有增加绕过该前置的入口。

`operationLock` 使用独立 SQLite BEGIN IMMEDIATE、busy_timeout=0，竞争时报 operation_busy，不同步等待另一条持锁调用；返工未增加锁嵌套、等待循环或重试。下列路径证明正常回收后的活性，不扩大为所有并发时序的保证。

R/02-candidate-green/result/integration_before_end_check_clean：task `fixture-20261016-1`、attempt `faf92a63-ce58-411f-a93f-e61860d88e0b`、worker session `f5ec59e1-11db-49fa-96a5-f2797d39062a`、fence/spec_rev 均 1；review `e14d8817-7219-4c2c-850d-fcd561a06c07`、review session `fcce6db6-90d8-43ab-84a4-0cebd1ef46ce`、launch `8aa2e290-f2e7-43aa-bcc2-5cbc8769cf53`。候选为 `2aa6108a492ea0adf7f9cfa69ac22651def8246e`。原件为 [提前集成回执](/private/tmp/r82r2-bCfvVo/02-candidate-green/result/integration_before_end_check_clean/integration-before-end-check.json)、[释放后状态](/private/tmp/r82r2-bCfvVo/02-candidate-green/result/integration_before_end_check_clean/after-release.json)、[完整断言](/private/tmp/r82r2-bCfvVo/02-candidate-green/result/integration_before_end_check_clean/case.json)。

- 持有 signal socket 写半边时：review_result seq 95，task verified/review passed，但 integrate 返回 ok:false/error:review_end_check_required，main 保持 `d52875d38eec2bf169e673b104c0154811878981`。
- 关闭连接后：copy_removed seq 115、worktree_removed 129、review_reclaimed 130；同候选再次 integrate ok:true、task accepted，main 成为该候选。
- 脏目录案：提前集成同样拒收；释放后 seq 108 review_lifecycle_failed，task paused/review unknown，main 不变，副本留存供诊断并上报。

## Acceptance 七条核对

| 条款 | 结论 | 证据与范围 |
| --- | --- | --- |
| 1. 起点红态 | PASS，起点行为已证明 | 起点 451be8462 的 core/Panes 没有完成条件充分性与 2～5 变异要求，仍以 read-only 在审查 worktree 启动；red-state/static-red.json 五项 true。另直接读取主 checkout 的 T-076 outside-p-review-02 的 sentinel-result、launch 与归档中的审查 sentinel：一次原生写入被 errno=1 拒绝，事后内容不变。只继承该历史只读事实，原 product_status=INCOMPLETE 保留。 |
| 2. 受控入口、四种先红后绿 | INCOMPLETE；当前拒收与旧版本反事实 PASS | R/09 readonly-argv、wrong-workspace、network-enabled、tmp-writable 均以 review_launch_boundary 拒收、paused/unknown 并上报，三个 T082-LAUNCH 断言全通过。wrong-workspace 有早先实际红绿；OUTSIDE-10 补的三项旧版本业务红态有效，但明确是修复后重建，未补足字面时间顺序，详见 P2。 |
| 3. 真实 Codex 边界 | PASS，限已保存真实边界及未改变的启动契约 | 独立读取 round-1-03 外置原生 gzip：工具行 39/46/53/62 解码后的 output 与保存选段逐字相同，call_id 一致；实际 context 为副本 cwd、workspace-write、network_access=false、两个 tmp 排除 true。副本写文件/测试 exit 0；外部三处各 exit 1/Operation not permitted；共享 update-ref exit 128/cannot lock ref；域名与直连 IP 各 exit 6、7。round-1 协议失败仍未通过完整生命周期，由 round-2 补结束事实。本轮未新增真实模型回合。 |
| 4. 结束作废及删除 | PASS | R/02 外部目录、共享 refs 改动均使结论作废/上报并保留异常副本，干净路径实际删副本；held-socket 场景保证核对前不可集成。M3/M4 对应错误实现均检出。round-2 真实结束 Git 回执另证明候选未变、两 worktree 干净、共享 refs 未变与正常删除。 |
| 5. 偏弱任务卡真实交付审查 | PASS | round-2 卡要求 value.txt 与 details.txt 两文件，oracle 只查前者。入库报告有独立节与五个变异；原生工具行 52 的 value 错值/缺 LF 各 exit 1，details 缺失/错值/缺 LF 各 exit 0。reviewer 判需修复、指出 details 缺验收，与目标相符；判断如实记录，门禁只管容器与元数据。 |
| 6. ≤4 回合、argv、home 删除 | PASS，2/4 | round-1-03 与 round-2 原生记录各一个 task_started/主回合，launch turn_limit 均 1。完整 argv/shell_argv、CLI/模型/强度均已读；删除收据为 absent，本次两 CODEX_HOME 路径确已不存在。初次 home 前置拒收与 -02 的 foreground_codex_required/未释放状态保留，不计成功回合。本轮 real_codex_turns=0。 |
| 7. T-076 三性质、T-077、地图 | PASS，限指定性质和套件 | R/07 错候选、不续接原生会话、写入者不能审查、严格协议及两种 default argv 六案全过；R/08 T-077 四案全过。cleanup 均无失败；地图 0 problems/0 stale。旧完整质量 runner 的源审计 INCOMPLETE 保留，不扩大为其整体通过。 |

### 真实证据的版本与读回限度

round-1-03 产品为 `0dd00d09dcdd4a6ae9c3b633e678419037485875`、launch `4f1c53ae-5d54-4cfe-b248-46608d94d171`；round-2 产品为 `7f2bd40611e920cb962ba20f17b58bb12a9acab0`、launch `59df6d1d-74b8-4c60-b6d1-21da7cdddcd5`。0dd00d09d..7f2bd4061 的 Panes 无差异；到冻结候选的 Panes 只将三组同值分支改成同值常量，实际沙箱参数不变。后来 core 的结束前置与路径绑定由本轮冻结候选的真实 CLI/daemon 检查证明；旧真实运行不替新增检查背书。

round-1 原件位于 boundary-readback.json 的 sources.rollout（外置盘），工具选段为 real-boundary-readback-01/native-tool-output-line-39/46/53/62.txt。round-2 原生记录为 real-codex-round-2/traces/59df6d1d-74b8-4c60-b6d1-21da7cdddcd5/native.jsonl。

round-2 [end-readback.json](real-codex-round-2/end-readback.json) 的原始 command_result：seq 105/109 两个 HEAD 均为 `af586aed2709b46768f90e334156cf9197d0115e`；seq 107/113 两个 status stdout 均空、exit 0。共享 refs 事前/事后文本相同，worker/shared sentinel 直接读回相同；review sentinel 由删除前 HEAD、clean 与受控内容间接证明，删除后的直接 after 不可得。生命周期为 result 94 → copy_removed 115 → worktree_removed 129 → reclaimed 130。

真实 argv 固定 codex-cli 0.162.1、gpt-6.1-sol/xhigh、显式 service_tier=default、-a never、副本 -C、workspace-write、关闭网络/proxy、排除两种 tmp。请求 tier 不证明供应商实际 tier。home 信任根仅为各自 fixture，规则只有 git add/git commit 两条；逐回合 hook 批准文件与启动记录存在。本次未读取 auth，不以文件名清单证明其内容；两个隔离 home 已删除。

round-2 工具行 24 有 heredoc 无法在 tmp 建文件的 exit 1，后续实际改用可执行命令并完成五个变异；该失败保持原义。系统启动器的 tmp 缓存权限诊断亦保留，没有误当成业务红态。round-1 协议失败没有因 round-2 成功被改写。

## 完成条件与变异检查

**完成条件充分性：PASS，限以下四类明确错误实现。** 预期来自 T-082 的候选绑定、结束核对及实际删除契约；候选新增测试是被审查信号，使用错误实现验证它们确实观察要求。正确候选 R/02 七案全过，排除了用“总是拒收”代替正确行为。此结论不是对所有错误实现的完整证明。

从仓库根完整再现：

```sh
bash evidence/2026-10-15-batch15/T-082/REVIEW-OUTSIDE-02.sh
```

每次新建输出目录。以下为本次四个实际子命令：R=/private/tmp/r82r2-bCfvVo，Python 实际为 /Library/Developer/CommandLineTools/usr/bin/python3；已有输出不覆盖，重跑用上面的脚本生成新 R。

```sh
python3 -B "${R}/candidate/workbench/tests/test_t082_review_boundary_e2e.py" --source "${R}/M1-report-only" --output "${R}/03-M1-report-only/result" --case integration_before_end_check_clean
python3 -B "${R}/candidate/workbench/tests/test_t082_review_boundary_e2e.py" --source "${R}/M2-nonempty-workspace" --output "${R}/04-M2-nonempty-workspace/result" --case requirements_workspace_changed
python3 -B "${R}/candidate/workbench/tests/test_t082_review_boundary_e2e.py" --source "${R}/M3-omit-shared-refs" --output "${R}/05-M3-omit-shared-refs/result" --case shared_refs_changed
python3 -B "${R}/candidate/workbench/tests/test_t082_review_boundary_e2e.py" --source "${R}/M4-false-copy-removed" --output "${R}/06-M4-false-copy-removed/result" --case tracer_review_copy
```

| 变异 | 实际修改 | 结果与原件 |
| --- | --- | --- |
| M1 | requireGate(ended, …) 改为只检查 review_result 的 row | exit 1、contract_failure、REVIEW-END-BEFORE-INTEGRATE；确实提前 integrate ok:true、main 前移，后置失败时仍 accepted，重现第一轮缺陷。[case.json](/private/tmp/r82r2-bCfvVo/03-M1-report-only/result/integration_before_end_check_clean/case.json) |
| M2 | 精确 workspace 比较改为 Boolean(workspace) | exit 1、contract_failure、REVIEW-REQUIREMENTS-WORKSPACE；wrong-copy 报告确实入库，task verified/review passed。[case.json](/private/tmp/r82r2-bCfvVo/04-M2-nonempty-workspace/result/requirements_workspace_changed/case.json) |
| M3 | 共享 refs 比较改为 true | exit 1、contract_failure、REVIEW-REFS-INVALIDATE；引用已改变却仍 verified/passed，随后回收并删除副本。[case.json](/private/tmp/r82r2-bCfvVo/05-M3-omit-shared-refs/result/shared_refs_changed/case.json) |
| M4 | 删除 rmSync 及事后不存在核对，保留 removed/reclaimed 事件 | exit 1、contract_failure、T082-COPY-REMOVED；数据库有 copy_removed 114、reclaimed 129，但实际目录仍存在，本次读回亦确认存在，证明未只信事件。[case.json](/private/tmp/r82r2-bCfvVo/06-M4-false-copy-removed/result/tracer_review_copy/case.json) |

四案 failure_id 均对应同名 failed assertion，cleanup_failures=[]、owned host exit 0。准确 argv、改动字符串及 stdout/stderr 在 R/03～06 的 command.json、assessment.json 和 result；变异只在 R 的副本，不进入 Git 或集成路径。

## 已确认发现（按严重度）

1. **[P2，验收过程证据缺口] 主 checkout 的 T-082 票据第 28 行“每种先见红”时间顺序未证明。** [outside-command-10-01/run.json](outside-command-10-01/run.json) 的 counterfactual_timing 原文为 `reconstructed after the fix on the starting revision; not an earlier chronological run`，第一轮报告也保留此限制。旧版本反事实与当前拒收都成立，但 readonly-argv、network-enabled、tmp-writable 没有可核对的逐项修前运行顺序。reviewer 无权把“旧实现会失败”自动改成“当时先运行失败”。最小处理是补已有的更早原始收据；若没有，应交有权决定验收的上层明确接受反事实替代时间要求并留痕。没有该决定前整票 INCOMPLETE；不要求为补时间顺序再消费模型回合，也不建议修改产品制造历史。
2. **[P3，既存报告元数据] workbench/tests/run_t076_launch_policy.py:25、:115 的两个状态字段不同步。** 初始化 status/product_status 均为 INCOMPLETE，成功时只改 status。实际 [OUTSIDE-12 run.json](outside-command-12-01/t076-launch-policy/run.json) 因而同时为 status:PASS、product_status:INCOMPLETE，外层 exit 0。其负例与正例已逐项核实；这个遗留标记不能当成业务测试失败，也不能静默上调。建议统一两个字段的成功/失败更新，或明确只保留有定义的权威字段；读取最终报告并核对 exit/status 一致性的检查即可检出。该问题既存于本轮返工前，属于证据报告缺陷，未证明产品 tier 错误，不单独构成 NO_GO。

## 结构核对与限制

symlink realpath 失败转为带原因的 Refusal；create/reclaim catch 保留生命周期失败、暂停当前任务并上报，不返回默认成功。删除 force:false 且事后检查实际不存在；任一步失败不写 review_reclaimed。未发现返工新增吞异常、兜底重试、旧 read-only 兼容分支、双写或平行 API。结束前置位于既有集成门禁，workspace 比较位于报告入库的事实拥有层，修复范围与根因一致。

机械检查只管报告容器、节键和请求元数据，不按模型自称的变异数、结果或判断自动批准，符合 D3 判断交 reviewer、不建平台的范围。本审查不把一次弱夹具上的正确判断外推为可靠性指标。

本次未新增真实 Codex 回合、完整旧质量 runner 或额外构建。真实沙箱证据来自两个已记录回合，当前门禁修复由冻结候选的独立 CLI/daemon 路径与四个变异证明。未发现尚需修复的 P1 产品问题；最终 **INCOMPLETE** 保留明确的验收时间证据缺口和报告元数据发现，不宣称七条 Acceptance 已全部成立。

T-082 REVIEW 02 DONE
