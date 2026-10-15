# T-084 尾注与启动记录核对

状态：尾注契约 PASS。基线 `fb5dd288` 上同一个恢复套件已经失败，这是既有问题，与本票无关，见返工审阅。工作树 `exec/t084`，基线 `fb5dd288721f105d0ca1e8732ca6c6e420aff78a`。本会话没有 commit、没有 push。ticket 仍 open。

门禁在受管 submit 之后，把本 attempt 的启动记录放在 `attempt.delivery` 上。核对用的就是这份值，不从尾注或其他提交反推。

| 尾注 | delivery 字段 | 启动记录字段 |
| --- | --- | --- |
| Launch | `launch_id` | `id`（同时等于 `runtime_identity.launch`） |
| Tool | `cli` | `cli_version` |
| Model | `model` | `model` |
| Effort | `effort` | `effort` |

真实窗格里，Tool 来自 `A2A_TOOL`，写入时等于 `cli_version`。Model、Effort 在提交时取 `sessionFacts` 的观察值（`panes.ts` 的 `launchInfo`）。钩子允许 Model、Effort 在读不到回合时写成 `unknown`；submit 拒绝观察值为 `unknown` 的交付（`delivery_facts_unknown`）。用户决定只保留尾注 Model 为字面量 `unknown` 的例外，Effort 不在此列。

本票跑的是受控宿主 `workbench/tests/daemon_acceptance_host.ts`。它在 dispatch 时把记录追加到 `worker-creations.jsonl`，`sessionFacts` 返回同一对象。记录里的 `cli_version` 固定为 `controlled-runtime fixture`，`model` / `effort` 抄任务卡（`gpt-6.1-sol` / `xhigh`）。每个案在 verify 之前先要求 delivery 与这条记录一致，不一致则以缺口退出。本次没有出现缺口。

没有 `attempt.delivery` 的 attempt（只 claim、未走受管 submit）拿不到这四项记录。带 A2A 尾注时，尾注检查直接拒收，码 `trailer_launch_record_missing`，`trailer_check` 事件的原因是缺启动记录。完全无尾注仍记一次「推断：缺尾注」。返工 #2 改的是这里。第一轮曾经只要求这四项非空。

伪造常量写在测试里，不从门禁输出读取：Launch `not-this-attempt-launch`，Tool `not-the-recorded-cli`，Model `not-the-recorded-model`，Effort `not-the-recorded-effort`。正例的四项从该案的 `launch-record.json` 取值。Model unknown 正例只把 Model 写成 `unknown`，其余三项仍等于记录。

入口是 `node workbench/src/gates/cli.ts`，经上述宿主连隔离的 `/tmp` 状态目录。没有调用真实模型 API。夹具仓库在 `/tmp` 下，不在证据目录里。

## 红态

在加入四行比较之前跑的。被放行的原始输出在 `red/`。汇总：`red/summary.json`，状态 PASS。宿主参数：`red/host-argv.json`（core 为工作树的 `workbench/src/gates/core.ts`，状态目录 `/tmp/t084-9c6ejtnw`）。

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t084
python3 -B workbench/tests/test_t084_trailer_record.py --phase red --output evidence/2026-10-15-batch15/T-084
```

四种不符的 verify 均为 ok，`trailer_check.passed` 为 true，error 为空，人工介入 0。与记录一致的正例和 Model `unknown` 同样通过。完全无尾注：`red/none/events.json` 里 `human_intervention` 为 1 条，通道 `commit-trailer`，标签 `推断：缺尾注`；汇总里 `user_inputs` 为 1。

## 修复

`workbench/src/gates/core.ts` 的 `checkTrailers` 在原有 Attempt/Session/Role 比较之后增加四行，拒收码仍是 `trailer_identity_mismatch`。Model 先放行字面量 `unknown`，再与 `delivery.model` 比较。`workbench/README.md` 原句只写了 Task、Attempt、Session、Role 四项；`project_map.py status` 因此把该 living doc 标为 stale。已改成与现在的核对一致，没有改地图。

## 绿态

同一入口，对照已含上述四行的 core。进程退出码 0，标准输出 `{"status": "PASS", "phase": "green"}`，墙钟 13.19 秒。汇总另存于 `green/summary.json`（顶层 `summary.json` 后来被变异阶段覆盖）。宿主参数：`green/host-argv.json`，状态目录 `/tmp/t084-713w20a6`。命令日志：`green/commands.jsonl`。

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t084
python3 -B workbench/tests/test_t084_trailer_record.py --phase green --output evidence/2026-10-15-batch15/T-084
```

