# T-086 独立审查

结论：**NO_GO**（角色卡要求的「需修复」）

冻结候选 `d9dcc107bd8ef122b83ed0c1226df3022fe37939`。`git rev-parse HEAD` 与 `git rev-parse d9dcc107` 相同。基线 `bb6c0ba352ff7cab1f470d2db055caac36387bab` 是其祖先。审查时工作树干净。本审查没有改产品代码，没有 commit，没有调用模型。

需修复的是这两案的完成条件。候选里的 `commit_worker` 确实读该 attempt 在 `worker-creations.jsonl` 的那一行，门禁比较没有放宽。完成条件在「写死与这条记录相同的常量」和「改从任务卡抄 Model/Effort」时仍然通过，看不出尾注是不是从启动记录取的。

## 发现

1. **完成条件不够格。** 宿主把任务卡的 `model`/`effort` 抄进启动记录，`cli_version` 固定为 `controlled-conflict-runtime`，`id` 等于 `thread_id`。M3、M4 不读 jsonl，两案仍然 PASS。缺一条能把记录和任务卡、和 `thread_id` 分开的检查：错误来源必须在 verify 上失败。本审查不指定唯一改法。
2. **清单少了两个调用方。** `test_quality_tracer_e2e.py`、`test_quality_widen_e2e.py` 经继承的 `QualityCase.commit` 写受管尾注，作者清单没有点名，本审查没有单独重跑。不能把它们写成通过。
3. **`run_worker_delivery.py` 的 unknown 期望与当前钩子、当前门禁对不上。** 这是代码和一份已归档真实回合里的事实，下面第 5 节列出三种时序。本审查不选择改钩子、改门禁还是改脚本期望。

## 1. 改动范围

`git diff --name-only bb6c0ba3 d9dcc107` 共 1733 个路径。其中 1731 个在 `evidence/2026-10-15-batch15/T-086/`。除此以外只有：

| 文件 | 改动 |
| --- | --- |
| `workbench/tests/conflict_acceptance_host.ts` | `createThread` 把 `sessionFacts` 使用的同一个对象写入 `worker-creations.jsonl` |
| `workbench/tests/test_worktree_lifecycle_e2e.py` | 新增 `launch_record`；`commit_worker` 用该行写 Tool/Model/Effort/Launch |

`git diff bb6c0ba3 d9dcc107 -- workbench/src acceptance scripts` 为空。`workbench/src/gates/core.ts` 的尾注比较仍是 Launch 对 `delivery.launch_id`、Tool 对 `delivery.cli`、Model 允许字面量 `unknown` 或 `delivery.model`、Effort 对 `delivery.effort`（约 1998–2003 行）。

写报告前 `project_map.py status --root .` 退出码 0，Problems 0，Stale living docs 0。T-086 仍 open，仍在 frontier。票据验收框仍未勾。作者 `RESULTS.md` 写于提交前的 `bb6c0ba3`；冻结对象是其后的 `d9dcc107`，代码差异就是上表两文件。

## 2. 尾注从哪一行来

`conflict_acceptance_host.ts` 的 `createThread` 构造一个对象：`id` 与 `thread` 都是 `attempt.thread_id`，`cli_version` 为 `controlled-conflict-runtime`，`model`/`effort` 来自 `task.card.executor`，并带上 `attempt`。`workers.set` 与 `log("worker-creations", creation)` 用的是这个对象。`sessionFacts` 返回 `{ launch, model: launch.model, effort: launch.effort }`。

`launch_record`（约 626–637 行）只保留 `attempt` 字段等于该 `attempt_id` 的一行；行数不是 1 就抛错。若传入的 attempt 字典已经有 `delivery`，再核对 `launch_id`/`id`、`cli`/`cli_version`、`model`、`effort`，不一致就抛错，不改用 delivery 覆盖 jsonl。`commit_worker` 用这一行的 `cli_version`、`model`、`effort`、`id` 写 Tool/Model/Effort/Launch。`A2A-Native-Session` 仍是 `attempt['thread_id']`。这个宿主里它等于记录的 `id`。`foreign=True` 只把 `A2A-Task` 写成 `foreign-task`。

