# T-086 独立审查 02

结论：**PASS**

冻结候选 `c9e431aaf59bebb8a237248f249461e21055dd90`。`git rev-parse HEAD` 与 `git rev-parse c9e431aa` 相同。基线 `bb6c0ba352ff7cab1f470d2db055caac36387bab` 是其祖先。第一轮冻结候选 `d9dcc107bd8ef122b83ed0c1226df3022fe37939`。审查时工作树干净。本审查没有改产品代码，没有在本仓库 commit，没有调用模型，没有复制 auth，没有发消息。

第一轮三条都已核对。第 1 条：写死常量、从任务卡抄、用 `thread_id` 作 Launch、取错 attempt 的记录，都会在 verify 上得到 `trailer_identity_mismatch`。第 2 条：tracer 与 widen 已点名并有重跑存档；wide 并发超时的证据支持「基线上即可复现，单跑通过，与本票三份测试文件无关」。第 3 条：按用户原话「只改脚本期望」，新期望与当前钩子、当前门禁在这条脚本的提交时序上一致；脚本未运行。

## 1. 改动范围

`git diff --name-status bb6c0ba3 c9e431aa -- . ':(exclude)evidence'` 只有：

| 文件 | 相对第一轮 `d9dcc107` |
| --- | --- |
| `workbench/tests/conflict_acceptance_host.ts` | 本轮改了启动记录的 id、cli、model、effort，以及 `readThread` 的 `runtime_identity.launch` |
| `workbench/tests/test_worktree_lifecycle_e2e.py` | 第一轮已改；本轮相对 `d9dcc107` 无差异 |
| `workbench/tests/run_worker_delivery.py` | 本轮只改提交尾注期望 |

`git diff bb6c0ba3 c9e431aa -- workbench/src workbench/hooks acceptance scripts/git-hooks` 为空。`workbench/src/gates/core.ts` 与基线逐文件相同。`checkTrailers` 仍是 Launch 对 `delivery.launch_id`、Tool 对 `delivery.cli`、Model 允许字面量 `unknown` 或 `delivery.model`、Effort 对 `delivery.effort`（约 1998–2003 行）。比较没有放宽。

票据允许的写入是 `workbench/tests/`、`acceptance/` 里写尾注的测试夹具，以及本票证据。`acceptance/` 无差异。证据都在 `evidence/2026-10-15-batch15/T-086/`。

写报告前 `project_map.py status --root .` 退出码 0，Problems 0，Stale living docs 0。T-086 仍 open，仍在 frontier。票据验收框仍未勾。

## 2. 第一轮第 1 条

宿主 `createThread`（`conflict_acceptance_host.ts` 约 30–37 行）对每个 attempt 写入 `id` `launch-` 加 `attempt_id`，`cli_version` `conflict-cli-` 加 `attempt_id`，`model` `conflict-model-` 加 `attempt_id`，`effort` `conflict-effort-` 加 `attempt_id`。`thread` 仍是 `attempt.thread_id`。任务卡 executor 仍是 `gpt-6.1-sol` / `xhigh`（生命周期测试约 584 行）。记录里的 cli、model、effort、id 与任务卡、与 `thread_id`、与 `Codex 0.162.1` / `fixture` / `controlled-conflict-runtime` 都不同。

`sessionFacts` 返回这个对象，model 与 effort 取该对象。`readThread` 把 `runtime_identity.launch` 设为 `created.id`，`thread` 与 `native_session` 仍是 thread id。没有创建记录时抛出 `No controlled conflict worker creation`。观察覆盖写在 `runtime_identity` 之后：`return { ...live, turn, runtime_identity, ...overrides }`。结束会话的 `{stopped, running}` 和未知会话的 `{error}` 盖的是顶层字段。门禁 `runtimeIdentity` 要求 `identity.thread === attempt.thread_id`，launch 只要求非空字符串，不要求等于 thread id。submit 要求 `facts.launch.id === attempt.runtime_identity.launch`。两边现在都是 `created.id`。

`commit_worker` 仍按 `attempt_id` 滤 `worker-creations.jsonl`，用该行的 `cli_version`、`model`、`effort`、`id` 写尾注。`A2A-Native-Session` 仍是 `attempt['thread_id']`。

