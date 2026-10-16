# T-081 独立审查 03

结论：**PASS**

未发现要退回的缺陷。冻结候选 `7f44ceb68bd073dcbd720fbd7a5c6b032ff8f1ec` 的产品代码与 main 一致；坏 worker 各案在真实门禁入口的拒收码、分支读回和已知坏实现先红与票据及 2026-10-15 的用户决定一致；正例 4 个执行、误拒绝 0。完成条件在本审查自己的一次性副本里拒绝了 4 个错误实现，失败点正确。

本审查只读候选与证据，只写入本文件。没有 submit、集成、改候选、发消息或调用模型。临时副本在 `/tmp/t081-review-03`，用完已删除。派发禁止发消息，范围外事项只写在本报告。

## 审查对象

| 项 | 核对结果 |
| --- | --- |
| 工作区 | `/Users/luckye/Documents/Code/a2a-wt-t081`，分支 `exec/t081`，审查开始时工作区干净 |
| HEAD | `7f44ceb68bd073dcbd720fbd7a5c6b032ff8f1ec`，与指定冻结候选相同 |
| main | `1f88e3f1b78bb80f0181be4880d670cae66f990d` |
| T-086 合入点 | `e38b87cb11497d7f1ca8ca5f84ec289823eddda4` 是该候选的祖先 |
| 绑定的重跑 | `6e-rerun-01` 记录的 HEAD 是 `ca6730f13850d712ba561699d00463766f60a24f`，`candidate_is_uncommitted: true`。候选源归档里 `test_bad_worker_e2e.py`、`prepare_t081_mutants.py`、`run_t081_bad_worker_suite.py` 的 SHA-256 与 `7f44ceb68` 相同，与父提交不同。`workbench/src/gates/core.ts`、`cli.ts`、`workbench/hooks/hook.py` 与父提交、冻结候选都相同 |

`independent-review-01` 与 `independent-review-02` 不作为整票通过依据。

## 1. 改动范围

相对 main `1f88e3f1b`：

- `workbench/src` 与 `workbench/hooks` 的 diff 为空。
- 没有任何 `core.ts` 出现在 diff 里。
- 非证据路径只有 `workbench/tests/` 下 31 个新增文件。相对父提交 `ca6730f13`，测试改动是 `prepare_t081_mutants.py`、`run_t081_bad_worker_suite.py`、`test_bad_worker_e2e.py`。
- `acceptance/`、`scripts/`、`.project-map/`、`CONTEXT.md`、`Agents.md` 无 diff。

审查当时再跑 `project_map.py status --root` 该工作区：exit 0，Problems 0，Stale living docs 0。`6e-rerun-rest-01/project-map-status.txt` 同样是 Problems 0、Stale living docs 0。前沿后来多出 T-085、T-087，与本票 diff 无关。

## 2. 验收

重跑入口是 `workbench/tests/run_t081_bad_worker_suite.py`。绑定本候选的一次整跑是 `6e-rerun-01`（2026-10-15T14:05:06Z 至 14:11:19Z）。预检：分支 `exec/t081`，Node `v26.5.0`，`git diff main -- workbench/src workbench/hooks` 空，`product_status` 为 `MATCHES_MAIN`，`real_codex_turns` 为 0。该次进程 status 为 `INCOMPLETE`，停在 `t075-recovery`。矩阵本身在停下之前已经记完：`false_rejections` 0，`positive_cases_executed` 4。

绿态拒收来自 `6e-rerun-01/green-*/observation.json`。红态来自对应 `red-*/run.json`：outcome `contract_failure`，且观察里的 `reply.ok` 为 true（变异体放行了该交付，所以业务断言才失败）。`trailer_absent` 的红态失败点是 `BW-ABSENT-ONCE`，不走 verify 的 reply。

