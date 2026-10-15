# T-086 结果

工作树 `/Users/luckye/Documents/Code/a2a-wt-t086`，分支 `exec/t086`，HEAD `bb6c0ba352ff7cab1f470d2db055caac36387bab`。改动未提交、未推送。`workbench/src/` 未改。票据验收框未勾。

结论：冲突夹具的尾注改为读取该 attempt 的启动记录后，`CONFLICT-ACTIVE-WRITEBACK` 与 `CONFLICT-ENDED-NEW-ATTEMPT` 在真实门禁入口上通过；冲突套件 7 案通过。其余会进门禁的尾注夹具按下面清点回归，通过。直接运行 `test_task_cards_e2e.py` 的失败在基线 `bb6c0ba3` 上复现，原因是没有拉起 daemon，见「基线上的既有失败」。

`git diff --stat`：

```
 workbench/tests/conflict_acceptance_host.ts    |  7 +++++--
 workbench/tests/test_worktree_lifecycle_e2e.py | 20 +++++++++++++++++---
 2 files changed, 22 insertions(+), 5 deletions(-)
```

## 红态

命令（`evidence/2026-10-15-batch15/T-086/red-01/command.txt`）：

```
cd /Users/luckye/Documents/Code/a2a-wt-t086
python3 -B workbench/tests/test_worktree_lifecycle_e2e.py --phase candidate --case test_conflict_active_worker_reworks_and_integrates --case test_conflict_ended_session_gets_new_attempt --output evidence/2026-10-15-batch15/T-086/red-01
```

套件入口调用 `node workbench/src/gates/cli.ts`。`--phase candidate`。`stdout.txt`：

```
{"case": "test_conflict_active_worker_reworks_and_integrates", "failures": 1, "errors": 0, "business_red": false}
{"case": "test_conflict_ended_session_gets_new_attempt", "failures": 1, "errors": 0, "business_red": false}
{"status": "INCOMPLETE", "phase": "candidate", "red_confirmed": null, "real_codex_turns": 0}
EXIT:1
```

`run.json` 的 `status` 为 `INCOMPLETE`，`real_codex_turns` 为 0。两案都是 `failures` 1、`errors` 0、`business_red` false、`exit_code` 1。`stderr.txt` 只有包装脚本写下的 `EXIT:0`；以 stdout 的 `EXIT:1` 和 `run.json` 为准。

两案都在修复后的 `verify` 上失败，错误是 `trailer_identity_mismatch`。

`01-test_conflict_active_worker_reworks_and_integrates/unittest.txt`：`test_worktree_lifecycle_e2e.py` 第 776 行 `v2 = self.cli('verify', ...)`。提交 `09c80ac73c4cd881cb2138683e5b73fdda19c7b2`。尾注 `tool` 为 `Codex 0.162.1`，`model` 为 `fixture`，`effort` 为 `xhigh`，`launch` 与 `native-session` 都是 `7ba0a401-4184-4101-91c2-75c12024f17c`。`Ran 1 test in 5.529s`，`FAILED (failures=1)`。同一次 `run.json` 里该 attempt 的 `delivery` 为 `launch_id` `7ba0a401-4184-4101-91c2-75c12024f17c`、`cli` `controlled-conflict-runtime`、`model` `gpt-6.1-sol`、`effort` `xhigh`。

`02-test_conflict_ended_session_gets_new_attempt/unittest.txt`：第 822 行 `self.cli('verify', ...)`。提交 `c1b17191fd52aa6a4e93a380938dc525271da2d9`。尾注同样是 `tool` `Codex 0.162.1`、`model` `fixture`、`effort` `xhigh`，`launch` 与 `native-session` 为 `403072b3-d435-4a34-8eec-d9d15d01c757`。`Ran 1 test in 4.927s`，`FAILED (failures=1)`。

当时的 `commit_worker` 把 Tool、Model、Launch 写成字面量 `Codex 0.162.1`、`fixture` 和 `attempt['thread_id']`。这个宿主的 launch id 就是 thread id，所以 Launch 碰巧相等；拒绝来自 Tool 和 Model 与启动记录不一致。

## 夹具

只改测试宿主和 `commit_worker`。门禁比较未改。

`conflict_acceptance_host.ts` 的 `createThread` 把 `sessionFacts` 返回的同一个对象写入 `worker-creations.jsonl`，并带上 `attempt` 以便按 attempt 查找。`cli_version` 仍是 `controlled-conflict-runtime`，`model` 与 `effort` 仍取任务卡 executor。`id` 仍是 `attempt.thread_id`。