### 本审查的变异

一次性副本在 `/tmp/t086-rev02/`。`git archive c9e431aa` 解出 `workbench`、`acceptance`、`fixtures`、`.project-map` 和快照所需的 T-077 四份文件，在副本里做了本地提交，以便预检的 `git rev-parse HEAD` 能通过。这不是本仓库的提交。`workbench/node_modules` 符号链接到本工作树。`workbench/src` 与工作树 `diff -rq` 无差异，`core.ts` 与基线副本逐字节相同。每个变异只改副本里的 `test_worktree_lifecycle_e2e.py`，再跑两案，`--phase candidate`。`real_codex_turns` 为 0，`stderr` 为空。预检 Node `v26.5.0`，`/Volumes/WD-Elements` 已挂载，`git diff HEAD -- workbench/src` 为空。

| 变异 | 改了什么 | 命令与输出 | 结果 |
| --- | --- | --- | --- |
| M1 | 不读 jsonl。Tool `Codex 0.162.1`，Model `fixture`，Effort `xhigh`，Launch `attempt['thread_id']` | `cd /tmp/t086-rev02/m1 && python3 -B workbench/tests/test_worktree_lifecycle_e2e.py --phase candidate --case test_conflict_active_worker_reworks_and_integrates --case test_conflict_ended_session_gets_new_attempt --output /tmp/t086-rev02/out/m1` | 退出码 1。两案 `failures` 1。verify 错误 `trailer_identity_mismatch`。活动案尾注就是这些字面量，Launch 与 Native-Session 都是 `be87d3e3-5e5a-4a68-a31c-f7f284b1817f` |
| M2 | `launch_record` 固定取 jsonl 第一行，不按 attempt 过滤 | 目录 `m2`，输出 `out/m2` | 退出码 1。活动案 `failures` 0（该案 jsonl 只有一行）。结束会话案 `failures` 1，`trailer_identity_mismatch`。提交 attempt 是 `27965d2d-d0fe-4e2a-a8df-84160131daa4`，Tool/Model/Effort/Launch 属于第一行 attempt `ac69575c-35c4-4c71-808a-08c7fdb1004a`，Launch 为 `launch-ac69575c-35c4-4c71-808a-08c7fdb1004a`。Native-Session 是后一条的 thread `f11cb144-6b6c-4e5b-b93f-8648ee022575` |
| M3 | 不读 jsonl。Tool `controlled-conflict-runtime`，Model/Effort 读 `conflict-card.json` 的 executor，Launch 用 `thread_id` | 目录 `m3`，输出 `out/m3` | 退出码 1。两案 `failures` 1。尾注是 `controlled-conflict-runtime`、`gpt-6.1-sol`、`xhigh`，Launch 等于 Native-Session |
| M4 | 读到该 attempt 的行，Tool/Model/Effort 用该行，Launch 改用 `thread_id` | 目录 `m4`，输出 `out/m4` | 退出码 1。两案 `failures` 1。活动案 Tool/Model/Effort 是 `conflict-cli-6f129555-948a-414a-93ee-9ebd6cb78b62` 等，Launch 与 Native-Session 都是 `ff83f71d-4db7-4a87-a7ab-b275c2fe346e`，不是 `launch-` 加 attempt |
| M5 | `commit_worker` 开头若 `attempt.get('delivery')` 则抛 `delivery present at commit`，否则仍按候选读 jsonl | 目录 `m5`，输出 `out/m5` | 退出码 0。两案 `failures` 0，unittest 末行 `OK`。全文没有 `delivery present` |

M1、M3、M4 在两案的 verify 上都失败。M2 在有两行记录的结束会话案上失败。活动案只有一行时，第一行就是该 attempt 的行，这一案分不出「取第一行」和「按 attempt 过滤」。两案合在一起能把取错 attempt 分开。

M5 与作者的说法一致：这两案走不到 delivery 分支。`commit_worker` 的调用是准备冲突时、submit 之前的 dispatch 字典（约 658 行）；返工和未获准的第三次提交用的仍是同一个字典（约 753、784 行）；结束会话案对 `status()` 取到的新 attempt 先提交文件、再 submit（约 816、834、835 行）。这些对象上没有 `delivery`。`launch_record` 里对照 delivery 的分支描述的是代码，不是这两案的运行路径。本审查没有为了让 M5 失败去造 delivery 路径。

