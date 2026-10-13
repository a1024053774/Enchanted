# T-076-2 断言与 hunk 对照（阶段 1–3 准备）

状态：**INCOMPLETE**。主控 #32 与 [决定 01](controller-decision-01.md) 已批准 PLAN 的 W01–W06、F01–F04。red-02与focused-tracer-01均已核对阶段PASS，首条路径及9个新反事实有效；主控 #39 批准加宽，见第7节。旧acceptance断言仍未改。本文前六节保留各阶段准备记录，不能把其中“尚未运行”“产品代码未改”用于当前进度。

基线：`a7f4cc3033c16d5888de50d8352da516c941f8e9`；本轮开始 HEAD：`d3f2c2cf3b838d8f56e8a57629a19b9d282ea64f`。两者间只增加了主控记录/收件箱，产品与旧三套验收相同。以下按函数名定位，不把行号漂移视为扩大授权。

## 1. 旧断言 hunk 清单：空

本阶段以下命令应输出空 diff：

```sh
git diff a7f4cc3033c16d5888de50d8352da516c941f8e9 -- acceptance/test_coop_e2e.py acceptance/test_recovery_e2e.py acceptance/test_run_e2e.py
git diff a7f4cc3033c16d5888de50d8352da516c941f8e9 -- workbench/src workbench/hooks
git diff a7f4cc3033c16d5888de50d8352da516c941f8e9 -- workbench/tests/test_task_cards_e2e.py workbench/tests/test_multiturn_identity_e2e.py workbench/tests/run_worker_delivery.py workbench/tests/run_t076_real.py workbench/tests/daemon_acceptance_adapter.py workbench/tests/daemon_acceptance_host.ts
```

W01–W06 的旧测试迁移尚未执行，F01–F04 的旧适配器尚未改动。Recovery 9 项、`test_coop_e2e.py` 未打回就换候选的反例、`test_run_e2e.py` 的 leader-changed 反例保持不动。

## 2. 新增测试 hunk 与独立预期

本阶段三个新增源码文件是 `/dev/null → 文件` 的完整新增 hunk：

- `workbench/tests/test_quality_chain_e2e.py`：真实 CLI/后台用例，独立期望及逐条断言。
- `workbench/tests/quality_chain_host.ts`：仅替换 `node-pty.spawn` 和 `Panes.processInfo` 的测试进程；生产 CLI、signal、relay、调用者身份检查、Panes 登记/队列/原生记录解析、门禁、Git、SQLite 全部保留。没有 reviewer 结论替身、没有数据库写 passed、没有模型调用。
- `workbench/tests/run_t076_quality_red.py`：冻结基线/测试、阶段边界、精确失败分类、受控对照和单点变异体、归档。

新增文件的可审阅补丁由下列命令分别生成（`git diff --no-index` 的退出 1 表示有差异，不是测试结果）：

```sh
git diff --no-index -- /dev/null workbench/tests/test_quality_chain_e2e.py
git diff --no-index -- /dev/null workbench/tests/quality_chain_host.ts
git diff --no-index -- /dev/null workbench/tests/run_t076_quality_red.py
```

