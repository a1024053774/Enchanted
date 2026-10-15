# T-084 第二轮独立审查

结论：**PASS**

冻结候选 `9ddf446e2609682b819f833f009dc7ad2256d537`。`git rev-parse HEAD` 与 `git rev-parse 9ddf446e` 都是这个值。基线 `fb5dd288721f105d0ca1e8732ca6c6e420aff78a` 是它的祖先（`git merge-base --is-ancestor` 退出码 0）。审查开始时 `git status --porcelain` 为空。本审查没有改产品代码，没有 commit。探针在 `/tmp/t084-review02/`、`/tmp/t084-review02-baseline-src/`、`/tmp/t084-review02-recovery-baseline/`、`/tmp/t084-review02-recovery-candidate/`。没有调用模型 API。

第一轮的发现 1、2 已被本票测试打红。用户第二次决定的 claim-only 路径按码拒收，完全无尾注仍记一次人工介入。基线恢复套件 5/5 失败、候选 4/5 通过可以复现。剩下的那一次失败与尾注规则无关；它和基线不是同一条断言。

没有需要打回的缺陷。

## 1. 改动范围

`git diff --name-status fb5dd288721f105d0ca1e8732ca6c6e420aff78a..9ddf446e -- . ':(exclude)evidence'` 只有下面 9 个文件。证据都在 `evidence/2026-10-15-batch15/T-084/`。中间提交是 `882638b3`、`b4470100`、`9ddf446e`。

| 文件 | 相对基线 |
| --- | --- |
| `workbench/src/gates/core.ts` | `checkTrailers` 增加启动记录比较，以及没有 delivery 时的拒收 |
| `workbench/README.md` | 第 91–93 行与上述行为对齐 |
| `workbench/tests/test_t084_trailer_record.py` | 本票新测试，563 行 |
| `workbench/tests/daemon_acceptance_host.ts` | 受控宿主可在 dispatch 前读 `observed-facts.json` |
| `workbench/tests/test_task_cards_e2e.py` | 快照案的 claim 提交改为无尾注 |
| `workbench/tests/test_worktree_lifecycle_e2e.py` | 三案的 claim 提交改为无尾注 |
| `workbench/tests/test_quality_chain_e2e.py` | 两个红态案改为无尾注 |
| `workbench/tests/test_quality_legacy_e2e.py` | 一个 claim 案改为无尾注 |
| `workbench/tests/test_daemon_recovery_e2e.py` | 见下表。其中进程身份与 `wait` 超出尾注契约本身 |

`verifyCandidate` 的顺序没变：路径、完成条件、质量检查都在尾注之前，尾注在 `core.ts` 1691 行，而且只在前面已经通过时调用。所以仍期望 `path_boundary_failed`、`oracle_failed`、`invalid_trailers`，或 Attempt/Session/Role 的 `trailer_identity_mismatch` 的 claim 用例，会在 1993–1997 行或更早退出，到不了新分支。`test_malformed_and_old_identity_trailers_rejected`（`test_task_cards_e2e.py` 380–402 行）因此不必改。这次没有重跑这些未改用例。

旧测试 diff 里没有删掉完成条件、路径、oracle、审查或集成断言。逐项如下。

