# T-084 独立审查

结论：**NO_GO**（角色卡要求的「需修复」）

冻结候选 `882638b3acc5c5f8cbac6055badc51b09f92a864`（`git rev-parse HEAD` 与 `git rev-parse 882638b3` 相同）。基线 `fb5dd288721f105d0ca1e8732ca6c6e420aff78a` 是其祖先。审查时工作树干净。本审查没有改产品代码，没有 commit。

需修复的是本票测试的完成条件，不是 `checkTrailers` 里那四行比较。受管 submit（`dispatch` 之后、`attempt.delivery` 已写入）上，当前实现与用户决定一致，下面有独立重跑。完成条件不够格的两点：

1. 把 Effort 也放行字面量 `unknown` 之后，本票绿态套件仍然 PASS。当前实现会拒。
2. 把 Model 比较从 `attempt.delivery.model` 改成 `task.card.executor.model` 之后，本票绿态套件仍然 PASS。当前实现比的是 delivery。本票宿主把记录里的 model/effort 抄成任务卡，所以套件看不出这个差别。

无 delivery 的 claim 路径另记在发现 3。那里尾注核对会放行伪造的 Launch/Tool/Model/Effort；集成被既有的 `score_provenance_required` 拦住，夹具主分支没有动。这一项只列事实，不代替用户决定要不要收紧。

## 1. 改动范围

`git diff --name-only fb5dd288…882638b3` 分类计数：`evidence/2026-10-15-batch15/T-084/` 下 212 个文件，另有 3 个文件，范围外 0 个。

| 文件 | 改动 |
| --- | --- |
| `workbench/src/gates/core.ts` | `checkTrailers` 增加 4 行比较和 1 行注释（约 1998–2002 行） |
| `workbench/README.md` | 第 91 行尾注句与上述行为对齐 |
| `workbench/tests/test_t084_trailer_record.py` | 本票新测试，349 行 |
| `evidence/2026-10-15-batch15/T-084/**` | 本票红态、绿态、变异证据 |

没有类型定义改动，没有其他源码。审查开始和写报告前各跑了一次 `project_map.py status --root .`：Problems 0，Stale living docs 0，退出码 0。T-084 仍 open，仍在 frontier。

## 2. 有 delivery 时的比较

用户原话（票据第 29 行）：Launch 必须等于本 attempt 的启动记录号，Tool/Model/Effort 必须与那条记录一致，spec 允许 Model 写 unknown 的情形保留，不一致就打回。拒收码沿用 `trailer_identity_mismatch`。完全无尾注仍记一次人工介入。

`workbench/src/gates/core.ts` 1999–2002 行，在 Attempt/Session/Role 已核对之后：

```1999:2002:workbench/src/gates/core.ts
        else if (attempt.delivery && trailers.launch![0] !== attempt.delivery.launch_id) error = "trailer_identity_mismatch";
        else if (attempt.delivery && trailers.tool![0] !== attempt.delivery.cli) error = "trailer_identity_mismatch";
        else if (attempt.delivery && trailers.model![0] !== "unknown" && trailers.model![0] !== attempt.delivery.model) error = "trailer_identity_mismatch";
        else if (attempt.delivery && trailers.effort![0] !== attempt.delivery.effort) error = "trailer_identity_mismatch";
```

- Launch 对 `delivery.launch_id`，Tool 对 `delivery.cli`，Model 对 `delivery.model`，Effort 对 `delivery.effort`。
- Model 先放行字面量 `unknown`，再与记录比较。Effort 没有这条例外。
- 四行都用现有码 `trailer_identity_mismatch`。
- 完全没有 `A2A-` 尾注时不进上述比较。2007–2015 行仍写一条来源为「推断：缺尾注」的 action 用户输入。

同一入口重跑（输出在 `/tmp`，未写入证据目录）：

```sh
python3 -B workbench/tests/test_t084_trailer_record.py --phase green --output /tmp/t084-review-green
```

退出码 0，标准输出 `{"status": "PASS", "phase": "green"}`，墙钟 10.13 秒。`/tmp/t084-review-green/summary.json` 的 `core` 是本仓库 `workbench/src/gates/core.ts`。七个案：

