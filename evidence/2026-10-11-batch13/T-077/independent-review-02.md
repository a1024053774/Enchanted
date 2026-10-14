STATUS: NO_GO

TARGET:

- 产品：`5d0bf1e84c02fbcb4b7699cdd9a48c4f6582c6b4`。
- 夹具：`178d15f3ddb13f06a00eac19d7655225519f98e2`。
- 本次证据候选与复审 HEAD：`05ed480bcc9882fb2c8074c4b8ad8c3727d66c2d`。
- 仅复审 F1 的七条冲突红态、06/07 定向变体、分类器及对应候选绿态。原 F1 中“06/07 未到达目标断言却计红”的问题已解决；本次提示 (c) 要求的普通断言失败分类仍有一处差异。这里的 NO_GO 仅限这次 F1 差异复审；T-077 整票仍为 INCOMPLETE，待主控验收。

EVIDENCE:

下文 `E` 为 `evidence/2026-10-11-batch13/T-077`，`R` 为 `E/outside-conflict-red-final-02`。只提取先前报告的 F1 段作为待核对问题，没有将其作为结果 oracle。

**(a) 目标与前置清单。** 冻结夹具 `workbench/tests/test_worktree_lifecycle_e2e.py:30`、`:41` 保存七个不同的稳定目标标识及逐案前置；runner `E/run-conflict-red-final-01.py:24`、`:33` 与它们一致。逐案读回 `R/red-01`～`red-07` 的 `result.json`、`unittest.txt`、readbacks 与夹具归档，而非只读顶层 PASS：七案所需前置均各出现一次、值为 true、有具体 details，并位于目标步骤之前。

- 01 要求 `scenario_prepared`、`worker_session_input_available`、`text_conflict_observed`、`conflict_handling_entered`。
- 02～04 在共同的场景准备、文字冲突观察与冲突登记之前，分别读取 `ended_session_input_configured`、`unknown_session_input_configured`、`delivery_unknown_input_configured`；归档的 `conflict-mode.json` 与记录相符。
- 05 要求场景准备、`git_io_failure_observed`、`target_verify_executed`。原始 merge 返回 73，unmerged 为空；失败分类本身没有被当作前置。
- 06/07 要求场景准备、文字冲突观察、冲突登记、`conflict_delivered`、`explicit_resubmitted`、`target_verify_executed`。

这里的 `conflict_handling_entered` 对应 `core.ts:1604` 在调用 `writeConflict` 前保存的 `verification_conflict` 事件，证明已到达冲突登记阶段，不证明回写已经成功。01～04 的被测回写、替换或上报结果没有被列为自己的前置。01 的投递为 false、显式重交为 false；02 没有向已结束会话投递，这些均原样保留，不能当作 06/07 的前置凭据。它们也没有被豁免为成功。

01～04、06/07 的原始 verification 均有 `M=null`、merge 返回 1、三个未合并索引条目、`src/settings.json` 冲突文件及真实冲突标记。readbacks 与归档提供同一 C1/G/attempt 的记录。输入配置与 native session/身份来自受控夹具；Git、daemon 进程、命令行调用和 SQLite 读回是实际本地依赖。

**(b) 06/07 的定向变体与目标命中。** `E/run-conflict-red-final-01.py:58`、`:61` 只改变对应守卫：06 仅在 `attempt.rework.state="submitted"` 时绕过路径拒收；07 仅在同一状态下跳过 task 尾注不匹配判断。冲突回写调用保持存在，其余身份尾注、缺失尾注、路径枚举与提交绑定逻辑保持存在。

- 06：`R/red-06/readbacks/t-m8onmrjr.json` 中事件顺序为冲突登记 → 投递完成 → 显式重交 → path_check。C2 为 `1377cb35f6d5da4cf66ddfa095d75f43bfff8a1d`；归档 commit 的父提交就是 G，工作区有 `src/private/secret.txt`。path_check 原样记录 forbidden 包含该路径且 passed=false，但变体 verify 返回 `ok=true`。`01-test_conflict_rework_still_rejects_forbidden_path/unittest.txt` 仅在冻结夹具 `:886` 的指定拒收断言失败。
- 07：`R/red-07/readbacks/t-itx4_bss.json` 保留相同阶段顺序。C2 为 `babf2d60db376dbf18bf32bedecd0af06713fcad`；归档 commit 的父提交就是 G，尾注明确为 `A2A-Task: foreign-task`。trailer_check 对该 C2 返回 passed=true，verify 返回 `ok=true`。`01-test_conflict_rework_still_rejects_foreign_trailer/unittest.txt` 仅在冻结夹具 `:897` 的指定拒收断言失败。