第一次 worker 提交在 submit 之前。返工提交在第一次 submit 之后，用的仍是 dispatch 当时返回的字典。结束会话一案在新 attempt 的 submit 之前，用 `status()['current_attempt']` 提交。M5 在 `commit_worker` 开头若发现 `delivery` 就抛错，两案仍然 PASS。活动一案还有一次未获准的第三次 `commit_worker`。这些调用用的对象上都没有 delivery，跑到的是 jsonl 分支。作者写的「delivery 出现后与同一行核对」描述的是代码里的分支，不是这两案的运行路径。

submit（`core.ts` 约 3397–3404 行）要求 `sessionFacts` 的 model、effort 都不是 `unknown`，然后把 `facts.launch.id`、`facts.launch.cli_version`、`facts.model`、`facts.effort` 抄进 `attempt.delivery`。这个受控宿主里，delivery 与 jsonl 是同一个对象的两份字段。

独立重跑候选副本后，提交说明与 jsonl、与 delivery 一致：

- 活动会话一案一条记录，attempt `20dacefb-5bf6-4895-8ac8-334f78215696`，id `b9e47083-340d-4999-8ebc-8072d4ea6f0a`。两次 worker 提交（`134d9b3c4d7b7ad3e817a3a9d6284f96b84bd304`、`b901e8ac929df644e20a4933023b29117009470a`）的 Tool/Model/Effort/Launch 都是 `controlled-conflict-runtime`、`gpt-6.1-sol`、`xhigh`、该 id。delivery 的 `launch_id`/`cli`/`model`/`effort` 相同。
- 结束会话一案两条记录。attempt `763cd5c0-5aa4-493e-a871-5e6bf88d0206` 的提交 `ca1addb67d47c6cb5e4f6d1877402f8310e157b4` 使用 id `69c15ece-3a04-4fa2-8967-d00952991a13`；attempt `b4bb63ff-bef7-429e-b2e3-2f8d59e7bc7c` 的提交 `f3d3d2d603f0baef535507cbff0c327def295588` 使用 id `9b7569b1-c642-41ca-ae92-f2f028a0bef4`。两边的 cli/model/effort 相同。delivery 与各自的行一致。

作者 `green-01/fixtures.tar.gz` 里的三行 jsonl，以及读回里的 delivery、`git show` 出的尾注，字段也一一对应。那是作者运行的现场；上面是本审查自己的重跑。尾注不是从 verify 的通过输出反推的：测试在提交时读 jsonl，verify 在其后才比较。

集成仓上那条「Other task integrated independently」只有 `A2A-Task: foreign-task`，不在 worker 范围内。

## 3. 两案红态与绿态

副本用 `git archive` 取出 `workbench` 与 `acceptance`，在 `/tmp` 里 `git init` 并只作本地提交，以便预检的 `git rev-parse HEAD` 能通过。`workbench/node_modules` 符号链接到本工作树。快照和夹具还需要票据、规格和 `fixtures/pagination`，从对应提交 `git archive` 补进副本。这不是项目的 worktree，没有 checkout、reset 或提交到本仓库。预检：Node `v26.5.0`，`/Volumes/WD-Elements` 已挂载，`git diff HEAD -- workbench/src` 为空。`--phase candidate`。`real_codex_turns` 为 0。

基线副本（内容等于 `bb6c0ba3`）：

```
cd /tmp/t086-rev-01/baseline
python3 -B workbench/tests/test_worktree_lifecycle_e2e.py --phase candidate \
  --case test_conflict_active_worker_reworks_and_integrates \
  --case test_conflict_ended_session_gets_new_attempt \
  --output /tmp/t086-rev-01/out/baseline-red-5
```

退出码 1。两案都是 `failures` 1、`errors` 0、`business_red` false，状态 `INCOMPLETE`。错误都是 `trailer_identity_mismatch`。观察到的尾注是 Tool `Codex 0.162.1`、Model `fixture`、Effort `xhigh`，Launch 等于 Native-Session，也就是当时的 `thread_id`。基线宿主不写 `worker-creations.jsonl`；`sessionFacts` 的 `id` 就是 `thread_id`，`cli_version` 是 `controlled-conflict-runtime`，model 来自任务卡。因此 Launch 与 delivery 相同，拒绝来自 Tool 和 Model。