`test_worktree_lifecycle_e2e.py` 的 `launch_record` 只取 `attempt` 字段等于该 `attempt_id` 的一行。若 `attempt.delivery` 已经存在，则核对 `launch_id`/`id`、`cli`/`cli_version`、`model`、`effort`，不一致就抛错。`commit_worker` 用这一行写 `A2A-Tool`、`A2A-Model`、`A2A-Effort`、`A2A-Launch`。`foreign=True` 仍只把 `A2A-Task` 写成 `foreign-task`。`A2A-Native-Session` 仍是 `attempt['thread_id']`。

提交发生在 submit 把记录抄进 `attempt.delivery` 之前，所以提交时读的是宿主 jsonl；delivery 出现后与同一行核对。

## 绿态

同一两案，命令见 `green-01/command.txt`，输出目录 `evidence/2026-10-15-batch15/T-086/green-01`。`stdout.txt`：

```
{"case": "test_conflict_active_worker_reworks_and_integrates", "failures": 0, "errors": 0, "business_red": false}
{"case": "test_conflict_ended_session_gets_new_attempt", "failures": 0, "errors": 0, "business_red": false}
{"status": "PASS", "phase": "candidate", "red_confirmed": null, "real_codex_turns": 0}
EXIT:0
```

`stderr.txt` 为空。两份 `unittest.txt` 末行都是 `OK`。

`green-01/fixtures.tar.gz` 里的 `worker-creations.jsonl`：

- `t-xnod4m6e` 一行：`id` `52eeace3-bd02-480e-bd7d-14ea761f0bcb`，attempt `9bec1a96-8807-4831-9bd8-3e208e3f4ba4`，`cli_version` `controlled-conflict-runtime`，`model` `gpt-6.1-sol`，`effort` `xhigh`。
- `t-i_hznvia` 两行：原 attempt `4c7a45ff-848b-40a2-855f-d559c3db68b6` 的 `id` `1464e631-41c2-445e-ad19-804861fab2ce`；替换 attempt `b485337a-4eea-4b22-b0c5-11218c58f008` 的 `id` `e84401e2-0d6b-40d9-8875-a686162677a0`。两行的 cli、model、effort 与上一行相同。

冲突全套件命令见 `conflict-suite-01/command.txt`。`stdout.txt` 七案都是 `failures` 0、`errors` 0、`business_red` false，最后一行：

```
{"status": "PASS", "phase": "candidate", "red_confirmed": null, "real_codex_turns": 0}
EXIT:0
```

`run.json` 七案 `exit_code` 都是 0，`target_passed` 都是 true。其中包括 `test_conflict_rework_still_rejects_forbidden_path` 与 `test_conflict_rework_still_rejects_foreign_trailer`。`stderr.txt` 为空。`real_codex_turns` 为 0。

## 清点与回归

范围是当前树上 `workbench/tests/` 与 `acceptance/` 里写 A2A 尾注的测试。证据目录里的历史副本不改。产品钩子 `workbench/hooks/hook.py` 与 `scripts/git-hooks/hook.py` 未改。

会调真实模型或复制 `~/.codex/auth.json` 的脚本只做静态阅读，没有运行。