### 宿主语义

冲突宿主只由 `ConflictContracts.setUp` 换上（约 559 行）。本审查在候选副本上重跑了七案，退出码 0，七份 unittest 都是 `OK`，没有 `identity_conflict`，也没有 `No controlled conflict worker creation`。

- 结束会话：目标合同「Confirmed ended worker is replaced by one new attempt」通过，新 attempt `f906de14-4b13-4984-b3c6-6a3a1aa89aad`，fence 2。jsonl 两行的 id 分别是 `launch-` 加各自的 attempt，与 thread id 不同。
- 未知会话：目标合同通过，有一条绑在原 attempt 上的 system issue。
- 未知投递：unittest `OK`。
- 返工仍拒绝禁路径：实际错误 `path_boundary_failed`，`forbidden` 为 `src/private/secret.txt`。
- 返工仍拒绝外来尾注：实际错误 `trailer_task_mismatch`，task 为 `foreign-task`。

七案的 `worker-creations.jsonl` 里，每行的 id、cli、model、effort 都带该 attempt，与 thread id 不同。

## 3. 两案红态、绿态与冲突套件

基线副本是 `git archive bb6c0ba3` 的同一组路径，本地提交 `7a4f315f38d737bba3a3ebe9bc52606efcfc3582`。`--phase baseline` 要求 HEAD 等于 `14b57d22a84bcaebfa91c5051b9909b53a570fac`，所以这次用 `--phase candidate` 跑这棵基线树。`core.ts` 与候选相同。夹具尾注仍是旧字面量。

```
cd /tmp/t086-rev02/baseline
python3 -B workbench/tests/test_worktree_lifecycle_e2e.py --phase candidate \
  --case test_conflict_active_worker_reworks_and_integrates \
  --case test_conflict_ended_session_gets_new_attempt \
  --output /tmp/t086-rev02/out/baseline-red
```

退出码 1。`status` `INCOMPLETE`，`real_codex_turns` 0，`stderr` 为空。两案 `failures` 1、`errors` 0。错误都是 `trailer_identity_mismatch`。活动案提交 `2a5e7efa8d3ab88534c39aa0bc468ede33af0638`，结束会话案提交 `fa9e90c2c236debe81cd0ff491781058771f5a8a`。尾注 Tool `Codex 0.162.1`、Model `fixture`、Effort `xhigh`，Launch 与 Native-Session 相同。基线归档里没有 `worker-creations.jsonl`。`run.json` 的 `target_passed` 为 true，是因为具名目标合同在后来的 verify 断言之前已经记下通过；用例本身是失败。`business_red` 为 false，`red_confirmed` 为 null。红态依据是 verify 的 `trailer_identity_mismatch`。

候选七案：

```
cd /tmp/t086-rev02/candidate
python3 -B workbench/tests/test_worktree_lifecycle_e2e.py --phase candidate \
  --case test_conflict_active_worker_reworks_and_integrates \
  --case test_conflict_ended_session_gets_new_attempt \
  --case test_conflict_unknown_session_preserves_scene_and_reports \
  --case test_conflict_unknown_delivery_does_not_resend \
  --case test_merge_command_error_is_not_text_conflict \
  --case test_conflict_rework_still_rejects_forbidden_path \
  --case test_conflict_rework_still_rejects_foreign_trailer \
  --output /tmp/t086-rev02/out/candidate-suite
```

退出码 0。`status` `PASS`，`real_codex_turns` 0，`stderr` 为空。七案 `failures` 0、`errors` 0、`exit_code` 0、`target_passed` true。副本预检 HEAD 是本地提交 `c09759764779c0c8d0c2de733a3d9c79cf507c8c`，内容来自 `c9e431aa`。跑完后本仓库 `git status --porcelain` 为空，HEAD 仍是 `c9e431aa`。

作者 `rework-red-01`、`rework-green-01`、`rework-conflict-suite` 的 `run.json` 与上述方向一致。本审查以自己的重跑为准。

## 4. 第一轮第 2 条