候选副本（内容等于 `d9dcc107`）用同一命令，输出目录 `/tmp/t086-rev-01/out/candidate-green-5`。退出码 0。两案 `failures` 0、`errors` 0，状态 `PASS`。两份 `unittest.txt` 为 `OK`。

作者 `conflict-suite-01/run.json` 七案 `exit_code` 0、`failures` 0、`errors` 0、`target_passed` true，`real_codex_turns` 0，状态 `PASS`。其中包括 `test_conflict_rework_still_rejects_forbidden_path` 与 `test_conflict_rework_still_rejects_foreign_trailer`。源码里这两案仍期望 `path_boundary_failed` 与 `trailer_task_mismatch`。本审查读了这份 `run.json`，没有重跑其余五案。

## 4. 写尾注清单

在 `workbench/tests` 与 `acceptance` 里检索 `A2A-`、`managed_trailers` 和 Tool/Model/Effort/Launch 字面量。证据目录里的历史副本不计入。没有发现作者清单之外的另一套提交尾注写入器。少记的是下面两个继承调用方。

| 位置 | 判定 |
| --- | --- |
| `commit_worker` 与冲突宿主 | 已改。独立重跑：基线红，候选绿 |
| 同文件四个受管用例（`create` 在这四个名字上走 `create_managed`） | 父类 `commit` 在有 `thread_id` 时调用 `managed_trailers`，按 attempt 读 jsonl。作者 `lifecycle-managed/run.json` 状态 PASS，4 案。本审查没有重跑 |
| `test_daemon_gates_e2e.py` 的 `managed_trailers` | 按 attempt 读 `worker-creations.jsonl`。作者 `run.json`：15 项，failures 0，errors 0。本审查没有重跑 |
| `test_task_cards_e2e.py` 的 `commit` | 无 `thread_id` 时写死 `Codex 0.162.1`、`gpt-6-astra`、`xhigh`、`fixture-launch`；有 `thread_id` 时覆盖为 `managed_trailers`。直接 `main` 不启动 daemon。文件相对 `bb6c0ba3` 无差异 |
| `test_t084_trailer_record.py` | 尾注来自 jsonl；错配是故意的。作者 `t084-green-04` 的 stdout 为 `{"status": "PASS", "phase": "green-04"}` |
| `test_multiturn_identity_e2e.py` | `managed_trailers` 取现场 facts 与 launch。作者 `run.json`：4 项，failures 0，errors 0 |
| `test_relay_conflict_e2e.py` | 取 `A2A_TOOL`、最后一条 turn context、launch id。作者 `run.json`：failures 0，errors 0，`real_codex_turns` 0 |
| `test_conflict_trailer_proofs.py` | 钩子写尾注。作者 `run.json`：2 项，failures 0，errors 0，`real_codex_turns` 0 |
| `test_quality_chain_e2e.py` 的 `commit` | 有 thread 时写死 `codex-cli 0.162.1`、`gpt-6.1-sol`、`xhigh`，Launch 用 `self.launch`。作者 controls 8 案、red 11 案的 `outcome` 都是 `passed`，`real_codex_turns` 0。字面量与受控宿主常量相同，测试没有读启动记录。作者已经写明，也没有改这些字面量。票据要求的是确认新规则下仍按原意通过；这份证据支持「通过」，不支持「尾注取自启动记录」 |
| `test_quality_tracer_e2e.py`、`test_quality_widen_e2e.py` | `Tracer` 继承 `QualityCase`，`Widen` 继承 `Tracer`，多处 `self.commit`。文件里没有另一套 `A2A-` 字面量。`test_quality_widen_e2e.py` 里 `cli_version='fixture-only'` 在分数夹具上，不是提交尾注。作者清单未点名，本审查没有单独重跑 |
| `test_hook_environment.py`、`test_hook_turn_facts.py` | 断言钩子输出。作者结果分别为 failures `[]`，以及五案 `business-pass`。无会话文件或当前回合缺上下文时期望 unknown，测的是钩子，不是 worker 夹具反推 |
| `acceptance/test_herdr_traceability_e2e.py` | 假 Herdr，期望钩子尾注。`summary.json`：tests 7，failures 0，errors 0。钩子路径是 `scripts/git-hooks/hook.py`，与 `workbench/hooks/hook.py` 不是同一个文件 |
| `run_t076_real.py`、`run_t076_quality_real.py`、`run_pane_lifecycle.py` | 会复制 auth 或占用真实回合。作者未跑，本审查未跑 |
| `run_t076_red.py` | 期望当前钩子事实套件返回码 1，且前四案 Model/Effort 为 unknown。当前该套件是 PASS / `business-pass`。这是过期的红态脚本，作者未把它算进本票失败。本审查未跑 |
| `test_offline_trace_e2e.py` | 源码中没有 A2A 提交尾注 |