| 文件 | 判定 | 结果 |
| --- | --- | --- |
| `workbench/tests/test_worktree_lifecycle_e2e.py` 的 `commit_worker`，以及 `conflict_acceptance_host.ts` | 受影响，已改 | 见上，绿态与冲突全套件 PASS |
| 同文件里走父类 `commit()` 的四个受管用例 | 父类已从启动记录取尾注 | `lifecycle-managed` PASS |
| `workbench/tests/test_daemon_gates_e2e.py` | `managed_trailers` 按 attempt 读 `worker-creations.jsonl` | 15 项 PASS。这是任务卡断言的真实入口 |
| `workbench/tests/test_task_cards_e2e.py` | 有 `thread_id` 时调用 `managed_trailers`。直接 `main` 不启动 daemon | 直接入口失败，见下一节。文件相对 HEAD 无差异 |
| `workbench/tests/test_t084_trailer_record.py` | 尾注来自 jsonl，错配是故意的 | `green-04` PASS。针未改 |
| `workbench/tests/test_multiturn_identity_e2e.py` | `managed_trailers` 取现场 facts | 4 项 PASS |
| `workbench/tests/test_relay_conflict_e2e.py` | `managed_trailers` 取 `A2A_TOOL`、turn context 与 launch id | 1 项 PASS，`new_attempt_delivery` 期望与实际都是 `submitted` |
| `workbench/tests/test_conflict_trailer_proofs.py` | 钩子写尾注后 verify；多写的 C2 尾注期望 `invalid_trailers` | 2 项 PASS，`real_codex_turns` 0 |
| `workbench/tests/test_quality_chain_e2e.py` | 受管 `commit()` 写死 `codex-cli 0.162.1`、`gpt-6.1-sol`、`xhigh`，Launch 用 `pane_status` 的 `self.launch`。这些值与受控宿主的版本检查和 turn context 相同 | `--card-dialect current` 下 controls 8 案、red 11 案都是 `passed`。未改字面量 |
| `workbench/tests/test_hook_environment.py` | 只断言钩子行。无 turn 时 Model/Effort 为 `unknown` 是钩子输出 | PASS，`failures` 为 `[]` |
| `workbench/tests/test_hook_turn_facts.py` | 断言钩子抄最新根回合的 model/effort | PASS，五案都是 `business-pass` |
| `acceptance/test_herdr_traceability_e2e.py` | 假 Herdr，文档写明不调模型。期望钩子尾注 | 7 项，`failures` 0，`errors` 0 |
| `workbench/tests/test_offline_trace_e2e.py` | 源码中没有 A2A 尾注 | 未跑 |
| `workbench/tests/run_pane_lifecycle.py` | 源码中没有 A2A 尾注。会复制 auth 并占用真实回合 | 未跑 |
| `workbench/tests/run_t076_real.py` | 期望 Launch 为 `launch['id']`，Model/Effort 等于 turn context 且等于 `model_requested` / `effort_requested`，Tool 为 `codex-cli 0.162.1` | 静态核对，未跑 |
| `workbench/tests/run_t076_quality_real.py` | 期望 Launch 为 `launches['worker']['id']`，Tool `codex-cli 0.162.1`，Model `gpt-6.1-sol`，Effort `xhigh` | 静态核对，未跑 |
| `workbench/tests/run_worker_delivery.py` | 第 197 行调用 `verify`，第 207–210 行期望钩子消息里 Model 与 Effort 都是 `unknown`，Tool 为 `codex-cli 0.162.1`，Launch 为 `launch['id']`。门禁允许 Model 为字面量 `unknown`，Effort 为 `unknown` 时会 `trailer_identity_mismatch`。钩子只在没有 turn context 时写 `unknown` | 静态核对，未跑，未改期望。这不是本票已观察到的失败 |
| `workbench/tests/run_t076_red.py` | 设计为红态：它期望 `test_hook_turn_facts.py` 返回码 1，且前四个用例 Model/Effort 为 `unknown`。当前钩子事实套件是 PASS / `business-pass` | 未跑。这是设计好的红态夹具，不计入本票失败 |

回归命令都在对应目录的 `runner-command.txt`，工作目录是本工作树，解释器是 `python3 -B`。stdout 末行：

- `hook-environment`：`status` PASS，`EXIT:0`
- `hook-turn-facts`：`{"status": "PASS", "cases": [["matching-request", "business-pass"], ["different-request", "business-pass"], ["latest-turn", "business-pass"], ["auxiliary-ignored", "business-pass"], ["current-context-missing", "business-pass"]]}`，`EXIT:0`
- `herdr-trace`：`summary.json` 为 `tests` 7、`failures` 0、`errors` 0，`scripts_root` 指向本工作树 `scripts`，`EXIT:0`
- `t084-green-04`：`{"status": "PASS", "phase": "green-04"}`，`EXIT:0`
- `daemon-gates`：`{"status": "PASS", "tests_run": 15, "failures": 0, "errors": 0}`，`EXIT:0`
- `trailer-proofs`：`status` PASS，`tests_run` 2，`failures` 0，`errors` 0，`real_codex_turns` 0，合约 `verify-refuses-extra-C2-trailers` 期望与实际都是 `invalid_trailers`，`EXIT:0`
- `multiturn`：`{"status": "PASS", "tests_run": 4, "failures": 0, "errors": 0, "skipped": 0}`，`EXIT:0`
- `relay`：`status` PASS，`tests` 1，`failures` 0，`real_codex_turns` 0，`EXIT:0`
- `quality-controls`：`run.json` `status` PASS，`real_codex_turns` 0，8 案 `outcome` 都是 `passed`，`EXIT:0`
- `quality-red`：`run.json` `status` PASS，`real_codex_turns` 0，11 案 `outcome` 都是 `passed`，`EXIT:0`
- `lifecycle-managed`：四案 `failures` 0、`errors` 0，`{"status": "PASS", "phase": "candidate", "red_confirmed": null, "real_codex_turns": 0}`，`EXIT:0`
- `task-cards`：`{"status": "INCOMPLETE", "tests_run": 14, "failures": 49, "errors": 0, "artifact_root": "/tmp/a2a-card2-e2e-i59q3j60"}`，`EXIT:1`。见下一节