| 文件 | 是否只为新契约 | 断言 |
| --- | --- | --- |
| `daemon_acceptance_host.ts` 24–43 行 | 是。文件不存在时，记录的 model/effort 仍抄任务卡。本票在 dispatch 前写入该文件，记录才能和任务卡分开。空字符串或类型不对会抛出，不回退。 | 默认路径与基线相同。 |
| `test_task_cards_e2e.py` | 是。`test_card_validation_versions_and_claim_snapshot` 的第一次 verify 要能通过，claim 又没有 delivery。301–302 行改为 `commit(a, trailers=False)`。同函数后面 316 行的替换认领仍带尾注，期望是 `oracle_failed`；oracle 在尾注之前。 | 快照、`stale_attempt`、`oracle_failed` 的断言都还在。 |
| `test_worktree_lifecycle_e2e.py` | 是。`test_clean_revoke`、`test_verification_name`、`test_completed_verification_cleanup` 都要 verify 通过。三处改为 `trailers=False`。同文件里走 `create_managed()` 的用例没有改。 | 目录、引用、oracle 观察、`passed` 的断言都还在。 |
| `test_quality_chain_e2e.py` | 是。`manual_candidate` 增加 `trailers=True` 参数。`red_review_required`、`red_terminal_prerequisites` 传入 `False`，因为这两案要越过尾注，去看审查请求和集成拒收。其余调用仍用默认尾注：它们在路径、oracle 或质量检查就被拒，尾注还没跑。这是夹具参数，产品没有“无启动记录也放行尾注”的开关。 | `RED-REVIEW`、`RED-FINAL-PREREQUISITES` 的检查原文都还在。 |
| `test_quality_legacy_e2e.py` | 是。`manual_claim_reviewed_score_refused` 要先通过 verify 和审查，再在集成看到 `score_provenance_required`。改为无尾注。 | 44–50 行的 provenance、主分支、`verified` 断言都还在。 |
| `test_daemon_recovery_e2e.py` | 部分是。`verify_fixture` 改为无尾注：第一次 verify 在 oracle 屏障被杀，第二次重启后的 verify 才会跑到尾注；claim 带尾注会被 `trailer_launch_record_missing` 拦住。`integration` 改为 `create_managed()`，提交走 `managed_trailers`（`test_daemon_gates_e2e.py` 88–92 行，从 `worker-creations.jsonl` 取记录）。`start()` 在已有 `integration_score` 时给 `integrate` 加上 `--score-file`。基线上这四个集成案就是在屏障前返回 `score_required`。CAS、reflog、`accepted`、`needs_reconciliation` 的断言没有删。 | 另有一处不是尾注契约所必需：`interrupt()` 把 `daemon.ts` 路径断言改成 `daemon_acceptance_host.ts`，加上 `self.host.pid == pid`，并在 SIGKILL 后 `self.host.wait(timeout=10)`。基线上旧断言已经失败，见第 4 节。新检查仍要求 ps 命令行包含实际宿主、状态目录和 pid 文件。恢复结果断言没有删。 |

`project_map.py status --root .`：Problems 0，Stale living docs 0，退出码 0。T-084 仍在 frontier，状态 open。

## 2. 第一轮发现 1 和 2 已被测试打红

当前实现比的是 `attempt.delivery`，Model 只放行字面量 `unknown`，Effort 不放行。见 `core.ts` 1998–2004 行。delivery 仍只在 `attempt.thread_id` 为真时写入（3397–3404 行），字段是 `launch_id`、`cli`、`model`、`effort`。这次 diff 没有改这段赋值。

完成条件在 `workbench/tests/test_t084_trailer_record.py`。正例从启动记录取值；`model-card` 把 Model 写成任务卡 `gpt-6.1-sol`；`effort-card` 把 Effort 写成任务卡 `xhigh`；`effort-unknown` 把 Effort 写成 `unknown`，记录 effort 仍是 `xhigh`（197–201 行）。`judge`（337–377 行）把拒收码写成字面量 `trailer_identity_mismatch`。宿主在 26–32 行只在存在 `observed-facts.json` 时改记录。

我用候选 `core.ts`，经 `node workbench/src/gates/cli.ts` 和 `daemon_acceptance_host.ts`，跑了绿态 12 案。命令：

```sh
python3 -B /tmp/t084-review02/probe.py
```

宿主 argv 里的 core 是仓库的 `workbench/src/gates/core.ts`。`real` 的 `judge` 状态是 PASS。摘录：

| 案 | verify_ok | verify_error | 人工介入 |
| --- | --- | --- | --- |
| launch、tool、model、effort、model-card、effort-card、effort-unknown | false | `trailer_identity_mismatch` | 0 |
| match、unknown | true | null | 0 |
| none | true | null | 1，标签 `推断：缺尾注` |