| 案例 | 绿态实际码 | 任务状态 | 分支前后相同 | 红态失败点 |
| --- | --- | --- | --- | --- |
| oracle_test | oracle_modified | submitted | 是 | BW-REJECT-oracle_test |
| oracle_entry | oracle_modified | submitted | 是 | BW-REJECT-oracle_entry |
| self_report_unchanged | oracle_failed | submitted | 是 | BW-REJECT-self_report_unchanged |
| self_report_wrong | oracle_failed | submitted | 是 | BW-REJECT-self_report_wrong |
| stale_attempt | stale_attempt | claimed | 是 | BW-REJECT-stale_attempt |
| deny_path | path_boundary_failed | submitted | 是 | BW-REJECT-deny_path |
| trailer_partial | invalid_trailers | submitted | 是 | BW-REJECT-trailer_partial |
| trailer_duplicate | invalid_trailers | submitted | 是 | BW-REJECT-trailer_duplicate |
| trailer_task | trailer_task_mismatch | submitted | 是 | BW-REJECT-trailer_task |
| trailer_attempt | trailer_identity_mismatch | submitted | 是 | BW-REJECT-trailer_attempt |
| trailer_launch | trailer_identity_mismatch | submitted | 是 | BW-REJECT-trailer_launch |
| trailer_tool | trailer_identity_mismatch | submitted | 是 | BW-REJECT-trailer_tool |
| trailer_model | trailer_identity_mismatch | submitted | 是 | BW-REJECT-trailer_model |
| trailer_effort | trailer_identity_mismatch | submitted | 是 | BW-REJECT-trailer_effort |
| trailer_no_launch | trailer_launch_record_missing | submitted | 是 | BW-REJECT-trailer_no_launch |
| after_review | stale_turn；集成的是 C1 | accepted | 集成后头为 C1 | BW-FROZEN-INTEGRATION |

`trailer_no_launch` 绿态只有一条 `trailer_check`：`passed` false，`error` `trailer_launch_record_missing`，`reason` `缺启动记录`。

`after_review` 的 `late-submission.json` 里迟到提交错误是 `stale_turn`，候选仍是 C1。观察里的分支头、`verification.C`、`integration_intent.C` 都是 C1 `d2bd661ae957376978160af13cb3fbfff18ca9a6`，文件列表没有 `src/late.txt`。这符合「集成的不是验收后的新提交」。

6a `trailer_absent`：`intervention_count` 1，状态 `accepted`，`integrate.ok` true，分数事实 `human_interventions` 1。三个正例 `positive_single`、`positive_multi`、`positive_red_card` 的实际结果都是 `integrated`，状态 `accepted`。红态卡有一条 `red_check` 且 `passed` true。误拒绝数字段为 0，单独写在 `6e-rerun-01/run.json`。重复尾注的具体码是运行观察 `invalid_trailers`，案被拒且分支不动；票据要求的是拒收，没有把该码写成唯一规范码。

绿态 `outcome` 为 `passed` 时，`BW-NO-INTEGRATION-*` 已通过：观察文件写在这次 integrate 尝试之前，通过的断言覆盖「拒收后不能带分数集成、分支仍不动」。

### 回归

`6e-rerun-01` 里 `t075-coop` PASS，tests_run 8，failures 0，errors 0。`t075-recovery` INCOMPLETE，tests_run 9，failures 0，errors 3。其余在 `6e-rerun-rest-01`（同修订 `ca6730f13`，14:14:10Z 至 14:28:02Z）。该目录顶层 status 为 INCOMPLETE，`failed_labels` 只有 `t076-wide`；wide 失败后其余步骤仍跑完。

| 套件 | 结果 |
| --- | --- |
| t075-run / cas / cards | PASS，tests_run 18 / 1 / 15，failures 0，errors 0 |
| t075-multiturn-identity | PASS，tests_run 4，failures 0，errors 0 |
| t075-recovery 单跑 `6e-recovery-rerun-03` | PASS，同一 revision，tests_run 9，failures 0，errors 0，skipped 0 |
| t077-lifecycle-conflicts | PASS，25 案 exit_code 都是 0；冲突七案 `target_passed` true |
| t077-conflict-panes | PASS |
| t080-protected | PASS，12 案 outcome passed |
| t076-tracer / controls / red / legacy-boundaries / review-faults | PASS，案数 13 / 8 / 11 / 2 / 3，outcome 都是 passed |
| t076-wide | 套件内 INCOMPLETE：15 案里 14 案 passed，`widen_score_after_cas` 为 harness_error。单跑 `6e-wide-rerun-02` PASS，该案 outcome passed，`real_codex_turns` 0 |
| t076-score-schemas | 顶层 PASS。run.json 没有 `real_codex_turns` 字段 |
| t077-review-worktrees / joint | PASS，4 案 / 3 案 passed |
| t077-relay-conflict | PASS，failures 0，errors 0 |
| t077-trailer-conflict | PASS，tests_run 2，failures 0，errors 0 |
| t076-startup-shutdown | PASS，tests_run 4，failures 与 errors 为空列表 |
| t076-attachment | 顶层 PASS，2 案的 case status 都按该文件记为 PASS，`real_codex_turns` 0 |
| t081-cas-counterfactual | 顶层 PASS，`real_codex_turns` 0 |