`test_task_cards_e2e.py` 直接入口：作者候选 `task-cards/run.json` 与基线 `task-cards-baseline/run.json` 都是 `tests_run` 14、`failures` 49、`errors` 0、状态 `INCOMPLETE`。两份文件里 `trailer_identity_mismatch` 各 0 次，`daemon_call_failed` 各 148 次，`invalid_task_card` 各 75 次，`connect ENOENT` 各 98 次。基线 stderr 第一例是 `daemon_call_failed` 不等于期望的 `invalid_task_card`，详情为 `connect ENOENT .../state/control.sock`。该文件相对基线无差异。这是直接入口没有 daemon 的既有失败，与本票尾注修改无关。本审查没有重跑这 49 个失败，依据是两份存档和 `git diff`。

## 5. 无 turn context 时的 Effort

`run_worker_delivery.py` 约 207–210 行，在 `verify` 之后断言提交说明里 Model 与 Effort 都是 `unknown`，Tool 为 `codex-cli 0.162.1`，Launch 为 `launch['id']`。约 236–238 行又断言同一会话的 `turn_context` 里 model 为 `gpt-6.1-sol`。作者未改这两处，也没有跑这个脚本。本审查也没有跑。它会复制 `~/.codex/auth.json` 并调用模型。

当前 `workbench/hooks/hook.py` 的 `latest_turn_facts`：没有 `CODEX_HOME`、没有唯一的根会话 jsonl、或最新 `task_started` 之后没有匹配的 `turn_context`，返回 `unknown, unknown`。有上下文时取 `model`，缺则 `unknown`；effort 取 `effort`，否则 `reasoning_effort`，再否则 `unknown`。不完整、没有换行的最后一行直接停，不用它。钩子不读 `A2A_MODEL_REQUESTED` / `A2A_EFFORT_REQUESTED`。`panes.ts` 的 `createPane` 设置的是这两个 `REQUESTED` 变量和 `A2A_TOOL`（必须是 `codex-cli 0.162.1`），不设置 `A2A_MODEL` / `A2A_EFFORT`，也不设置 `CODEX_THREAD_ID`。

`42e2b8ed`（2026-10-11 12:04:17 -0400）之前的钩子把 Model/Effort 写成 `env.get('A2A_MODEL', 'unknown')` 与 `env.get('A2A_EFFORT', 'unknown')`。这两个变量窗格并不设置，所以当时的受管提交会写成 unknown。

门禁只允许 Model 为字面量 `unknown`。Effort 必须等于 `delivery.effort`。submit 在 `facts.effort === "unknown"` 时以 `delivery_facts_unknown` 拒绝，不会留下 effort 为 unknown 的 delivery。因此「尾注 Effort unknown 且 verify 通过」在当前 submit 与当前 `checkTrailers` 下没有路径，除非 delivery.effort 本身是 `unknown`，而 submit 不允许写入那个值。

`evidence/2026-10-10-batch12/T-075/card-3/outside-b-06/delivery/orchestration-events.json` 有 156 条事件，其中 113 条 `native_record`。第一回合的顺序是：`task_started`（事件下标 12，turn `01a1297e-663a-7a01-bc65-cc59a0caa55e`），`turn_context`（下标 19，同一 turn，model `gpt-6.1-sol`，effort `xhigh`），其后才是 `git commit -m` 的已完成工具记录（下标 84），然后 `task_complete`（下标 130）。第二回合同样是 `task_started`、`turn_context`（model/effort 相同）、`task_complete`。该次提交的尾注是 Tool `codex-cli 0.162.1`、Model `unknown`、Effort `unknown`（`candidate-trailers.json`）。会话文件按追加写入；钩子和窗格扫描都把截断当作错误。`git commit` 的完成记录排在 `turn_context` 整行之后，所以提交当时那一行已经换行结束。当时写成 unknown，是因为跑的是旧钩子，不是因为没有上下文。