| 案 | verify_ok | verify_error | trailer_error | 人工介入 | 主分支未动 |
| --- | --- | --- | --- | --- | --- |
| launch / tool / model / effort | false | `trailer_identity_mismatch` | 同码 | 0 | true |
| match / unknown | true | null | null | 0 | true |
| none | true | null | null | 1，标签 `推断：缺尾注` | true |

基线核心（`git show fb5dd288721f105d0ca1e8732ca6c6e420aff78a:workbench/src/gates/core.ts` 写入 `/tmp` 副本，经同一 `run_cases(..., phase=red)`）上，四种不符的 `verify_ok` 都是 true，`trailer_error` 为 null，人工介入 0。none 仍是 1 条 `推断：缺尾注`。这与「修复前放行」一致。该次汇总状态字是测试脚本对红态的 `PASS`，意思是旧行为仍放行，不是候选通过。

Effort 字面量 `unknown`、其余三项等于记录：真实入口 `verify_ok` false，`verify_error` 与 `trailer_error` 都是 `trailer_identity_mismatch`，delivery.effort 为 `xhigh`。见 `/tmp/t084-review-probe/report.json` 的 `effort_unknown_real_core`。

期望值在测试里写成常量，不读门禁的通过输出。伪造值是 `test_t084_trailer_record.py` 30–35 行的 `FORGED`。正例由 `trailers_for`（110–118 行）取 `worker-creations.jsonl` 里该 attempt 的 `id` / `cli_version` / `model` / `effort`。`judge`（276–303 行）把拒收码写成字面量 `trailer_identity_mismatch`。submit 之后、verify 之前，脚本要求 `attempt.delivery` 与这条记录一致，否则以 GAP 退出，不把尾注或门禁结论当成期望值。

入口是 `node workbench/src/gates/cli.ts`。`Gate.__call__`（测试 64–74 行）和作者保存的 `evidence/2026-10-15-batch15/T-084/green/commands.jsonl` 第一条 argv 都是这个文件。本次重跑没有调用模型 API。

## 3. 比较对象是 submit 时写入的 delivery

`checkTrailers` 只读 `attempt.delivery` 的四个字段，不读任务卡，不读尾注自己，也不在验收时重查 `launch_records`。

delivery 只在 submit 成功路径写入，全文件一处赋值（`core.ts` 3394–3401 行）：`attempt.thread_id` 为真时调用 `runtime.sessionFacts`，拒绝 model 或 effort 为 `unknown`（码 `delivery_facts_unknown`），然后

- `launch_id` = `facts.launch.id`，且必须等于 `attempt.runtime_identity.launch`
- `cli` = `facts.launch.cli_version`
- `model` = `facts.model`
- `effort` = `facts.effort`

`claim` 把 `thread_id` 设成空字符串（1348 行）。空字符串在这个 `if` 里为假，所以只 claim 再 submit 不会写 delivery。

生产窗格的 `sessionFacts`（`panes.ts` 340–342 行）返回 `launchInfo`：启动记录对象，加上 pane 上扫到的 model/effort（85–92、314–315 行）。持久化记录上的配置字段是 `model_requested` / `effort_requested`（153、181 行），来自任务卡，并写入启动 argv。delivery 抄的是观察到的 `facts.model` / `facts.effort`，不是这两个 requested 字段。Tool 来自记录上的 `cli_version`，创建窗格时等于 `codex --version`，同时放进 `A2A_TOOL`（146–169 行）。本次审查没有启动真实 CLI 窗格，这条生产路径是读代码，不是运行证据。

本票跑的宿主是 `workbench/tests/daemon_acceptance_host.ts`。它在 `createThread` 时把 `model` / `effort` 设成 `task.card.executor.model` / `effort`（30 行），`cli_version` 固定为 `controlled-runtime fixture`。`sessionFacts`（44–47 行）原样返回这条记录。测试 209 行还要求记录的 model/effort 等于任务卡常量，否则 GAP。因此作者套件里，Model/Effort 的记录值与任务卡相同；Tool 不同（记录是 `controlled-runtime fixture`，任务卡 `executor.cli` 是 `Codex`）。