| 新用例 / 失败标识 | 独立来源及预期 | 与批准白名单的关系 | 阶段 2 起点预期 |
| --- | --- | --- | --- |
| `red_manifest_missing` / RED-MANIFEST | P1：非空 red_commands 必须显式 test_paths；旧卡能被接受即违约 | W06；仅验证字段契约，不称完整业务红态 | 在 card_validate 接受缺清单命令处失败 |
| `red_base_not_failing` / RED-BASE-PASSES | T-076 Acceptance 反例1、spec §3.4：起点也通过的命令不能建立红态 | W06、R-red | 真正执行同一测试，确认 B+测试、C 都退出0；旧verify放行后业务断言失败 |
| `red_candidate_fails` / RED-CANDIDATE-FAILS | spec §2、§3.4：候选上的同一红态命令必须通过 | W06、R-red | 独立脚本在C的明确业务assert退出1，旧verify忽略该命令而放行 |
| `red_rules_failing` / RED-RULES | T-076反例2：项目规则失败须拒收 | W04、R-rules | 冻结工作分支中的规则为明确失败命令，旧verify仍成功 |
| `red_rules_frozen` / RED-RULES-FROZEN | 决定01/P1：规则从注册时工作分支读取并冻结 | W04、R-rules | 候选删除规则不能取消已注册规则；旧verify仍成功 |
| `red_feedback_idle` / RED-FEEDBACK | spec §3.4、§6：首拒应为原worker登记gate修复消息 | W01/F01；对应首拒回写 | 完成条件确实oracle_failed之后，缺少新的gate登记。初始submit ACK不计修复消息 |
| `red_repair_resubmit` / RED-RESUBMIT | 同attempt、同原生会话收到打回后可修好提交C2 | W01/W05/F01 | C1明确失败，供给一个受控执行主控输入驱动修复动作；新turn显式交付C2被旧门禁拒绝。此用例只证明修复交付授权，不冒称自动回写已发生 |
| `red_review_required` / RED-REVIEW | spec §3.5：机械通过后新建reviewer，不能立即verified | W02/W03/W04 | 旧verify完成后没有reviewer启动事实且task已经verified |
| `red_terminal_prerequisites` / RED-FINAL-PREREQUISITES | spec §3.5–6：缺独立审查及执行主控评分不得集成 | W02/W03 | 旧integrate无两项前置仍推进Git。这是合取前置缺失证据，不能单独证明评分字段校验有效 |
| `red_run_reject_preserves_worker` / RED-RUN-REPAIR | Q1/Q4：首拒不能回收正在等待修复的原worker | W01 | 显式期限run在一次oracle失败后回收原worker，保留完整run收据与库读回 |
| `red_run_waits_for_executor` / RED-RUN-FINALIZE | 决定01/P3：run等审查和执行主控显式最终命令 | W02/W05 | 未有外部最终命令时旧run直接集成；记录Git实际改变 |

`legacy` 卡形状只用于冻结起点的两个红态命令用例，因为起点不认识新 `test_paths`。测试的独立预期不变；新接口实现后的同场景用 `current` 形状显式提供清单，不给产品增加旧格式兼容分支。缺清单用例始终故意用旧形状以验证新契约拒绝。候选测试迁移及变异体结果另列，不能把起点的usage/字段未知报错当红态。

## 3. 阶段 3：8 个既有保护对照与 3 个已知坏产品变异体

所有对照通过真正的CLI、后台、Panes/relay/门禁路径，PTY/进程/原生输入为受控夹具；不存在真实模型或物理终端证据。

| 对照 | 检查内容 | 起点期望 |
| --- | --- | --- |
| control_completion | 独立完成条件拒绝bad候选，ref不变且有事件 | PASS |
| control_paths | 禁止路径拒绝，ref不变且有事件 | PASS |
| control_frozen_candidate | 未被打回时不得用C2替换C | PASS |
| control_fence | 错fence不得submit，有stale_fence事件 | PASS |
| control_stop_without_request | 已commit但没有显式请求的Stop不submit | PASS |
| control_relay_invalid | 错session、缺commit请求由真实relay拒绝 | PASS |
| control_relay_duplicate | ACK的Stop再次读同文件，submit只执行一次并留replay | PASS |
| control_busy_queue | busy只登记/排队；Stop之后先bracketed paste、后CR，登记/提交意图均早于字节 | PASS |

只在起点复制目录中分别变异，不改主checkout。每个变异体只替换 `core.ts` 的一个唯一命中片段，完整前后文本进 `*.mutation.json`：

| 变异体 | 删除的行为 | 必须命中的断言 |
| --- | --- | --- |
| fence-disabled | submit的fence核对 | CONTROL-FENCE |
| candidate-freeze-disabled | 没有打回仍禁止换C | CONTROL-FROZEN |
| path-guard-disabled | 禁止路径拒收 | CONTROL-PATH |