| 案 | verify | 错误 | trailer_check | 人工介入 | 主分支 |
| --- | --- | --- | --- | --- | --- |
| launch | 拒 | `trailer_identity_mismatch` | passed false，error 同码 | 0 | 未动 |
| tool | 拒 | `trailer_identity_mismatch` | passed false，error 同码 | 0 | 未动 |
| model | 拒 | `trailer_identity_mismatch` | passed false，error 同码 | 0 | 未动 |
| effort | 拒 | `trailer_identity_mismatch` | passed false，error 同码 | 0 | 未动 |
| match | 过 | 无 | passed true | 0 | 未动 |
| unknown | 过 | 无 | passed true | 0 | 未动 |
| none | 过 | 无 | passed true | 1，标签 `推断：缺尾注` | 未动 |

Launch 案的 CLI 原始回执在 `green/launch/verify.json`：`ok` false，error `trailer_identity_mismatch`，尾注 Launch 为 `not-this-attempt-launch`，记录号 `160ff51d-6e00-42fd-a540-73c60fe0413e`。Tool / Model / Effort 三案的尾注只有对应一项是伪造值，另外三项等于该案记录。match 的四项等于记录 `f3115110-db5f-4880-8078-d2e8ac7427a5`（Tool 为 `controlled-runtime fixture`，不是任务卡上的 Codex）。unknown 的 Model 为 `unknown`，记录上的 model 仍是 `gpt-6.1-sol`。none 的提交说明没有 `A2A-` 行；`green/none/events.json` 中 `human_intervention` 为 1，标签 `推断：缺尾注`。

各案的 `verify.json`、`events.json`、`launch-record.json`、`delivery.json`、`commit-message.txt` 在 `green/<案>/`。

## 变异

一次性副本：把 `workbench/src` 拷到 `/tmp/t084m-*`，只删一行比较，`node_modules` 指向工作树的 `workbench/node_modules`，宿主改加载该副本的 `core.ts`。进程退出码 0，标准输出 `{"status": "PASS", "phase": "mutants"}`，墙钟 30.74 秒。汇总在顶层 `summary.json`。四个案的原始输出在 `launch/`、`tool/`、`model/`、`effort/`。删行后的 diff 在 `mutant-patches/`。副本已从 `/tmp` 删除。

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t084
python3 -B workbench/tests/test_t084_trailer_record.py --phase mutants --output evidence/2026-10-15-batch15/T-084
```

针文本不含行首空白，删行后下一行多了一段缩进，比较语句本身不在。行为上只有被删的那一项变为放行，其余三项仍是 `trailer_identity_mismatch`。

| 删掉的比较 | 放行 | 仍拒 |
| --- | --- | --- |
| Launch | launch | tool、model、effort |
| Tool | tool | launch、model、effort |
| Model | model | launch、tool、effort |
| Effort | effort | launch、tool、model |

## 未覆盖

- 受控宿主的 model、effort 与任务卡相同。伪造值与记录不同，所以拒收成立；这项不能单独证明比较对象不是任务卡。Tool 可以：正例用的是记录里的 `controlled-runtime fixture`，任务卡写的是 Codex。
- 没有 delivery 的 claim 路径没有重跑。
- 没有启动真实 CLI 窗格，没有调用模型。
- 本机 `workbench/node_modules/node-pty/prebuilds/darwin-arm64/spawn-helper` 原为 644，按 README 的既有做法改为 755 后宿主才能启动。该文件在 gitignore 里，产品代码没有改权限。

只读复核读了已保存的 CLI 输出、启动记录和 delivery，没有重跑套件，结论 PASS。局限与上列相同。

## 地图

在工作树执行：

```sh
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

README 更新后：Problems 0，Stale living docs 0，退出码 0。T-084 仍在 frontier，状态 open。

## 返工 #1

独立审查 `independent-review-01.md` 结论 NO_GO。要修的是测试完成条件。`workbench/src/gates/core.ts` 的四行比较没有改，工作树相对 `b4470100` 的 diff 里没有这个文件。

