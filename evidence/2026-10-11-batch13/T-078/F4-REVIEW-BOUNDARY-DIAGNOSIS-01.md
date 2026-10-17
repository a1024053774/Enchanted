# F4 单用例故障：审查报告已接受，结束边界拒绝（主控 #336）

2026-10-16。**保存现场的根因定位 PASS；跨版本实跑 INCOMPLETE；修复/整组复验 NO_GO，需主控裁定语义交叉。** 不改acceptance/、冻结protocol、core或legacy driver，不调整超时，不把旧结果改写成通过。

## 已观察到的事实

原场 `review-followup-regressions-01` 绑定6f9fae871：coop原8方法完整执行，7项无报错、1 error、0 failure；后续recovery/run/CAS/cards/变异均未运行。首败是 `test_submit_requires_clean_head_and_cannot_replace_frozen_candidate` 的verify之后等待review回收，不是整个8组未执行。实际宿主stderr只有MODULE_TYPELESS_PACKAGE_JSON警告，原生host已正常退出；没有缺schema/导入/权限启动报错。

[只读facts](review-followup-f4-diagnosis-01/facts.json) 来自已保存的JSON readback与tar内driver.jsonl，不打开停机SQLite：

| 实际时点 | 原件事实 |
|---|---|
| review_requested 115 | 候选C=`3cc14063399ae88551cb9e9ef324d695fb52b2af`；当时shared_refs已记录worker分支HEAD=`67ef506f7e1c6704f60cfce53046163a6f4483da`，已不等于C |
| review_result 122 | 门禁已接受report，task=verified/review=passed；review_requirements与report已入库；无review_protocol_failed |
| command_result 125/127 | shared refs与请求快照相同；worktree list里审查detached HEAD=C，worker HEAD仍67ef… |
| command_result 131/133 | 审查worktree HEAD=C且status为空，审查目录没有被改 |
| command_result 135 | worker HEAD仍67ef…，与review开始时相同，仍不等于C |
| review_lifecycle_failed 136 | phase=reclaim，error=`review_worker_workspace_changed`；task暂停，review unknown；review_reclaimed=0 |

driver的signal返回 `{}` 是真实Stop入口已接纳，不表示回收成功。`legacy_quality_driver.py:106`等不到review_reclaimed只是上述门禁失败的后果；把8秒加长不会改变结果。业务侧已经有可读诊断，driver等待期没有及时把它抛出，这是诊断易用性问题，不是本次根因；本轮不先修日志掩盖语义冲突。

## 契约交叉与归属

原验收 `acceptance/test_coop_e2e.py:505–536` 在提交冻结C之后，明确又提交一个later_bad到worker，再拒绝以它替换已存C，最后要求verify仍验证C。这个文件在150ef6516与main 0e6c2b833之间逐字相同；因此不能把它说成T078新改了预期。当前失败的worker前后HEAD相同，有证据支持“审查期间没有把worker HEAD从C改走”，不同HEAD在审查开始前已经存在。worker clean检查因HEAD短路失败未执行，不能补称门禁已读到worker clean。

T082新增 `core.ts:2353` 要求 **worker HEAD == review.candidate_commit**，之后才查分支/clean。新检查位于candidate-copy清理前，失败会暂停并阻止review_reclaimed，新的integrate前置也因此生效。报告协议已经通过，审查副本回收按当前guard正确拒绝；这不是把review_reclaimed凭空丢掉，也不是driver未回传T082字段。

T082原票/用户原话要求审查目录、worker worktree不被reviewer写、结束时干净、共享refs不变；原交付用例要求候选冻结后即使worker再有提交也不能改掉被验证C。**“worker在review开始前HEAD≠C，但审查期间未变，是否仍可验证冻结C”是两票需要明确的交叉。** 源码事实已指向T082新增guard；尚未运行两个历史版本，不能把“main也失败”写成实测，更不据此改产品或验收。

建议保持原冻结候选合同：候选/审查worktree继续绑定C；另在review开始时绑定实际worker HEAD/branch与clean状态，结束核对该worker边界没变，保留路径/身份、共享refs、结束后才可集成等T082保证。**这是待裁定的最小方向，不是本轮已实现或自动批准。** 若主控认为HEAD必须等于C是有意收紧，则应由契约owner处理旧验收冲突；worker不得改验收、在driver里reset worker到C、跳过回收或伪造review_reclaimed来取得绿态。

core审查结束逻辑超出T078原“转交/调用者身份”所有权。本轮按#336停在语义交叉，上报主控，等待安排实现范围；不擅自修改T082已合入的保证。

## 两版本同用例的待执行对照

精确命令见 [F4-DIAG-COMMANDS](F4-DIAG-COMMANDS-01.txt)。`compare-f4-review-boundary.py --check-only`只读Git对象、文件/依赖路径，不创建clone或跑测试；本轮会保存实际check-only输出。正式命令由主控沙箱外运行，新目录 `review-followup-f4-compare-01`，依次：

1. 合并前 `150ef6516f6ef5aaa6855631b770ce262991ffbf`。
2. main `0e6c2b833f6da64243f71d670ea45bb9116fda4d`。

各用一个临时shared clone、稀疏checkout代码/测试/夹具/脚本/地图，只读借用原objects；不改主仓引用、不rebase/reset/提交/push。依赖只在临时源码node_modules链接既有缓存，不链接/构建dist。每个版本的产品、acceptance、legacy driver、宿主都保持该提交原字节；**只覆盖旧runner为当前单case/证据选择器**（旧runner没有--case），保留原runner、精确overlay.diff，并前后拒绝任何其他源码差异。原业务方法和协议不改，overlay不把新quality driver套到旧产品上。

每版本只执行同一个继承的原方法，预期用例数1；如旧版PASS而main得到同一review_worker_workspace_changed，支持“上游guard造成原冻结候选场景回归”的判断。若main PASS、原版也失败、或先遇其他错误，则如实保留并重新定位，不用预期覆盖观测。顶层PASS只表示两次单用例结果已采集，须看各test_status/error/events，绝非产品PASS。

真实Claude/Codex/模型均0；最多一次受控宿主测试在跑。每用例180秒上限，超时保留runner PID/scratch/原stderr，不重试、不盲发信号。原测试teardown后再独立ps确认实际daemon PID已不存在，逐成员/字节核对原fixture tar才删本轮短/tmp fixture；两版本采集完再删clone scratch。若身份/退出/归档不符则保留，不自动清理。source archive仍在Git历史，runner overlay与命令、状态读回/原件进新目录；不直接打开历史SQLite，不改原F4失败目录。

## 修复后整组命令

新目录预留 `review-followup-regressions-02`。**当前不运行**：必须先完成语义裁定、获分配的最小修复和红绿/边界反例、冻结实际源码，并将review-followup-source.json更新为该修复提交；否则重跑仍会在同一处失败。随后沿原F4串行入口完整重跑coop8/recovery9/run18/CAS1/cards15和三变异，不能只续跑后7项掩盖coop缺口。实际修复若改变worker边界，还需T082“审查期间真改worker/refs/审查目录仍拒绝”的结束核对，不能拿原来小范围PASS背书。本文只交下一步命令模板与新输出位置，没有宣告修复完成。