作者写的这个限制成立，而且会让「Model 改去比任务卡」的错误实现通过套件。见发现 2。当前 `core.ts` 在记录与任务卡被拆开时比的是记录：我只改了 `/tmp` 里的宿主副本，让记录 model 变成 `observed-not-card`，任务卡仍是 `gpt-6.1-sol`，核心仍是候选的 `core.ts`。`/tmp/t084-review-probe/report.json` 的 `model_card_versus_record`：

| 尾注 Model | delivery.model | verify |
| --- | --- | --- |
| `gpt-6.1-sol`（任务卡） | `observed-not-card` | 拒，`trailer_identity_mismatch` |
| `observed-not-card`（记录） | `observed-not-card` | 过，`task_state` 为 `reviewing` |

Launch 与 Tool 在作者套件里已经和任务卡分开：正例 Tool 是 `controlled-runtime fixture`，Launch 是宿主生成的记录号。match 能通过，说明这两项对上的是 delivery / 记录，对不上任务卡上的 `Codex`。

delivery 是 submit 当时的快照。verify 不再读一次启动记录。提交之后观察值若再变，尾注核对仍用这份快照。

## 4. 没有 delivery 时只要求非空

会走到 `attempt.delivery &&` 短路的真实提交，是 `thread_id` 为空的 submit。`claim` 走这条（1348、1412、3394 行）。`dispatch` 会建线程并在成功 submit 时写入 delivery。submit 的重放在写 delivery 之前返回（3392 行），不会把已有 delivery 清掉。全文件没有第二处 `attempt.delivery =`。

我用候选 `core.ts` 和原宿主，经 `cli.ts` 做了一次只 claim、不 dispatch 的提交。尾注四项都是测试里的伪造常量（Launch `not-this-attempt-launch` 等）。`/tmp/t084-review-probe/report.json` 的 `claim_forged`：

- submit `ok` true，`thread_id` 为 `""`，`delivery_present` false
- verify `ok` true，`trailer_passed` `[true]`，`trailer_error` `[null]`，人工介入 0
- 审查驱动 `complete_review` 完成后 `task_state` 为 `verified`
- integrate `ok` false，错误 `score_provenance_required`（`core.ts` 3446 行，本票 diff 没有动这行）
- 夹具主分支 `main_moved` false（仍是 `ff66392abc7f733c5d189624ef7337cc41174efe`）

所以：尾注核对和独立审查都会放行这四项伪造值；集成没有发生，拦住它的是「没有 delivery」，码不是 `trailer_identity_mismatch`。历史 claim 套件里，真正调用 integrate 的用例走 `create_managed()` → `dispatch`（`workbench/tests/test_task_cards_e2e.py` 103–109、151–169 行），那种 attempt 有 delivery。只 `create()` / `claim` 的用例停在别的拒收上，没有一条在无 delivery 时集成成功。

票据正文还写了：门禁拿不到 Tool/Model/Effort 的记录值时，先报告缺口并停下，不从尾注或其他提交推断。运行时的这条分支没有停，也没有报缺口；它退回「九项里这四项非空即可」（1994–1995 行的原检查）。README 第 91 行把这个退回写明了。用户决定原文没有单列「没有启动记录的 attempt」。这里不判断该收紧、该拒绝，还是维持非空。

## 5. 测试、期望值与变异

测试经 `cli.ts`，期望值来源见第 2 节。我重跑了绿态，并在基线核心上重跑了红态形状。没有调用模型。

变异都在 `/tmp` 副本里，仓库 `core.ts` 未改。每个变异都再经 `cli.ts` 和本票测试的 `judge`。