`test_quality_tracer_e2e.py`、`test_quality_widen_e2e.py`、`test_quality_chain_e2e.py` 相对 `bb6c0ba3` 无差异。widen 导入 tracer，tracer 导入 `QualityCase`。三份文件都不引用 `conflict_acceptance_host.ts`、`test_worktree_lifecycle_e2e.py`、`run_worker_delivery.py`。

作者存档：

| 目录 | `run.json` | 本审查看到的内容 |
| --- | --- | --- |
| `quality-tracer` | PASS，`card_dialect` `legacy`，13 案，`real_codex_turns` 0 | stdout 末行 `TRACER_EXIT:0` |
| `quality-widen-wide` | INCOMPLETE，15 案里 `widen_score_after_cas` 为 `harness_error` | 错误 `HarnessFailure('Expected explicit fixture boundary was not reached: false')`。栈在 `test_quality_widen_e2e.py` 第 274 行调用第 250 行 `wait_for`，再到 `test_quality_tracer_e2e.py` 第 23 行。等待上限是第 17 行的 5 秒。traceback 里没有 `trailer_identity_mismatch` |
| `quality-widen-wide-solo` | PASS，15 案都是 `passed`，含 `widen_score_after_cas` | 单独重跑 |
| `quality-widen-review-red` | PASS，3 案 | |
| `baseline-widen-wide` | PASS，15 案，含 `widen_score_after_cas` | 命令在 `/tmp/t086-baseline-quality`，`--source` 指向该副本 |
| `baseline-widen-wide-loaded` | INCOMPLETE，只有 `widen_score_after_cas` 是同一句 `harness_error` | traceback 路径在 `/private/tmp/t086-baseline-quality/`，行号同样是 274、250、23 |
| `baseline-quality-tracer-loaded` | PASS，13 案 | |

文件时间：`quality-widen-wide` 与 `quality-tracer` 都从 2026-10-15 09:20:00 铺到 09:24:13，widen 有 76 个不同的秒，这 76 秒都落在 tracer 的 81 秒里。基线那一对从 09:39:16 铺到 09:41:03，widen 的 73 个秒都落在 tracer 的秒里。`command.txt` 写明 wide 与 tracer 一起启动。这是同一次并发窗口，不是跑完一个再跑另一个。

因此存档支持：5 秒等待在基线并发时会失败，单独跑在基线和当前候选上都通过，失败栈不经过本票改动的三份文件。本审查没有重跑这对质量套件。

## 5. 第一轮第 3 条

用户 2026-10-15 的原话是「只改脚本期望」（构思主控 `20261015T131159Z-ideation-answer-001`）。`run_worker_delivery.py` 的 diff 只增加从编排事件取 model/effort 的期望，并要求它们等于 `delivery` 的 model 与 effort。钩子、`checkTrailers`、submit 写入 delivery 的代码没有改。本审查没有运行该脚本。它在第 99 行把 `~/.codex/auth.json` 复制进隔离的 `CODEX_HOME`，后面会调用真实模型。未运行。这不是一次真实回合通过。

字段在当前代码里存在：

- `delivery.turn_id`：`workbench/src/contracts/a2aGates.ts` 约 117–119 行，类型里有 `turn_id`。submit 在约 3393 行把 `attempt.turn_id` 设为 `caller.turn`，约 3402 行写入 `delivery.turn_id`。`caller.turn` 是 `panes.ts` `caller()` 里的 `pane.turn`（约 455–464 行）。`pane.turn` 在根会话 `event_msg` / `task_started` 时取 `payload.turn_id`（约 317–318 行）。
- `native_record`：`panes.ts` 约 305 行 `store.event("native_record", { file, offset, record })`。`store.read`（`store.ts` 约 50–52 行）把 `data` 解析成对象。`record` 就是会话 jsonl 的那一行，所以有 `type` 和 `payload`。脚本第 208–211 行用的 `event['type']`、`event['data']['file']`、`event['data']['record']['type']`、`event['data']['record']['payload']['turn_id']` 与这个形状相符。同文件第 187–189 行原本就用同一形状滤 `task_complete`。
- 文件名与 `native_session`：`pane.native` 来自 `session_meta.payload.id`（约 307–309 行）。`pane_status` 返回的 `native_session` 就是 `pane.native`。扫描和钩子都把根会话文件认成以 `native + '.jsonl'` 结尾（`panes.ts` 约 312 行，`hook.py` 约 15 行）。存进事件的 `file` 是相对 `CODEX_HOME` 的路径，后缀仍是这个文件名。脚本的 `endswith(pane['native_session'] + '.jsonl')` 与这条规则相同。