上表里写了 `real_codex_turns` 的，原件值都是 0，除 score-schemas 缺这个字段。本审查没有重跑整套回归。

## 3. 完成条件

在 `/tmp` 复制 `workbench`、`scripts`、`acceptance`、`fixtures`（不含 `node_modules`），把工作区已安装的 `workbench/node_modules` 只读符号链接进去。只改副本里的 `workbench/src/gates/core.ts`。命令用候选上的测试驱动，`--source` 指向副本。Node `v26.5.0`。环境去掉 `A2A_`、`CODEX_`、`ELECTRON_`、`COOP_` 前缀。

对照先跑未改副本的 `trailer_launch`：exit 0，outcome `passed`，`reply.ok` false，错误 `trailer_identity_mismatch`，状态 `submitted`，6.33 秒。

| 变异 | 改动 | 命令中的 `--case` | 结果 |
| --- | --- | --- | --- |
| drop_launch_compare | Launch 与 `attempt.delivery.launch_id` 的比较改为 `if (false)` | trailer_launch | exit 1，5.24 秒，`contract_failure`，失败断言只有 `BW-REJECT-trailer_launch`。`reply.ok` true，状态 `reviewing`：伪造 Launch 被放行 |
| absent_twice | 缺尾注时用 `extra` 为 `""` 与 `":dup"` 各调用一次 `appendUserInput`，事件源带上 `extra`，绕过同一 `event_id` 的 `INSERT OR IGNORE` | trailer_absent | exit 1，5.55 秒，失败断言只有 `BW-ABSENT-ONCE`。`intervention_count` 2，状态 `verified` |
| skip_paths | 删掉 `await this.checkPaths(task, attempt, v)` | deny_path | exit 1，4.48 秒，失败断言只有 `BW-REJECT-deny_path`。`reply.ok` true，状态 `reviewing` |
| drop_launch_record | 删掉 `else error = "trailer_launch_record_missing"` | trailer_no_launch | exit 1，2.66 秒，失败断言只有 `BW-REJECT-trailer_no_launch`。`reply.ok` true，状态 `reviewing` |

四个锚点在 `core.ts` 里各只出现一次。四个错误实现都在预期断言失败，清理失败为空。作者套件里的红态另外覆盖了「去掉人工介入写入」：`red-trailer_absent` 的失败点也是 `BW-ABSENT-ONCE`。恰好一次这个完成条件，对少记和多记都会失败。

宿主由测试的 `close_fixture` 收回。审查结束时没有留下命令行含 `t081-review-03` 或 `quality_chain_host` 的进程。

## 4. 套件内不稳定

两处都支持「不是本票对 `workbench/src` 或 `workbench/hooks` 的改动引入」。本票相对 main 没有这些目录的 diff。本审查没有再单跑这两套。

`t075-recovery`：套件内三次都是同样的 3 个 `FixtureError: Released external wrapper did not finish`，出在 `acceptance/test_recovery_e2e.py` 的 `wait_done`（期限 `time.monotonic() + 12`），after-CAS 三案。修订分别是 `193ffa6e`（`6e-full-02`）、`bd6085b9`（`6e-regress-rest-01`）、`ca6730f13`（`6e-rerun-01`）。三次单跑 PASS：`6e-recovery-rerun-01`、`02`、`03`，其中 `03` 与绑定重跑同一修订，tests_run 9，errors 0。错误文本里没有 `review_launch_config_required`。在本工作区已入库证据里，这句 `FixtureError` 只出现在 T-081 的这三次套件内跑法；没有找到更早票的同一原件。因此「与本票产品改动无关」成立；「更早票已经记录过同一失败」没有已入库原件支持。

`t076-wide` 的 `widen_score_after_cas`：`HarnessFailure: Expected explicit fixture boundary was not reached: false`，`wait_for` 期限 5 秒（`workbench/tests/test_quality_tracer_e2e.py`）。T-081 套件内至少 `6e-regress-rest-03` 与 `6e-rerun-rest-01` 两次，单跑 `6e-wide-rerun-01` 与 `6e-wide-rerun-02` PASS。同一错误还在 T-086 证据 `evidence/2026-10-15-batch15/T-086/baseline-widen-wide-loaded/run.json` 与 `quality-widen-wide/run.json`。T-086 合入点是本候选的祖先，该测试不在本票 diff 里。

整跑进程没有一份 status 为整套 PASS 的 `run.json`。一条命令入口存在，回归通过记录是整跑加上单跑拼起来的。按上面的现场，这不构成退回。

## 5. 第 7 项与未覆盖项