这些变异体证明本阶段对照能抓住已有底线退化，**不替代尚不存在的review/score/三次上限变异体**。候选有新接口后，再针对接受writer/续接、错C、缺score、第三次仍自动回写等真实行为逐个取反事实。

## 4. 明确尚未取得的验收证据

第三次打回、有效reviewer身份反例、错C结论、需修复问题清单、独立score字段/放弃/格式/恢复，以及P-review实测均未完成。阶段脚本会把这些写入 `deferred-contracts.json`/`run.json`，没有把它们包装成跳过后全绿的测试。

此卡尚未进入旧8/9/18迁移与最终回归；本阶段的8个对照不是旧交付8项，报告分别命名。后续修改旧断言时，逐hunk追加W编号、规范原句、实际红/绿产物路径；超出白名单则停止提交修订。

## 5. 主控 #34：夹具读取修正hunk

`harness-repair-01/test-fix.diff`相对`test_quality_chain_e2e.py.before`列出本次三个hunk；只涉及本卡新增测试，不涉及旧W01–W06的文件断言迁移：

| 方法 | 修改 | 独立期望是否变化 |
| --- | --- | --- |
| red_feedback_idle | 保存单次读取的current_attempt；不存在时RED-FEEDBACK.identity失败 | 不变：消息仍属于原worker，当前attempt仍须为原ID |
| red_repair_resubmit | current_attempt存在才读取ID；丢失时RED-RESUBMIT.binding失败 | 不变：C2与原attempt绑定 |
| red_run_reject_preserves_worker | 判定前保存run/task/ref/历史attempt；不存在、ID不同或已回收都以RED-RUN-REPAIR失败 | 不变：首拒保留原worker待修复，不能集成；增加显式原ID核对使表述与既定合同一致 |

`offline-replay-01`用原始保存读回复放旧/新方法，证明旧方法崩溃、新方法生成指定业务失败；只证明夹具修复，不把旧run报告补改为已取得RED-RUN-REPAIR。新的真实入口结果须在red-02取得。

## 6. 主控 #35：新接口的受控用例/反事实

旧W01–W06迁移仍未执行；新增`test_quality_tracer_e2e.py`与`run_t076_quality_green.py`的完整新增hunk，其独立预期来自PLAN §3–5与决定01/P2/P3：

| 新方法 | 对应合同 | 候选坏行为反事实 |
| --- | --- | --- |
| tracer_success | 首拒→原attempt修复C2→新审查→带分集成，整串重跑、一次最终分 | 起点已有RED-FEEDBACK/RESUBMIT/REVIEW/FINAL-PREREQUISITES；候选reviewer-writable须命中启动参数断言 |
| tracer_score_required | 有有效review后，缺评分/缺notes独立拒绝 | score-invented、score-fields-unchecked |
| tracer_wrong_candidate | 其他身份均合法，唯一错误为review结论C | wrong-c-accepted |
| tracer_malformed_review | JSON被Markdown包住不能自动提取，原文保留并暂停 | markdown-extracted |
| tracer_review_needs_fix | 位置/场景/建议原文回写，C2重新审查后集成 | 配合下一行，正例提供同输入的独立有效新会话对照 |
| tracer_reused_native | 新launch、新home也不能沿用旧reviewer原生ID | old-native-accepted |
| tracer_third_rejection | 三个独立新C失败，只有两条修复消息，第三次issue/paused | third-rejection-keeps-writing |
| tracer_writer_cannot_review | writer的B目录不能以有效review id冒充reviewer | 当前产品真实relay角色拒绝；原始拒绝必须保存，不仅看请求失败 |
| tracer_run_waits | 有效review完成后run仍等执行主控，显式集成后才回收 | 起点RED-RUN-FINALIZE已证明旧自动集成违约；新路径不预填分 |
| tracer_missing_delivery_context | 修复交付缺当前模型上下文，不沿用ACK/旧turn事实 | prior-turn-score-facts |
| tracer_identity_score | 一条错fence的B请求在ACK重放后仍只计一次identity_version拒绝 | identity-refusals-not-scored |