受控宿主增加 `observed-facts.json`。文件不存在时，记录的 model/effort 仍抄任务卡。本票在每次 dispatch 前写入该文件。任务卡保持 `gpt-6.1-sol` / `xhigh`。除 `effort-unknown` 外，记录 model 为 `observed-not-card`，effort 为 `observed-not-xhigh`。`effort-unknown` 的记录 effort 是 `xhigh`，model 仍是 `observed-not-card`。

### 绿态 green-02

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t084
python3 -B workbench/tests/test_t084_trailer_record.py --phase green-02 --output evidence/2026-10-15-batch15/T-084
```

退出码 0，标准输出 `{"status": "PASS", "phase": "green-02"}`，墙钟 19.60 秒。汇总在 `green-02/summary.json`。旧的 `red/`、`green/`、`summary.json` 没有覆盖。

| 案 | 尾注相对记录 | verify |
| --- | --- | --- |
| launch / tool / model / effort | 对应一项为伪造常量 | 拒，`trailer_identity_mismatch` |
| model-card | Model 为任务卡 `gpt-6.1-sol`，其余等于记录 | 拒，`trailer_identity_mismatch` |
| effort-card | Effort 为任务卡 `xhigh`，其余等于记录 | 拒，`trailer_identity_mismatch` |
| effort-unknown | Effort 为 `unknown`，记录 effort 为 `xhigh`，其余等于记录 | 拒，`trailer_identity_mismatch` |
| match | 四项等于记录（model `observed-not-card`，effort `observed-not-xhigh`） | 过 |
| unknown | Model 为 `unknown`，其余等于记录 | 过 |
| none | 无尾注 | 过，人工介入 1，标签 `推断：缺尾注` |

`effort-unknown` 的提交说明在 `green-02/effort-unknown/commit-message.txt`：Effort 为 `unknown`，Model 为 `observed-not-card`，记录 effort 为 `xhigh`。`model-card` 的 Model 是 `gpt-6.1-sol`，记录 model 是 `observed-not-card`。`effort-card` 的 Effort 是 `xhigh`，记录 effort 是 `observed-not-xhigh`。

### 变异 mutants-02

```sh
python3 -B workbench/tests/test_t084_trailer_record.py --phase mutants-02 --output evidence/2026-10-15-batch15/T-084
```

退出码 0，标准输出 `{"status": "DETECTED", "phase": "mutants-02"}`，墙钟 41.09 秒。`DETECTED` 表示绿态判定不再 PASS：被改的那一案从拒收变成放行。汇总在 `mutants-02/summary.json`。补丁在 `mutants-02/patches/`。副本已从 `/tmp` 删除。

| 变异 | 绿态判定 | 变成放行 | 仍拒 |
| --- | --- | --- | --- |
| Effort 比较也放行字面量 `unknown` | INCOMPLETE | effort-unknown | 其余拒收案，含 model-card、effort-card |
| Model 比较改为 `task.card.executor.model` | INCOMPLETE | model-card | 其余拒收案；match 改为拒收，因为尾注 Model 是记录值 |
| Effort 比较改为 `task.card.executor.effort` | INCOMPLETE | effort-card | 其余拒收案；match 与 Model `unknown` 正例改为拒收，因为这两案的 Effort 是记录值 `observed-not-xhigh` |

三条变异都仍放行完全无尾注，人工介入 1 条，标签 `推断：缺尾注`。

曾把 Model 与 Effort 两行同时改成任务卡字段，单字段反例仍被另一行拒收，没有单独留下那次输出。上面两行是分开改的。

### 发现 3，本轮未改

只 claim、没有 `attempt.delivery` 的分支没有改，也没有重跑。审查第 4 节的记录仍然是：伪造的 Launch/Tool/Model/Effort 可以通过尾注核对和审查，任务状态可以到 `verified`；`integrate` 返回 `score_provenance_required`，夹具主分支没有动。审查把这项交给用户决定。本轮不收紧、不放宽。

### 地图（返工后）

同一条 `project_map.py status --root .`：Problems 0，Stale living docs 0，退出码 0。T-084 仍 open，仍在 frontier。没有 commit。

## 返工 #2：没有启动记录的尾注直接拒收

用户决定（answer `20261015T043855Z-ideation-answer-001`，原话「尾注这关直接拒收 (Recommended)」）：带 A2A 尾注、但该 attempt 没有启动记录的交付，在尾注检查直接打回，不进入审查。完全无尾注仍按 6a 记一次「推断：缺尾注」。拒收码 `trailer_launch_record_missing` 由主控指定。主 checkout 的票据记录在 `b94dd1fe`，本工作树没有改主 checkout，也没有把那段话抄进票据。

上文「发现 3，本轮未改」是返工 #1 的记录。本轮按这个决定改了产品。

`checkTrailers` 在任务不符、坏尾注、Attempt/Session/Role 不符之后，若尾注结构完整且 `attempt.delivery` 不存在，写入 `trailer_launch_record_missing`。`trailer_check` 事件只在这个码上带 `reason: 缺启动记录`。其后四行与启动记录的比较保持原样，仍要求有 delivery。Launch、Tool、Effort 必须与记录一致；Model 仍可为字面量 `unknown`。

### 受影响的旧测试

先列出、再改。`workbench/tests/` 下没有 T-081、t081 或坏 worker 套件文件，没有留给主控的未改套件。

这些文件用过 claim-only，结果会因新契约改变，已按新契约改，没有留下“带尾注的 claim-only 仍放行”的开关：

| 文件 | 改动 |
| --- | --- |
| `workbench/tests/test_task_cards_e2e.py` | 快照案的 claim 提交改为无尾注 |
| `workbench/tests/test_worktree_lifecycle_e2e.py` | 三案的 claim 提交改为无尾注 |
| `workbench/tests/test_quality_chain_e2e.py` | `red_review_required`、`red_terminal_prerequisites` 改为无尾注 |
| `workbench/tests/test_quality_legacy_e2e.py` | `manual_claim_reviewed_score_refused` 改为无尾注 |
| `workbench/tests/test_daemon_recovery_e2e.py` | verify 夹具无尾注；集成改为受管提交并带执行者分数。另见下方进程身份 |

无尾注的 claim 仍能通过尾注检查，并记一次人工介入。集成还要启动记录和分数，所以恢复套件的集成案改走 `create_managed()`，提交使用与记录一致的受管尾注，`integrate` 带上 `--score-file`。`acceptance/test_coop_e2e.py` 的 W07 本来就没有 A2A 尾注，没有改。`run_t076_legacy_green.py` 本轮没有重跑。

### 红态 red-03

在改 `core.ts` 之前，经 `node workbench/src/gates/cli.ts` 跑。claim-only、四项伪造、verify 放行。汇总 `red-03/summary.json` 状态 PASS。这里的 PASS 表示放行红态被复现。

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t084
python3 -B workbench/tests/test_t084_trailer_record.py --phase red-03 --output evidence/2026-10-15-batch15/T-084
```

