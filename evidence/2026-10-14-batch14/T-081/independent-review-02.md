STATUS: PASS
P2-01: RESOLVED

本状态仅针对审查 01 的 P2-01 与矛盾 Session 单案修正，不代表整个 T-081 验收通过。BASE：`3ee28bc3ad77595e23b77dbef34af20c5370dea9`；复审时 HEAD 仍为该版本。审查模型请求为 `gpt-6.1-sol`、`xhigh`；供应商实际 tier 未观察。

实际执行快照为 `duplicate-conflict-01/candidate-source.tar.gz`，配套记录为 `candidate-working-tree.patch`、`source-manifest.json`、`driver.py`。归档内六份待审测试均与当前文件逐字节相同，四份已跟踪测试的归档 patch 也与 BASE→当前的对应差异一致；两份新增测试由源码归档保存。执行 driver 与归档内 `run_t081_duplicate_case.py` 相同。相关产品 `core.ts`、实际 host 与共享 harness 的冻结内容与 BASE 相同。结束前再次比较，六份测试未变化。

拒收预期有独立身份依据。规格 `.project-map/specs/native-cli-orchestration-2026-10-10.md:140` 的“提交尾注”列出 `A2A-Task`、`A2A-Attempt`、`A2A-Session` 等身份；T-072 ticket 第 19 行“提交追溯”把任务、attempt、会话等绑定到每个会话的环境与提交，并要求门禁核对候选里的每个提交。这里的契约解释是：同一提交同时声明本会话和另一个会话，不能提供一致的本 attempt/会话追溯身份，因此应拒收。该推论不依赖实现当前采用的“恰好一个”语法检查，也不依赖新增测试常量、输出中的 PASS 或 `invalid_trailers`。上述原文没有规定本案必须使用哪个错误码，也没有明确同值重复的错误语义；本复审不补写这两项产品规则。

原始输入不是同值重复。直接在内存中读取两份 `fixtures.tar.gz` 的 Git 提交对象，正文均与各自 `commit-*.json` 一致：

| 运行 | 候选提交 | 本 attempt 的 Session | 第二个 Session |
| --- | --- | --- | --- |
| red | `90577761cdcc71baf8cf4df6320301966b609f6d` | `a91493b2-5394-4d26-ad28-2e5b50de0c62` | `00000000-0000-4000-8000-000000000181` |
| green | `9c13dc1fa091037a4790fa5749dd2a47e1ebfaa2` | `5928f3fe-a19b-4700-acb5-de17ecbb2fcb` | `00000000-0000-4000-8000-000000000181` |

每份正文恰好两条 Session，其中恰好一条等于归档 SQLite 中该 attempt 的 `session_id`；对应 Attempt 分别为 `97501b75-e30e-4fe8-bb0b-f137873c2b9d`、`aa758405-399f-472d-b506-54dfc23fff71`。其余八个尾注字段各一条且非空。门禁原始 `trailer_check` #72 对两值的解析与提交正文相符。

唯一变异 `session-cardinality.patch` 只在 Session 上放宽数量检查。必需字段集合、字段存在及首值非空检查、其他字段的单值检查、任务不匹配检查，以及原有 attempt/session/role 身份比较均保留。按冻结 `prepare_t081_mutants.py` 的唯一替换重建差异，结果与留存变异 patch 完全相同；实际 red host 与 CLI 参数均指向 manifest 中的 mutant。第一条 Session 是本会话，使放宽后仍保留的首值身份比较可以通过，目标缺陷因此可达。

反例证据来自原始运行记录，而非状态标签。red 的 `command-0030.stdout.bin` 是 `ok: true`，命令 exit 0、stderr 为空；SQLite 记录 #72 尾注通过、#73 verification passed，随后进入 reviewing 并有 review_started。测试先通过输入和目标检查断言，再在 `BW-REJECT-trailer_duplicate` 抛出 `ContractFailure`，进程 exit 1；没有 harness_error 或 cleanup_failures。它证明只取消目标数量检查即可放过这份矛盾身份，目标业务断言能发现已知坏实现；不声称 red 已完成集成。

green 的同一编号原始 verify 回执为 `ok: false, error: invalid_trailers`，exit 1、stderr 为空，与 observation 完全一致。SQLite #72 记录该候选尾注拒收，#73 verification failed，#86 delivery_rejected，#87 rejected 使用同一错误码。后续真实 integrate 命令 #35 返回 `not_verified`，并追加 #88 rejected。最终任务/attempt 均为 submitted，integration_intent 为空；没有 integrated 或 score_recorded 事件。main 仍为 `30a7947ba21fc965a65a5b2112a878ad0ba2bcbf`，归档 main reflog 只有初始提交；worker 与 verification 引用保留候选提交，与 `git-readback.json` 一致。`run.json` 如实将 `invalid_trailers` 记为 actual_refusal_code，expected_refusal_code 为 null。

上述 SQLite 核对直接读取 red/green fixture 归档内 `state/state.sqlite3`，仅在内存副本上将 WAL 文件头读写模式字节改为回滚模式后 deserialize；没有解包或更改证据。其中 tasks、attempts、verifications、events 四表与各自 `database-readback.json` 相同，observation 的事件区间也与原数据库一致。

原同值案已降为观察：本次 `same-value-observation.json` 明确 `counted_as_pass: false`；冻结 `collect_t081_closeout.py` 从旧 bad_cases 中排除 trailer_duplicate，保留 historical_row，并只在新矛盾身份单案满足替代条件时计入一次。完整 suite 的对应映射也改用 `trailer_session_cardinality`。这解决了 P2-01 所指“同值重复没有独立拒收 oracle 却被计为坏行为通过”的问题。

原始证据均在 `evidence/2026-10-14-batch14/T-081/duplicate-conflict-01/`：顶层 commands.jsonl 与 command-output、session-cardinality.patch；red/green 下的 run.json、fixtures.tar.gz；各 trailer_duplicate 目录中的提交正文、commands.jsonl、command-0030 stdout/stderr、case.json、duplicate-trailer-check.json、observation.json、database-readback.json、git-readback.json，以及 green 的 command-0035 stdout/stderr。

限制：本次是只读证据复审，没有运行测试、模型、PTY 或 daemon，没有修改实现或夹具，也没有 add/commit/submit。受审运行使用受控 PTY、进程和原生输入，真实 Codex 回合数为 0；不据此评价真实模型能力。未读取或重审其他坏行为、能力、CAS、回归证据，未重新核验 full-04 其他内容；不把这次单案红绿结果扩张为最终组合入口完整重跑或整个 T-081 通过。此次范围内未发现仍阻止 P2-01 解决的问题。