每个新反事实的具体文件/替换前后文本/目标断言会写入focused输出中的`*.mutation.json`。尚未运行，不提前填PASS。只读argv变异体不能替代真实沙箱拒写探针；放弃/升级、评分恢复和完整旧回归仍待加宽。

`test_relay_core.ts`的唯一变更为夹具binding增加`role: "worker"`；不改其任何断言，生产relay不把未知角色默认为worker。该输入适配与真实后台role来源一致，不是免检开关。

## 7. 主控 #39：加宽合同与反事实

`test_quality_widen_e2e.py`与`run_t076_quality_widen.py`为新增文件；通过`git diff --no-index -- /dev/null <文件>`生成各自完整hunk。旧acceptance、旧恢复屏障以及`scripts/score`只读，白名单尚未用于修改它们。

| 用例组 | 独立预期来源 | 已有红态或本次反事实 |
| --- | --- | --- |
| B/C分开、检查顺序、同命令B失败C通过 | spec §3.4、决定01/P1、PLAN §2.2 | red-02的RED-BASE-PASSES/CANDIDATE-FAILS；本次两项允许错误退出结果的变异体 |
| 项目规则失败、候选删配置无效 | 决定01/P1：注册时冻结 | red-02的RED-RULES/FROZEN；本次rule-failure-ignored |
| 测试路径、symlink、坏项目配置 | P1显式文件清单与损坏配置拒收 | relative-test-path-escape-accepted、symlink-test-accepted、project-rules-silently-disabled |
| 放弃、升级、缺分与字段拒绝、回收保留终结结果 | spec §3.8/§8、PLAN §5 | abandon-requires-scores、abandon-extra-fields-ignored、upgrade-score-rejected |
| 旧/新schema=1双向校验及用户独立行 | 只读scripts/score与record_io的公开格式 | duplicate-score-import-accepted、truncated-score-tail-repaired；另有缺事实、关联错来源、放弃夹facts的双向拒绝输入 |
| CAS前后中断，不提前记最终分、不改恢复评分、恰好一次 | 原恢复契约、PLAN §5.2/6.1 | score-written-before-cas、recovery-score-changed；沿只读GIT_BARRIER注入实际中断 |
| reviewer创建失败、重启待审、退出未确认 | 未知状态可恢复暂停、PLAN §4.4；主控 #39明确要求 | 上轮冻结产品取REVIEW-CREATE-PAUSE/RESTART-PAUSE/RECLAIM-PAUSE三项红态，未修复 |

当前测试增加`configure_host`和`start_host`仅为各fixture独立配置Git屏障及保留每次后台启动的原始证据；原断言不变。PTY故障由明确字段触发，每次输入追加保存；不是异常兜底或自动重试。CAS恢复只信号本fixture经pid/root/socket身份核对的后台。reviewer异常红态与加宽候选绿态分别执行，避免拿新产品的输出当旧实现失败证据。

本阶段计划15项候选用例、13个变异体、3项冻结源码红态。动态结果均待主控沙箱外运行；语法检查不称验收通过。8/9/18迁移仍待执行，Recovery9的业务断言始终不改。

## 8. 主控 #48：原reviewer断言转绿准备

第7节各项已由主控运行并读回符合预期；三项reviewer异常仍用原方法及原业务断言，测试正文无变化。runner只新增`review-green`组合：三项异常、三条reviewer正常路径、两项CAS评分恢复；不再跑其余加宽用例及变异体。

新产品事件的task快照进入只读一致性重建；创建/回收异常只增加记录及暂停，不把异常转换成通过。修复diff独立保存在`review-repair-01/reviewer-lifecycle.diff`，待主控审阅及绿态执行。