退出码 0，标准输出 `{"status": "PASS", "phase": "red-03"}`。`claim-forged`：`verify_ok` true，`trailer_check.passed` true，人工介入 0，delivery 为空。`claim-none`：verify 通过，人工介入 1，标签 `推断：缺尾注`。

### 绿态 green-03

```sh
python3 -B workbench/tests/test_t084_trailer_record.py --phase green-03 --output evidence/2026-10-15-batch15/T-084
```

退出码 0，标准输出 `{"status": "PASS", "phase": "green-03"}`。汇总 `green-03/summary.json`。

| 案 | verify |
| --- | --- |
| claim-forged | 拒，`trailer_launch_record_missing`，事件原因 `缺启动记录`，人工介入 0 |
| claim-none、none | 过，人工介入 1，标签 `推断：缺尾注` |
| launch、tool、model、effort、model-card、effort-card、effort-unknown | 拒，`trailer_identity_mismatch`，事件没有这条原因 |
| match、unknown | 过，人工介入 0 |

### 变异 mutants-03

删掉 `else if (!attempt.delivery) error = "trailer_launch_record_missing";` 这一行。副本在 `/tmp`，已经删除。补丁在 `mutants-03/patches/delete-launch-record-rejection.patch`。

```sh
python3 -B workbench/tests/test_t084_trailer_record.py --phase mutants-03 --output evidence/2026-10-15-batch15/T-084
```

退出码 0，标准输出 `{"status": "DETECTED", "phase": "mutants-03"}`。`DETECTED` 表示绿态判定不再是 PASS。`claim-forged` 变回放行。`launch` 仍是 `trailer_identity_mismatch`。`claim-none`、`none`、`match` 仍放行；两个无尾注案仍是一次「推断：缺尾注」。