两案的 `commands.json.gz` 均记录首次 verify 为 `merge_conflict`、随后 submit 为 `ok=true`、第二次 verify 为 `ok=true`；投递文件与 transport prompts、message_id 和 SQLite 事件一致。两案没有停在 repair 的提交成功断言。

**(c) 分类器。** 冻结夹具 `:61`～`:91` 将冲突案的旧通用 business_red 规则覆盖为目标规则，要求目标步骤与 contract 唯一、同一目标为 false、所需前置完整且先于目标，并排除 errors、skipped、cleanup_failures、无 unittest failure 和错误测试数。`_callCleanup():595` 保存清理失败来源。七份原始红态全部命中指定目标，errors/skipped/cleanup_failures 均为零；06/07 各只有一个 failure。01 有三个 failure，其中第一个为指定目标，另两个是目标后的连带失败，未冒充前置成功或另两个目标的覆盖。

目标未到达、前置缺失/false/迟到、setup 失败及登记的清理失败会进入 NOT_COVERED；普通断言失败本身不会计红。然而“目标通过后出现普通断言失败”仍返回 TARGET_PASSED，未遵守提示 (c) 的 NOT_COVERED 要求，见唯一确认发现。

**(d) 断言和 oracle。** 对照 `5d0bf1e8` 至冻结候选的允许路径 diff，并逐个核对 `a5c6d50c48fa856cf85fe7d2fefddda61f5d2ade`、`178d15f3ddb13f06a00eac19d7655225519f98e2`、`fba6ebb56aead710c8c2f153842ddf76258702ef`、`628234b7ac1b067bbb404ad7140c8a551a4361f1`、`05ed480bcc9882fb2c8074c4b8ad8c3727d66c2d` 的允许差异，没有用 commit message 解释实现。06/07 将原来的两个断言合为严格的 `ok is False` 且固定错误码的目标断言，未放宽业务要求。原有工作分支不变、禁止路径不得到达 completion oracle、外来尾注 check 必须失败等断言仍保留。期望值来自夹具任务卡、输入文件、预设尾注和独立内容断言；产品输出作为被测实际值及阶段读回，没有成为期望值的来源。

`R/candidate` 七项都为一项测试、零 failures/errors/skipped/cleanup_failures，目标均为 TARGET_PASSED；候选 06 实际返回 `path_boundary_failed`，07 返回 `trailer_task_mismatch`。候选对应原始 path_check/trailer_check 也拒收相应输入。

**(e) 冻结身份。** Git 的产品差异及工作区产品差异为空。按 Git 对象类型比较全部 `workbench/src`、`workbench/hooks` 的 48 个受控路径，文件字节及符号链接目标均与完整产品版本一致。`R` 八个 `sources.tar.gz` 的 21 个产品 TypeScript 文件均相同；生命周期夹具、直接 daemon adapter、conflict host、command_evidence 均与夹具版本字节一致。`E/outside-conflict-red-final-02-preparation/frozen-source-and-harness.tar.gz` 保存完整 48 个产品路径，未缺失或变化；其中 F1 夹具、runner、分类器检查源码也与冻结 HEAD 一致。

preparation 的机器 `plan.json` 保存四条变异配方、七案与八个阶段；实际 `R/run.json`、receipts、preflight 与 host ready 都将红态绑定到对应隔离变体路径，将候选绑定到仓库产品路径。实际运行 checkout 为 `628234b7ac1b067bbb404ad7140c8a551a4361f1`，随后证据提交成为冻结 `05ed480b`，产品及夹具没有变化。八份 preflight 记录 Node `v26.5.0`、Git `2.52.0`、外置盘已挂载、source_diff 为空；各阶段 stderr 均为空。readiness JSON 的 PASS 只覆盖交付完整性，它明示当时 rerun INCOMPLETE；没有将它代作业务验收。

FINDINGS:

**P2 — 普通断言失败后的覆盖分类仍不符合本次 (c) 契约。**

- 冻结位置：`workbench/tests/test_worktree_lifecycle_e2e.py:84`；直接检查源码 `E/check-conflict-classifier-01.py:82`。
- 可达输入已在该检查源码中明确声明：`inputs(passed=True)`，设置 `failures=1`，再追加 `assertion_id=None, pass=False` 的普通失败 contract；前置完整，errors/skipped/cleanup_failures 为零。目标步骤与目标 contract 均为 true，故 `target_failed=false`、`target_passed=true`。分类器只在 `target_failed and not failures` 时处理 failure 数；其 coverage 分支确定返回 TARGET_PASSED，而不是本次提示 (c) 明确要求的 NOT_COVERED。这是静态可达结论，本复审未执行新测试。
- 原始定位依据：`R/candidate/01-test_conflict_active_worker_reworks_and_integrates/result.json` 记录目标通过后的后续 contract；对应冻结测试 `:751` 之后仍执行 replay、显式重交及普通 assert，普通断言失败可以发生在已通过目标之后。已有分类器检查 `:85` 只断言 business_red=false，没有核对覆盖类别，因而漏掉这一差异。
- 影响：这类失败不会误计 business_red，也不会令当前 runner 候选总验收通过；但保存的 target_coverage 会将按本次契约应为 NOT_COVERED 的案标为 TARGET_PASSED。不能据此报告分类要求全部满足。没有确认当前七条红态被此处误计。
- 最小修正：在目标未失败而 unittest 存在 failure 时登记普通断言失败的 classification issue，使 coverage 为 NOT_COVERED；在已有普通断言反例中同时要求该类别。保留目标真实失败后的连带失败事实，不把它们改写为新目标命中。本 reviewer 没有修复。