旧W01–W06/F01–F04迁移尚未改文件。手工claim无法通过现有运行时接口提供评分来源，已按F01的停止条件交[issue](ISSUE-legacy-claim-provenance.md)，等待决定具体夹具准备方式；Recovery9断言及两个冻结身份/候选反例仍保持原样。

## 9. 主控 #50：迁移方向已定，精确hunk边界待批准

reviewer-green三组共8项均已读回通过。决定02批准受控dispatch准备的方向；[F05-migration-list](F05-migration-list.md)是本次待审清单，F05–F12列明helper/method及原/新准备，不是实施记录。

其中F12请求额外W07，只涉及原冻结候选method末尾无来源却集成成功的合同冲突；原dirty/head/未打回换C/验收冻结C检查保留，原受管集成C的证据单列完整补充场景。未经主控明确批准不改该处。Recovery9方法与断言仍计划逐字保留；leader-changed原反例不改。新手工claim合法review/score反例及其来源守卫变异体在清单获批后才编写。

## 10. 主控 #52：决定03对应的实际hunk

以下均尚未运行动态检查；起点红态沿原red-02，新来源断言以本次单点变异体先取得反事实。实际两份acceptance diff见`legacy-acceptance-hunks.diff`，运行器不允许其与交接文件不同。

| 文件／方法或helper | 实际变更 | 批准编号与保留内容 |
| --- | --- | --- |
| test_coop：good_candidate、baseline_change | claim准备改显式dispatch helper | F05；分页oracle/快照/引用及冲突原断言不改 |
| test_coop：submit_requires_clean_head…末尾 | 合法score下拒绝score_provenance_required；ref/reflog不变、候选仍C、拒绝事件存在 | W07、决定02/PLAN §5.2；旧“手工集成C”三行改掉，直到verified/C的原前缀逐字保留 |
| test_run：run_entry、concurrent_duplicate、matching_reclaim | 显式外部review/执行主控finalize在原run完成观察前执行 | W02/F07；旧业务结果、唯一worker/close/reflog等断言不改 |
| test_run：fixture_existing_dispatch | 显式准备绑定attempt的评分 | W02/F07；原dispatch/verify/integrate/reclaim仍经真实入口 |
| test_run：oracle_failure | 原失败oracle/ref/workspace不变；不关闭worker、原attempt未回收且登记一条修复输入 | W01；不再保留原“首拒close”预期 |
| daemon_acceptance_adapter/host | method＋owner选择、持久外部创建事实、独立review/B、显式评分、读回后续动作 | F06/F07/F09；Recovery源码不编辑，原方法不在adapter中覆盖；屏障/CAS断言未改 |
| test_task_cards/DaemonCards | 注册helper提取，批准六处显式managed准备，受管尾注事实，review/score和事件前置 | F08/W04；create仍手工claim；所有旧路径/尾注/dirty断言保留；non_fast_forward未改、待F13 |
| multiturn host/tests | 受控创建事实与reviewer边界；两个正例加review/score | F09/W05；delivery-A、receipt-B及伪造native/leader断言不改 |
| controlled_quality_pty/legacy_review_runtime/driver | 提取既有PTY观察，组合受控worker与真实Panes reviewer，记录真实CLI动作 | F09；无模型、无生产库预填状态、无免检入口 |
| run_daemon_acceptance/audit_legacy_scope | 审核批准method、W07保护前缀、Recovery全文件及具体diff；报告实际证据层 | F11；suite计数8/9/18不变 |

新增`test_quality_legacy_e2e.py`的F10与managed冻结场景，按决定03取预期。`run_t076_legacy_green.py`先删一个来源守卫取得MANUAL-CLAIM-SOURCE、W07-MANUAL-SOURCE，再跑候选；后续报错但Git已变也判业务失败。结果原样保存；本轮尚未执行，不能填写红/绿PASS。