按当前钩子，那份文件状态会写入 `gpt-6.1-sol` / `xhigh`。窗格扫描对 `task_started` 先把 model/effort 置为 unknown，再采用其后同一 turn 的 `turn_context`。submit 发生在 `task_complete` 之后，会看到这个上下文。三种时序是：

- 提交时 `turn_context` 已是完整行：当前钩子写入真实 model 与 effort。verify 可以通过。`run_worker_delivery.py` 随后因期望 unknown 而失败。
- 提交时还没有可用上下文，submit 时已经有：钩子写下 Effort `unknown`，delivery.effort 为真实值，verify 返回 `trailer_identity_mismatch`。
- 提交和 submit 时都没有：submit 返回 `delivery_facts_unknown`，到不了尾注断言。

已归档的这一回合属于第一种。README 约 334–337 行仍写：当前回合缺上下文时写 unknown，不沿用上一回合或请求值；实际沙箱读取与提交时序还须通过真实回合验收。本审查没有新的真实 Codex 回合。没有用这一次历史文件代替一次当前钩子的现场验收。

## 6. 变异

五份一次性副本都从候选归档复制，只改 `/tmp` 里的 `test_worktree_lifecycle_e2e.py`。`workbench/src/gates/core.ts` 与候选副本逐字节相同。每个变异跑与第 3 节相同的两案，`--phase candidate`，`real_codex_turns` 为 0。副本未提交进本仓库。

| 变异 | 改了什么 | 命令与输出目录 | 结果 |
| --- | --- | --- | --- |
| M1 | 恢复字面量 Tool `Codex 0.162.1`、Model `fixture`、Effort `xhigh`、Launch `attempt['thread_id']`，不读 jsonl | `cd /tmp/t086-rev-01/m1 && python3 -B workbench/tests/test_worktree_lifecycle_e2e.py ... --output /tmp/t086-rev-01/out/m1` | 退出码 1。两案 failures 1。错误 `trailer_identity_mismatch`。尾注即为这些字面量 |
| M2 | `launch_record` 固定取 jsonl 第一行，不按 attempt 过滤 | 同上，目录 `m2`，输出 `out/m2` | 退出码 1。活动会话一案 failures 0。结束会话一案 failures 1，`trailer_identity_mismatch`。该案 Launch 为 `42c2b3ed-9c76-4306-bb9e-3cc422a4a126`，Native-Session 为 `c253b831-b0fe-4cee-b809-31e4b3dda276`。Tool/Model/Effort 仍与记录相同，因为各行的这三项一样。失败的是另一条 attempt 的 launch id |
| M3 | 不读 jsonl。写死 Tool `controlled-conflict-runtime`、Model `gpt-6.1-sol`、Effort `xhigh`、Launch `attempt['thread_id']` | 目录 `m3`，输出 `out/m3` | 退出码 0。两案 failures 0，状态 PASS |
| M4 | 不读 jsonl。Model/Effort 改读 `conflict-card.json` 的 `executor`，Tool 写死 `controlled-conflict-runtime`，Launch 用 `thread_id` | 目录 `m4`，输出 `out/m4` | 退出码 0。两案 failures 0，状态 PASS |
| M5 | 若 attempt 字典已有 `delivery` 则抛错；否则仍按候选方式读 jsonl | 目录 `m5`，输出 `out/m5` | 退出码 0。两案 failures 0，状态 PASS。这两案提交时没有 delivery |

M1 说明旧字面量仍会被拒。M2 说明两行记录时，用错 launch id 会被拒。M3 与 M4 说明完成条件分不出「读了该 attempt 的启动记录」和「写出与这条记录碰巧相同的值」。M5 说明 delivery 核对没有参与这两案的通过。

## 未另行重跑

冲突套件其余五案、daemon、lifecycle-managed、t084、multiturn、relay、trailer-proofs、quality controls/red、钩子两套、Herdr 追踪、任务卡直接入口，都只核对了作者存档，没有在本审查里重跑。质量 tracer/widen 没有存档可核对。真实模型脚本没有运行。T-078 的进程没有动。

审查用的 `/tmp/t086-rev-01` 在写完本文件并回读后删除。