### 旧测试回归

任务卡 `regression-03/cards/run.json`：status PASS，tests_run 5，failures 0。汇总没有方法名。改动落在 claim 快照案。

工作树三案：

```sh
python3 -B workbench/tests/test_worktree_lifecycle_e2e.py --output evidence/2026-10-15-batch15/T-084/regression-03/worktree --phase candidate --case test_clean_revoke --case test_verification_name --case test_completed_verification_cleanup
```

`regression-03/worktree/run.json` status PASS，三案 exit_code 0。

质量：

```sh
python3 -B workbench/tests/test_quality_chain_e2e.py --source /Users/luckye/Documents/Code/a2a-wt-t084 --output evidence/2026-10-15-batch15/T-084/regression-03/quality-red --group red --case red_review_required --case red_terminal_prerequisites --card-dialect current
python3 -B workbench/tests/test_quality_legacy_e2e.py --source /Users/luckye/Documents/Code/a2a-wt-t084 --output evidence/2026-10-15-batch15/T-084/regression-03/quality-legacy --case manual_claim_reviewed_score_refused
```

两份 `run.json` status PASS。`red_review_required`、`red_terminal_prerequisites`、`manual_claim_reviewed_score_refused` 的 outcome 都是 passed。

恢复套件跑了三次，前两次目录保留。

```sh
python3 -B workbench/tests/test_daemon_recovery_e2e.py --output evidence/2026-10-15-batch15/T-084/regression-03/recovery-before-managed
```

`recovery-before-managed/run.json` status INCOMPLETE，5 败。当时 verify 已改为无尾注，集成仍是 claim。四个集成案在 git barrier 前返回 `score_required`（`integrate` 没有 `--score-file`）。verify 中断案失败在 `interrupt()`：ps 命令行里没有 `workbench/src/daemon.ts`，实际是 `daemon_acceptance_host.ts`。

第二次把集成改为 `create_managed()` 并传入分数，输出在 `regression-03/recovery`。status INCOMPLETE，5 败，都停在同一条 `daemon.ts` 断言。集成案已经越过尾注、分数和 provenance，进入 `interrupt()`。

这条断言写于 T-075。当时的通过记录里，被杀进程是 ppid 为 1 的 `node .../workbench/src/daemon.ts`（`evidence/2026-10-10-batch12/T-075/card-4/outside-checks-02/test_daemon_recovery_e2e/run.json`）。当前 `DaemonCards` 启动的是 `daemon_acceptance_host.ts`，它在进程内调用 `serve()`。本轮把 ps 预期改成这个宿主脚本，并核对 pid 就是 `self.host.pid`。`regression-03/recovery-host-identity`：身份断言已过，5 案仍败，原因是 SIGKILL 之后 10 秒内 ps 仍看得到该 pid。宿主是测试进程的子进程，杀掉后会留下僵尸，直到父进程 `wait`。

补上 `self.host.wait(timeout=10)` 后再跑：

```sh
python3 -B workbench/tests/test_daemon_recovery_e2e.py --output evidence/2026-10-15-batch15/T-084/regression-03/recovery-reap
```

退出码 1，墙钟 26.881 秒。`recovery-reap/run.json` status INCOMPLETE，tests_run 5，failures 1。四个集成案通过。`test_daemon_verify_interruption_and_operation_lock` 在第二次 verify 失败：退出码 1，错误 `review_launch_config_required`。`interrupt()` 删掉套接字之后，`restart()` 调用 `cli.ts daemon_start`，配置是空对象。`panes.ts` 的 `createReview` 在没有 `reviewers` 项时返回这个码。被杀掉的宿主带有审查运行时；重启起来的是不带这项配置的 daemon。本轮没有改 `restart()`，也没有改产品。这一案保持 INCOMPLETE。

### 验收审查与地图

只读验收审查看的是当时的 `core.ts`（sha256 `03bb6616a52e746dcccca413d4fd00ca722080d92c5ce14460eef117ab37ef7a`）和 `README.md`（sha256 `73bb16513598dc856aad268fe3d57acbb3b4154027148f49f71861e6b57325a3`）。结论 STATUS PASS，无发现。审查没有重跑套件。审查结束时这两个文件还是这两个哈希。返工审阅又改了 `core.ts`，见下一节。

完成后重跑：

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t084
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