期望与当前钩子、当前门禁的对应关系：

- 钩子 `latest_turn_facts`（`hook.py` 约 10–43 行）：最新一条 `task_started` 之后，取 `turn_id` 相同的最后一条 `turn_context`。model 用 `model`，空则 `unknown`；effort 用 `effort`，否则 `reasoning_effort`，再否则 `unknown`。钩子不读 `A2A_MODEL_REQUESTED` / `A2A_EFFORT_REQUESTED`。
- 真实窗格的 `sessionFacts`（`panes.ts` 约 340–342、85–90 行）返回启动记录，以及扫描写入的 `pane.model` / `pane.effort`。根文件里 `turn_context.turn_id === pane.turn` 时，model 取 `payload.model`，effort 取 `payload.effort`，否则 `reasoning_effort`（约 313–316 行）。submit 把 `facts.launch.id`、`facts.launch.cli_version`、`facts.model`、`facts.effort` 抄进 delivery，并且在 model 或 effort 为 `unknown` 时以 `delivery_facts_unknown` 拒绝（约 3397–3404 行）。
- 脚本取 `delivery.turn_id` 对应的最后一条 `turn_context`，用与钩子相同的 `or` 链取出 model 与 effort，要求二者都不是 `unknown`，并且等于 `delivery.model` 与 `delivery.effort`。尾注 Model/Effort 用这两个值。
- Tool 仍期望 `codex-cli 0.162.1`。`createPane` 把 `A2A_TOOL` 设为 `codex --version` 的输出，并且只接受这个版本字符串（约 147、169 行）。启动记录的 `cli_version` 就是该字符串。钩子把 `A2A_TOOL` 写入 Tool。delivery.cli 是 `facts.launch.cli_version`。门禁要求 Tool 等于 delivery.cli。
- Launch 仍期望 `launch_show` 返回的记录 `id`。这个 id 就是 `A2A_LAUNCH`，钩子把它写入 Launch。delivery.launch_id 是 `facts.launch.id`。

这条脚本的时序是：工作回合里 commit，Stop 时 submit，然后才有回执回合。commit 当时最新的 `task_started` 就是后来写入 `delivery.turn_id` 的那一回。回执回合的 `turn_id` 不同，滤不进来。在非空的 model、effort 上，钩子、窗格和脚本取的是同一组字段。门禁再拿尾注跟这份 delivery 比。Model 的字面量 `unknown` 仍是门禁允许的特例；脚本现在要求观察到的 model 不是 `unknown`，与「有回合上下文时钩子写入观察到的值」一致，也与用户「不放宽尾注必须与启动记录一致」一致。

空字符串是既有差别：钩子的 `or` 把空串当成缺值，窗格的 `??` 会留下空串。本票没有改这两处。脚本要求的是非空 model 与 effort；同文件约 247–249 行还要求各条 `turn_context` 的 model 为 `gpt-6.1-sol`。

## 6. 证据体积

`evidence/2026-10-15-batch15/T-086`：`du -sh` 为 120M，`du -sk` 为 122884，普通文件 10062 个。没有单文件大于 5 MB。最大的是 `daemon-gates/run.json`，2933342 字节。

## 未另行重跑

质量 tracer/widen 的并发与单跑、review-red，只核对了作者 `run.json`、traceback、stdout 和文件时间。`run_worker_delivery.py` 以及会复制 auth 或调用真实模型的 `run_t076_real.py`、`run_t076_quality_real.py`、`run_pane_lifecycle.py`、`run_t076_red.py` 都没有运行。第一轮已经归档的 daemon、lifecycle-managed、任务卡直接入口、钩子两套、Herdr 追踪、t084、multiturn、relay、trailer-proofs，本轮没有重跑；那些文件相对本轮候选没有新的产品差异。审查用的 `/tmp/t086-rev02` 与本次夹具目录在报告落盘后删除。