| 变异 | 改了什么 | 命令 / 结果 |
| --- | --- | --- |
| 删掉 Launch 比较 | `mutant_core("launch")` 去掉 1999 行那句 | `run_cases("mutant-launch", …, ["launch"])`。`/tmp/t084-review-probe/report.json`：`status` PASS，即伪造 Launch 变为 `verify_ok` true、`trailer_passed` [true]。删行前绿态此为拒收。 |
| Effort 也允许 `unknown` | 2002 行改成与 Model 相同的 `!== "unknown"` 短路 | 对本票全部七个案跑 `judge` 的 green 规则。套件 `status` PASS。错误实现没有被套件打红。同一伪造 Effort `unknown` 在未改的核心上被拒，见第 2 节。 |
| Model 改比任务卡 | `attempt.delivery.model` 换成 `task.card.executor.model` | 同样七个案，套件 `status` PASS。错误实现没有被套件打红。第 3 节的宿主拆开实验说明未改的核心会拒任务卡值、接受记录值。 |

作者证据里的另外三次删行（Tool、Model、Effort）我读了 `evidence/2026-10-15-batch15/T-084/summary.json` 和 `mutant-patches/model.patch`，没有重跑。model 补丁显示比较句被删掉后，下一行 Effort 比较还在，只是多了一段行首空白；作者汇总写的是：被删的那一项放行，其余三项仍为 `trailer_identity_mismatch`。这个补丁形状和测试 38–42 行的针文本（不含行首空白）对得上。我独立重跑的只有 Launch 删行。

## 发现

1. **需修复，P2。** `workbench/tests/test_t084_trailer_record.py` 的绿态没有 Effort 为 `unknown` 的拒收案。把 2002 行改成也放行 `unknown` 后，套件仍 PASS（`/tmp/t084-review-probe/report.json` 的 `mutant_effort_unknown_exemption_suite`）。用户决定只保留 Model 的 unknown。当前实现会拒，见同文件 `effort_unknown_real_core`。缺的是一条经 `cli.ts` 的用例：记录 effort 为 `xhigh`，尾注 Effort 为 `unknown`，其余三项等于记录，期望 `trailer_identity_mismatch`。

2. **需修复，P2。** 同一套件不能拒绝「Model 与任务卡比较」。宿主 30 行把 model/effort 抄入记录，测试 209 行又要求二者等于任务卡，记录与任务卡在 Model/Effort 上被绑死。把比较改成 `task.card.executor.model` 后套件仍 PASS（`mutant_compare_model_to_card_suite`）。Tool、Launch 不受这个绑定（记录 cli 不是 `Codex`，Launch 不在任务卡上）。当前核心在拆开的宿主上会拒任务卡 Model、接受记录 Model（发现节前面的表）。缺的是宿主能给出与任务卡不同的 model/effort，并且正例取记录值、反例取任务卡值。

3. **P2，事实，不代设计决定。** 无 `attempt.delivery` 时，1999–2002 行不比较。只 claim 的 submit 会走到这里：伪造四项可以通过尾注核对和审查，状态可以到 `verified`，integrate 返回 `score_provenance_required`，主分支不动。证据见第 4 节。这与「不一致就打回」在尾注这一关上的字面不同；集成这一关没有放行。票据里「拿不到记录就停下」在运行时没有发生。

未发现范围外的源码改动，也未发现受管 submit 把四项与尾注自身或任务卡比较的实现。生产 `panes.ts` 的观察值路径没有在真实窗格里跑过。

## 局限

- 没有启动真实 Codex / Claude 窗格，没有调用模型 API。
- Tool/Model/Effort 的生产来源（`panes.ts` 的 `launchInfo` / 原生日志）是代码阅读。运行证据里的 sessionFacts 来自受控宿主。
- 作者的 Tool、Model、Effort 三次删行变异没有重跑，只核对了补丁和已保存汇总；Launch 删行已重跑。
- 红态重跑用的是基线 `core.ts` 的 `/tmp` 副本加上候选里的测试脚本，不是把工作树 checkout 回基线。

## 本次命令

```sh
python3 -B workbench/tests/test_t084_trailer_record.py --phase green --output /tmp/t084-review-green
python3 -B /tmp/t084-review-probe.py
```

红态是另一次进程：把基线 `core.ts` 写入 `/tmp` 副本后调用 `run_cases("red", 该副本, /tmp/t084-review-red/red, …)`。标准输出七行均为基线放行（none 的人工介入为 1）。探针报告：`/tmp/t084-review-probe/report.json`。