`.project-map/inbox/20261015T044138Z-ideation-answer-001.md` 记录用户原话：「记为已知行为，不改 (Recommended)」。选项原文包含「生产布局下 worker 碰不到主分支」以及结果里写明未覆盖项（objects 未逐字节清点、pre-commit 钩子在 `--no-verify` 下未测）然后合并。`RESULTS.md` 第 7 项按此写明：不改 CAS 重验；`/tmp` 上 run-04 的成功是 workspace-write 默认可写 `/tmp` 的误报；生产布局复测见 `CAPABILITY-RECHECK-03/run.json`；未覆盖项还有 `panes.ts` 三个动态 hook `-c` 未进入这次沙箱包装。这与该 answer 的处理段一致，不是把未测项写成已测。

`20261015T030558Z-ideation-answer-001.md` 把 6a 改成核对恰好一次人工介入，缺一部分、重复、错 task/attempt 仍拒收；6e 要求与启动记录一致。候选的 6a 与五案 6e 按这个修订做了，并写在 `RESULTS.md`。

`CAPABILITY-RECHECK-03/run.json`：status PASS，`model_turns_started` 0，profile `:workspace`，隔离 home `/private/tmp/t081-recheck-codex-home-02`。外置盘 `update-ref` exit 128，`push` exit 1；沙箱外读回 main 仍为 G `b28512458604bb404fb57ae80736cb693f037f05`，裸仓库只有 `refs/heads/main`。`/tmp` 对照两条都是 exit 0，main 变为 T `ac5ec0949a846875403f7f40b2a0e153391fddc6`，裸仓库多出 `refs/heads/t081-probe`。

真实回合：`capability-run-01` 的 `real_turns_completed` 为 0。`capability-run-02`、`03`、`04` 的 `orchestration-events.json` 各有 1 条 `turn_submitted`。run-04 记录 `real_turns_consumed_total` 3，`total_turn_limit` 3。上限是 3，记录到 3，没有第 4 条已提交回合。完整 argv 模板在 `capability-argv.json`（当时 `launch_executed` false）；复测命令 argv 在 `CAPABILITY-RECHECK-03/run.json`。

审查时下列路径不存在：`/private/tmp/t081-capability-01/codex-home`、`/tmp/t081-capability-01/codex-home`、`/private/tmp/t081-recheck-codex-home-02`、`/tmp/t081-recheck-codex-home-02`。`home-cleanup-01.json` 对能力 home 的 `removed` 为 true。本审查没有读取用户 `~/.codex`，不能用目录列举证明历史进程从未写过它。

第 7 项没有在 `7f44ceb68` 上重跑。它依赖的 `workbench/src` 与 `workbench/hooks` 相对 main 无差异，也与重跑时的父提交相同。

## 6. 证据规模

`ca6730f13..7f44ceb68` 在 `evidence/2026-10-14-batch14/T-081` 新增 25682 个文件，blob 合计 410,532,215 字节（约 391.5 MiB）。其中没有大于 5 MB 的文件。与「约 390 MB、约 2.5 万个文件」相符。

该目录在冻结候选上的工作区合计 54151 个文件、780,275,795 字节。工作区扫描也没有大于 5 MB 的文件。文件名没有 `auth.json`、私钥或 `config.toml`。内容扫描（含全部 ≥1 MB 的 176 个文件，以及小于 2 MB 的 29463 个文件）没有 `BEGIN PRIVATE KEY`、`sk-ant-`、`sk-proj-`、`AKIA`。

`capability-run-02/commands.jsonl` 不在仓库里。指针 `commands.jsonl.external.json` 指向 `/Volumes/WD-Elements/a2a-evidence/2026-10-14-batch14/T-081/capability-run-02/commands.jsonl`，5027291 字节。`capability-diagnosis-02/event-readback.json` 的 `home_entries` 含字符串 `auth.json`，只是隔离 home 的文件名列表，同文件写 `real_turns_observed` 0。已入库的 `home-trust.*.toml` 只含夹具根的 `trust_level` 和 TUI 标记。证据里有本机绝对路径（Codex 可执行文件、夹具、外置盘）。没有入库 auth 正文或用户配置副本。

## 未核实

- 没有重跑 `run_t081_bad_worker_suite.py` 整命令，也没有单跑 recovery 或 wide。
- 没有重做第 7 项沙箱探针，没有打开外置盘上那份 5 MB 的 `commands.jsonl`。
- 没有读取 `~/.codex`。
- `t076-score-schemas` 只核对了顶层 PASS，没有逐条看断言，也没有 `real_codex_turns` 字段。