F13申请对应的non-fast-forward方法当前仍与起点一致；在批准前不修改、不skip、不降低为任意拒绝。完整legacy-green尚不能执行，见`ISSUE-non-fast-forward-fixture.md`。

## 11. 主控 #56：F13的唯一准备hunk

决定03补充已批准F13。`workbench/tests/test_task_cards_e2e.py:test_non_fast_forward_git_result_cannot_integrate`仅改`a = self.create()`为`a = self.create_managed()`，原Git wrapper、v.M=B、实际commit-tree输出与B不同、`integration_not_fast_forward`及ref=G全部保留。审计将候选完整方法与起点执行这一处替换后的文本逐字比较，其他变化即拒绝。

`legacy-acceptance-hunks.diff`不变：F13位于workbench测试文件。旧回归与任务卡运行器只增加failfast，成员和断言不变；静态收据另存`legacy-ready-checks-01.json`。动态红态、候选绿态及旧回归均待主控运行，不提前标PASS。

## 12. 主控 #57：F10红态成立，W07前置失败

legacy-green-01的F10来源变异体命中MANUAL-CLAIM-SOURCE；W07因旧卡model=fixture在reviewer启动失败，未取得W07-MANUAL-SOURCE。它不能冒充来源守卫反事实。状态/事件读回表明reviewer失败合同已满足，不改产品。

[F14](F14-fixture-executor.md)仅请求变更`ManagedDeliveryCLI.create()`的一处model值，尚未批准/实施，不修改断言，也不把它加入现有审计白名单。原交接diff和失败目录都不变；获批后保留旧diff副本、重新冻结新diff再跑新label。

## 13. 主控 #59：F14实际hunk

决定03补充已批准。`acceptance/test_coop_e2e.py:ManagedDeliveryCLI.create()`仅将executor.model从fixture改为gpt-6.1-sol；cli/effort、其他卡字段和helper内断言均保持。Recovery文件仍逐字不变。

审计允许列表增加create/F14，同时用完整helper正文逐字比较约束唯一字符串替换，不能借helper范围改其他逻辑。旧hunk原样保留为`legacy-acceptance-hunks.pre-F14.diff`；当前hunk新增这一行。01失败证据不动，02动态结果待运行，静态收据另存`legacy-ready-checks-02.json`。

## 14. 主控 #60：F09的路径拼写修复

02的W07失败为PTY夹具配置使用/tmp、产品传入/private/tmp；home已登记，shell正确。F09内只改`legacy_quality_driver.prepare_review_control()`先解析自建root，以及`controlled_quality_pty.ts`在原拒绝分支补诊断；严格包含条件和所有业务断言不改，`legacy-acceptance-hunks.diff`不变。

文件probe列出失败模式并复现旧配置拒绝、新配置接受和陌生home/错误shell拒绝；另查session/turn与B文件协议。probe自身一次shell_argv索引错误保留在offline-01，offline-02通过。精确前后diff与前置核对见`fixture-path-repair-01/`；完整W07及剩余回归等待legacy-green-03，尚无新产品PASS。

## 15. 主控 #62：managed_frozen的主动输入边界

03已证明W07-MANUAL-SOURCE且Git已变，F10同样命中；候选manual_claim场景通过。managed_frozen在dirty ACK结束后缺新输入，harness等待了不会发生的新ACK。产品的unmatched Stop拒绝符合合同。

F09/F05内仅改新增测试文件：添加begin_worker_turn helper，在dirty ACK后、合法C批次ACK后明确pane_dispatch；新增前置检查同原生身份/attempt、idle→busy和repair=null。原dirty/head/冻结C/C2/集成断言及计分预期不变；旧acceptance diff不变。每个等待边界与diff在`managed-flow-repair-01/`中，完整绿态待legacy-green-04，不冒充已通过。

## 16. 主控 #65：F06/F09异步收据重读