变异都在 `/tmp/t084m-*`，仓库 `core.ts` 未改。每个变异再经同一 `cli.ts` 和绿态 `judge`。`diff -u` 确认副本只改了下面这一行。`judge` 状态都是 INCOMPLETE，也就是错误实现被打红。

| 变异 | 副本 | 结果 |
| --- | --- | --- |
| Effort 也放行 `unknown` | `/tmp/t084m-effort-unknown-0pjx6g7e/src/gates/core.ts` | `effort-unknown` 变为 `verify_ok` true。未改核心上此为拒收。match、unknown 仍通过。 |
| Model 改为 `task.card.executor.model` | `/tmp/t084m-model-card-0tj_mjyb/src/gates/core.ts` | `model-card` 变为放行。match 变为 `trailer_identity_mismatch`，因为正例 Model 是记录值 `observed-not-card`。 |
| Effort 改为 `task.card.executor.effort` | `/tmp/t084m-effort-card-anmsslt8/src/gates/core.ts` | `effort-card` 变为放行。match 与 Model `unknown` 正例变为拒收，因为这两案的 Effort 是记录值 `observed-not-xhigh`。 |

发现 1 和发现 2 的错误实现都不能再让本票绿态判定通过。

## 3. 第二次决定与 claim-only

票据 28–29 行记录的用户原话是「尾注这关直接拒收 (Recommended)」。选项要求：没有启动记录就在尾注检查打回；完全无尾注仍按 6a。执行主控指定码 `trailer_launch_record_missing`，事件写明缺启动记录。

实现在 `core.ts` 1999–2008 行：尾注结构完整且 `attempt.delivery` 不存在时，错误为 `trailer_launch_record_missing`，`trailer_check` 带 `reason: 缺启动记录`。有 delivery 时才做四项比较。完全没有 `A2A-` 键时 `missing` 为真，不进这个分支，2010–2018 行仍写一条标签为 `推断：缺尾注` 的 action。README 第 91 行写了同一码和「缺启动记录」。

同一探针里的 claim-only 两案，入口仍是 `cli.ts`。`claim-forged` 只 claim、不 dispatch，四项都是测试常量（Launch `not-this-attempt-launch` 等）。

`/tmp/t084-review02/real/claim-forged/delivery.json`：

```json
{"launch_id": null, "cli": null, "model": null, "effort": null, "runtime_launch": null}
```

`verify.json` 为 `ok` false，`error` 为 `trailer_launch_record_missing`。`events.json` 里该提交的 `trailer_check` 是 `passed` false、`error` 同码、`reason` 为 `缺启动记录`、`missing` false。人工介入 0。主分支未动。

`claim-none`：`verify_ok` true，人工介入 1，用户输入 1，标签 `推断：缺尾注`。事件 `source_ref.label` 同为这个标签。

删掉拒收行的变异（`/tmp/t084m-missing-vuqt9cgp/src/gates/core.ts`，只把 `} else error = "trailer_launch_record_missing";` 换成 `}`）：`claim-forged` 变回 `verify_ok` true、`trailer_error` `[null]`、人工介入 0。`claim-none` 与 `none` 仍是一次 `推断：缺尾注`。`launch` 仍是 `trailer_identity_mismatch`。绿态 `judge` 为 INCOMPLETE。

第二次决定已经落在尾注检查上，并且删掉这行会被本票测试打红。

## 4. 恢复套件

作者的数量可以复现。剩余失败与尾注规则无关。基线打印的不是 `review_launch_config_required`。

基线用 `git archive fb5dd288721f105d0ca1e8732ca6c6e420aff78a` 导出到 `/tmp/t084-review02-baseline-src`，`workbench/node_modules` 符号链接指向本工作树。没有 worktree、checkout 或改共享 `.git`。导出的 `core.ts` 不含 `trailer_launch_record_missing`，也不含 `attempt.delivery.launch_id`。

```sh
cd /tmp/t084-review02-baseline-src
python3 -B workbench/tests/test_daemon_recovery_e2e.py --output /tmp/t084-review02-recovery-baseline
```