## 基线上的既有失败

只有这一条，与本票的尾注夹具无关。

`test_task_cards_e2e.py` 的 `main` 直接调用 `node workbench/src/gates/cli.ts`，`setUp` 不启动 daemon。CLI 要连接 `state/control.sock`。本工作树上该文件相对 HEAD 无差异（`git diff --exit-code -- workbench/tests/test_task_cards_e2e.py` 通过）。工作树回归的 `run.json` 里 `trailer_identity_mismatch` 出现 0 次，`daemon_call_failed` 与 `connect ENOENT` 覆盖这些失败。第一例期望 `invalid_task_card`，实际是 `daemon_call_failed`。

基线证明：`git archive bb6c0ba352ff7cab1f470d2db055caac36387bab workbench` 解到 `/tmp/t086-base-bb6c0ba3`，`workbench/node_modules` 符号链接到本工作树，不新建 git worktree。归档内的 `test_task_cards_e2e.py` 与工作树该文件 `cmp` 相同。命令：

```
cd /tmp/t086-base-bb6c0ba3
python3 -B workbench/tests/test_task_cards_e2e.py --output /Users/luckye/Documents/Code/a2a-wt-t086/evidence/2026-10-15-batch15/T-086/task-cards-baseline
```

`stdout.txt`：`{"status": "INCOMPLETE", "tests_run": 14, "failures": 49, "errors": 0, "artifact_root": "/tmp/a2a-card2-e2e-a1gm74s2"}`。`stderr.txt` 记录 `Ran 14 tests in 4.686s`、`FAILED (failures=49)`。第一例断言为 `daemon_call_failed` 不等于期望的 `invalid_task_card`，详情是 `Error: connect ENOENT .../state/control.sock`。`run.json` 中 `trailer_identity_mismatch` 为 0 次。门禁路径是归档里的 `workbench/src/gates/cli.ts`。

带 daemon 的入口是 `test_daemon_gates_e2e.py`，本票回归 15 项 `failures` 0。本票没有改 `test_task_cards_e2e.py`，也没有让它自己拉起 daemon。

归档目录和 `/tmp/a2a-card2-e2e-a1gm74s2` 已删除。本票回归产生的临时夹具目录也已删除。T-078 的 daemon（PID 23492，`a2a-wt-t078` 的 `daemon.ts`）仍在。

## 地图状态

写完本文件之后再跑一次 `project_map.py status`，输出附在下面。

命令：

```
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

工作目录是本工作树。退出码 0。输出：

```
Problems (0):
Stale living docs (0):
Frontier (10):
  - T-010 [task] Account for descendant agent sessions and model settings
  - T-011 [task] Check monitor coverage and finding disposition
  - T-012 [task] Define research deliverables and handoff evidence
  - T-013 [task] Make fixture governance scope explicit
  - T-014 [task] Check evidence capture and artifact packaging before model runs
  - T-078 [build] S4 两个主控进工作台：主控窗格、交互输入、收件箱进库、唤醒、用户输入记录、紧急停止
  - T-081 [build] 门禁加固 D2：坏 worker 测试集，在真实门禁入口逐个证明拒收，并统计误拒绝
  - T-082 [build] 门禁加固 D3：reviewer 必查完成条件是否够格，并在一次性副本里做变异检查
  - T-085 [build] 缺陷：恢复套件中断用例重启后 daemon 缺审查配置（review_launch_config_required）
  - T-086 [build] 缺陷：T-084 后测试夹具仍写非启动记录的尾注（T-077 lifecycle 冲突两案失败）
```