04已通过managed_frozen、手工来源拒绝和coop8；Recovery第二项的cleanup重读旧verify handle时多次驱动reviewer。仅在adapter的complete中记录一次性后续动作及原绑定；process/complete首轮调用显式绑定响应attempt/C。未改QualityDriver的严格状态检查、产品、Recovery源码、9项断言或任何屏障。

原CLI响应仍逐字返回；重读不是重新验收。incomplete/变更绑定不重试，新的handle不复用旧标记。离线复放与九项路径表在`recovery-cleanup-repair-01/`，原acceptance交接diff不变。Recovery全量绿态待legacy-green-05。

## 17. 主控 #69：F09异步review就绪等待

05的Recovery9项已通过。run首项读到了正常创建的中间状态；同review随后475毫秒内running。仅调整fixture finalize_run的推进条件、固定绑定及期限，并把状态CLI查询限制在剩余时间内；requested不等于通过，失败/unknown/超时不重试。

主正例、helper-joins委托、duplicate run、matching reclaim、同步fixture_existing_dispatch及MultiTurn的路径表在`run-review-wait-repair-01/`。没有改acceptance hunk、业务断言、产品或屏障；完整run绿态待legacy-green-06，离线控制流复放单独标注。

## 18. 主控 #71：完整受控回归与P-review审批边界

legacy-green-06的22步均按预期完成，W01–W07/F01–F14迁移已在coop8/recovery9/run18及相关T-075/T-076-1受控回归上通过；Recovery仍逐字不改。F10/W07的来源红态及相应候选绿态均保留，W07反事实有真实Git引用变化。详细读回在`p-review-preparation-checks-02.json`，原失败01–05不动。

新增P-review只验证真实只读沙箱和B结论通道，不修改旧acceptance断言或已通过的产品字节。外部观察器在原node-pty启动前核对审批argv，随后调用原spawn；不提供受控原生记录、身份、Stop或结论。sentinel用普通可写文件，将由主机对照证明写操作能成功；真实reviewer内必须拿到结构化EPERM/EACCES及不变的文件/ref。该探针尚未执行，不能写PASS；此处不增加白名单例外。

## 19. 主控 #76：普通速度期望

本轮不改acceptance的任何hunk；仅新增workbench里的worker/reviewer无service_tier覆盖及default记录断言，并同步旧真实probe报告/launch期望。原TRACER-READONLY-ARGV内容不改，单点reviewer-writable变异体继续必须命中该编号。两个新无Fast断言在保留的01旧产品快照上预期失败，候选预期通过；动态证据待单阶段launch-policy运行。P-review01材料原样保留，02重新冻结，无Fast且仍只读、不续接。

## 20. 主控 #82：显式default契约

无参数继承普通档的约定已被用户最新决定替代：两个workbench启动参数方法现在要求唯一`service_tier="default"`及配对-c，编号改为TRACER-WORKER-DEFAULT-ARGV、TRACER-REVIEWER-DEFAULT-ARGV。旧NOFAST编号和运行证据作为历史保留。新缺参红态用未启动的real-delivery01冻结产品；priority变异体证明错误值即使record仍default也必须被拒。原TRACER-READONLY-ARGV不改，Recovery/Coop/Run断言和既有白名单hunk不变。动态取证待主控运行，不把静态准备计为业务PASS。


## 17. 主控 #92：独立交付审查与最终范围核对

独立只读审查为PASS / LIMITED_GO，无需红态修复的新发现。审查后更新README及交付文档/收据；暂存检查另发现新controlled_quality_pty.ts第13行空行尾随两个空格，仅删除这两个空格。失败及diff保存在source-staging-check-01，最终核对严格限定差异；产品、hooks或acceptance字节不变，没有改变测试行为。W01–W07/F01–F14仍是唯一迁移白名单；Recovery9逐字不变。完整142文件首次读回一致，最后范围核对仅允许README事实更新与上述空白修正，其余冻结源码不变；证据为delivery-review-readback-01/run.json、final-delivery-check-01/run.json，重放命令见RESULTS末节。真实预算7/8。