退出码 1。`run.json`：status INCOMPLETE，tests_run 5，failures 5，errors 0。墙钟 19.163 秒。四个集成案在 git 屏障前返回 `score_required`，`integrate` 的 argv 没有 `--score-file`。`test_daemon_verify_interruption_and_operation_lock` 失败在基线 `interrupt()` 第 91 行：ps 里是 `daemon_acceptance_host.ts`，断言要的是 `daemon.ts`。输出里没有 `review_launch_config_required`。

候选：

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t084
python3 -B workbench/tests/test_daemon_recovery_e2e.py --output /tmp/t084-review02-recovery-candidate
```

退出码 1。`run.json`：status INCOMPLETE，tests_run 5，failures 1，errors 0。墙钟 30.038 秒。四个集成案通过。失败的仍是 `test_daemon_verify_interruption_and_operation_lock`，断言在当前文件 182 行：第二次 verify 退出码 1。该次回执是 `{"ok":false,"error":"review_launch_config_required",...}`。它前面有一次不带 `--launch-config` 的 `daemon_start`。`cli.ts` 191–192 行在没有这个参数时把配置写成 `{}`。`panes.ts` 120–123 行在 `reviewers` 缺项时返回这个码。`restart()`、`createReview` 和 `daemon_start` 的这段都不在本票 diff 里。

所以：这个测试方法在基线上也失败，失败点是更早的进程名断言。候选把进程名改对并回收僵尸之后，第二次 verify 才走到审查运行时配置。尾注规则没有制造这个码。`RESULTS.md` 里「没有改本工作树里的恢复测试」和 diff 对不上：相对基线，这个测试文件已经改过；剩下的这一案被留在失败状态，没有为了把它改成通过再改断言。

## 5. 兼容分支、开关、被吞掉的异常

产品 diff 只有 `core.ts` 的尾注分支和 README。没有环境变量、没有保留「尾注非空即可」的开关。`else if (attempt.delivery)` 的 else 是拒收，不是退回旧行为。

`...(error === "trailer_launch_record_missing" ? { reason: "缺启动记录" } : {})` 只给这一个码加事件字段。新代码没有 `try/catch`。`verifyCandidate` 1691–1700 行原有的 `Refusal` 处理会把这个拒收记成失败验证并重新抛出，不会把它当成通过。

受控宿主的 `observed-facts.json` 只在测试宿主里。文件缺失时仍抄任务卡。文件坏了就抛出。这不是产品上的第二套尾注规则。

`manual_candidate(..., trailers=True)` 只决定夹具提交写不写尾注。

## 局限

- 没有启动真实 Codex 或 Claude 窗格。Tool、Model、Effort 的生产观察值仍是读 `panes.ts` 的 `launchInfo` / `sessionFacts`，运行证据来自受控宿主。
- 没有重跑任务卡、工作树、质量链、质量遗留、relay、conflict 这些整套。第 1 节对未改用例的判断来自调用顺序和 diff，不是新的运行。
- 恢复套件只重跑了这 5 个测试。作者保存的 `regression-03/cards/run.json` 没有方法名，这次没有用它代替自己的运行。

## 本次命令

```sh
git rev-parse HEAD
git rev-parse 9ddf446e
git merge-base --is-ancestor fb5dd288721f105d0ca1e8732ca6c6e420aff78a HEAD
git diff --name-status fb5dd288721f105d0ca1e8732ca6c6e420aff78a..9ddf446e -- . ':(exclude)evidence'
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
python3 -B /tmp/t084-review02/probe.py
git archive fb5dd288721f105d0ca1e8732ca6c6e420aff78a | tar -x -C /tmp/t084-review02-baseline-src
python3 -B workbench/tests/test_daemon_recovery_e2e.py --output /tmp/t084-review02-recovery-baseline
python3 -B workbench/tests/test_daemon_recovery_e2e.py --output /tmp/t084-review02-recovery-candidate
```

后两条分别在基线导出树和本工作树执行。审查结束时，除本报告外工作树没有别的改动。