P0/P1/P3：无确认发现。原 F1 的 06/07 目标未到达问题已解决；本次分类契约差异未解决，确认发现数为 1。

COUNTEREXAMPLE:

下表位置均指冻结夹具的目标调用行；原始失败文件位于 `R/<阶段>/01-<case>/unittest.txt`，case 名由对应 result.json 保存。

| 阶段 | 变体 | 目标标识 | 失败位置与实际结果 | 前置与真实类别 |
| --- | --- | --- | --- | --- |
| 01 | no-conflict-feedback | CONFLICT-ACTIVE-WRITEBACK | :751；原会话 feedback 为空；另有 :759、repair :742 连带失败 | 四项前置成功且在目标前；TARGET_FAILED，目标命中 |
| 02 | no-conflict-feedback | CONFLICT-ENDED-NEW-ATTEMPT | :798；attempt 不变、fence 仍为 1 | ended 输入及其余三项前置成功；TARGET_FAILED |
| 03 | no-conflict-feedback | CONFLICT-UNKNOWN-SESSION-REPORT | :834；system issues 为空 | unknown-session 输入及其余三项前置成功；TARGET_FAILED |
| 04 | no-conflict-feedback | CONFLICT-UNKNOWN-DELIVERY-ONCE | :844；feedback 数为 0 | delivery-unknown 输入及其余三项前置成功；TARGET_FAILED |
| 05 | io-as-text-conflict | CONFLICT-GIT-ERROR-CLASSIFICATION | :878；I/O 返回 73、unmerged 为空，却返回 merge_conflict | 三项前置成功；TARGET_FAILED |
| 06 | rework-path-guard | CONFLICT-REWORK-FORBIDDEN-PATH | :886；禁止路径存在，verify 为 ok=true | 六项前置成功且在目标前；TARGET_FAILED，原 F1 缺口已补齐 |
| 07 | rework-trailer-task-guard | CONFLICT-REWORK-FOREIGN-TRAILER | :897；C2 为 foreign-task，verify 为 ok=true | 六项前置成功且在目标前；TARGET_FAILED，原 F1 缺口已补齐 |

分类器额外反例为上述“目标 true + 普通 failure=1”输入：业务红态为 false，实际覆盖分支为 TARGET_PASSED，本次契约要求 NOT_COVERED。该结论来自冻结源码的静态分支核对，无新增运行证据。

LIMITATIONS:

- 只完成这一遍限定 F1 复审；没有复审整票、运行新测试或启动任何 daemon/socket/PTY/Electron/模型 CLI，没有访问 auth、进程状态或实施聊天及禁读文档。
- 请求的 reviewer 配置为 gpt-6.1-sol/xhigh/fork_turns none；实际模型、思考强度及供应商 tier 未独立观察。被测真实模型回合为 0；受控 session、身份、模型字段和反馈 transport 不证明真实供应商边界。
- 红态 sources.tar.gz 保存未变异产品；隔离变体通过冻结源码、唯一替换配方、runner 及 host ready/命令路径绑定核对，未将归档原产品字节称作变体的运行源码字节。阶段不证明变体已经集成或产品放过非法输入。
- 开始与保存前 HEAD 均为冻结 `05ed480bcc9882fb2c8074c4b8ad8c3727d66c2d`。保留原有未跟踪 prompt、request 与 real-conflict-02/03；本次仅新增此报告，保存后再只读核对 HEAD 与工作区状态。

RULE:

本次延续 F1 的失败来源与分类收据不一致类别。机械检查放在已有 `E/check-conflict-classifier-01.py:test_other_assertion_failure_is_not_the_target`：对其现成输入同时要求 `business_red=false`、`target_coverage="NOT_COVERED"`，并由 `workbench/tests/test_worktree_lifecycle_e2e.py:61` 的分类器产生这一类别；它可直接捕获本次确认的普通失败分类差异，无需新增产品运行或以零 errors 代替目标命中。