Problems 0，Stale living docs 0，退出码 0。T-084 仍 open，仍在 frontier。没有 commit。

## 返工审阅

### 恢复套件在基线上已经失败

用 `git archive fb5dd288` 把基线导出到 `/tmp/t084-baseline-fb5dd288`。没有 `git worktree add`，没有 checkout，没有改共享 `.git`。`workbench/node_modules` 符号链接指向本工作树。在这棵树上跑基线自己的 `test_daemon_recovery_e2e.py`，输出在 `/tmp/t084-recovery-baseline-run`，`run.json` 已拷到 `regression-03/recovery-baseline/run.json`。

```sh
cd /tmp/t084-baseline-fb5dd288
python3 -B workbench/tests/test_daemon_recovery_e2e.py --output /tmp/t084-recovery-baseline-run
```

退出码 1，墙钟 17.192 秒。status INCOMPLETE，tests_run 5，failures 5。

`test_daemon_verify_interruption_and_operation_lock` 的原样失败信息：

```text
AssertionError: '/private/tmp/t084-baseline-fb5dd288/workbench/src/daemon.ts' not found in '65276 64892 node /private/tmp/t084-baseline-fb5dd288/workbench/tests/daemon_acceptance_host.ts /tmp/a4r-yfdqr_fw/c-vmkhj0qg/state /tmp/a4r-yfdqr_fw/c-vmkhj0qg/worker-control /tmp/a4r-yfdqr_fw/c-vmkhj0qg/daemon-ready.json /private/tmp/t084-baseline-fb5dd288/workbench/src/gates/core.ts /private/tmp/a4r-yfdqr_fw/c-vmkhj0qg/quality-control\n'
```

位置是基线文件 `interrupt()` 第 91 行。ps 里的进程是 `daemon_acceptance_host.ts`。这一案没有走到 `review_launch_config_required`。

另外四个集成案停在 git barrier 之前，客户端 stdout 是 `{"ok":false,"error":"score_required",...}`。`integrate` 没有 `--score-file`。

这是既有问题，与本票无关。基线没有通过，所以没有改本工作树里的恢复测试。工作树上的 `review_launch_config_required` 出现在本票改了 ps 预期并 `wait` 回收子进程之后，测试才继续跑到 `restart()`。基线在更早的断言上已经失败。

### 四行多余条件

`else if (!attempt.delivery)` 之后，四行里的 `attempt.delivery &&` 在这条分支上恒为真，已从这四行删掉。

先按原来的 else-if 链删掉 `&&`，跑了一次。`green-04-chain` 为 PASS。`mutants-04-unguarded` 为 INCOMPLETE：删掉拒收行之后，下一行读取 `attempt.delivery.launch_id`，`claim-forged` 变成 `gate_failure`，不再是放行。

四行比较因此放进 `if (attempt.delivery)` 块，缺记录仍由这个块的 else 拒收，码仍是 `trailer_launch_record_missing`。四行里没有 `attempt.delivery &&`。删掉 else 上的拒收后，`claim-forged` 再次放行。

```sh
cd /Users/luckye/Documents/Code/a2a-wt-t084
python3 -B workbench/tests/test_t084_trailer_record.py --phase green-04 --output evidence/2026-10-15-batch15/T-084
python3 -B workbench/tests/test_t084_trailer_record.py --phase mutants-04 --output evidence/2026-10-15-batch15/T-084
```

green-04 退出码 0，`{"status": "PASS", "phase": "green-04"}`。与 `green-03` 的 12 个案逐项相同：`verify_ok`、`verify_error`、`trailer_error`、`trailer_reason`、人工介入次数、标签都一致。`claim-forged` 仍拒收，原因仍是缺启动记录。`claim-none` 与 `none` 仍是一次「推断：缺尾注」。

mutants-04 退出码 0，`{"status": "DETECTED", "phase": "mutants-04"}`。四个变异都是 DETECTED，绿态判定都是 INCOMPLETE。前三个与 mutants-02 的放行/拒收相同：`effort-unknown`、`model-card`、`effort-card` 各自变成放行，其余拒收案仍是 `trailer_identity_mismatch`。mutants-02 的结果行没有 `trailer_reason` 字段；mutants-04 这个字段是 `[null]`。`delete-launch-record-rejection` 与 mutants-03 的五行结果相同，`claim-forged` 放行。

没有 commit。
