# T-086 结果（返工）

工作树 `/Users/luckye/Documents/Code/a2a-wt-t086`，分支 `exec/t086`。HEAD 仍是审查提交 `8f3d1b5e`（独立审查 01，对冻结候选 `d9dcc107` 给出 NO_GO，报告 `independent-review-01.md`）。本轮改动未提交、未推送。`git diff -- workbench/src` 为空。票据验收框未勾。

结论：受控冲突宿主按 attempt 写入与任务卡、`thread_id`、固定常量都不同的启动记录，`readThread` 把该记录的 `id` 作为 `runtime_identity.launch`。基线副本上两案在 verify 失败；当前工作树上两案与冲突套件七案通过。审查的 M1、M3、M4 在两案的 verify 上失败；M2 在有两行记录的结束会话一案上失败。M5 两案仍通过，因为这两案调用 `commit_worker` 时 attempt 上还没有 `delivery`。`test_quality_tracer_e2e.py` 与 `test_quality_widen_e2e.py` 已重跑。widen wide 与 tracer 同时跑时，`widen_score_after_cas` 的 5 秒等待会失败；基线副本上用同样的并发复现了同一次失败，单独跑则通过。`run_worker_delivery.py` 只改了期望，未运行。

本轮 `git diff --stat`：

```
 workbench/tests/conflict_acceptance_host.ts | 15 ++++++++++++---
 workbench/tests/run_worker_delivery.py      | 13 ++++++++++++-
 2 files changed, 24 insertions(+), 4 deletions(-)
```

`test_worktree_lifecycle_e2e.py` 相对 HEAD 无差异。`commit_worker` 仍按 `attempt_id` 读 `worker-creations.jsonl`，用该行的 `cli_version`、`model`、`effort`、`id` 写尾注。

## 宿主

`conflict_acceptance_host.ts` 的 `createThread` 对每个 attempt 写入：

- `id`：`launch-` 加 `attempt.attempt_id`
- `cli_version`：`conflict-cli-` 加 `attempt.attempt_id`
- `model`：`conflict-model-` 加 `attempt.attempt_id`
- `effort`：`conflict-effort-` 加 `attempt.attempt_id`
- `thread` 仍是 `attempt.thread_id`，`role` 为 `worker`

任务卡 executor 仍是 `model` `gpt-6.1-sol`、`effort` `xhigh`。记录里的 model、effort、cli 与 `controlled-conflict-runtime`、`Codex 0.162.1`、`fixture` 都不同，`id` 也不是 `thread_id`。

`readThread` 在 `workers` 里取这次创建。没有记录就抛出 `No controlled conflict worker creation`。`runtime_identity.launch` 用 `created.id`，`thread` 与 `native_session` 仍是 thread id。观察覆盖写在 `runtime_identity` 之后，结束会话的 `{stopped, running}` 和未知会话的 `{error}` 仍能盖住现场。

## 红态

基线副本：`git archive bb6c0ba352ff7cab1f470d2db055caac36387bab` 解到 `/tmp/t086-rework-baseline`，只含套件快照所需路径，没有叠本轮宿主。副本里本地提交 `fdc6bca356afa0e29ca3e957ef66978f8f441cc1`，说明是 `baseline bb6c0ba3 copy`。`rework-red-01/preflight.json` 的 HEAD 就是这枚提交。套件的 `--phase baseline` 要求 HEAD 等于 `14b57d22a84bcaebfa91c5051b9909b53a570fac`，所以这次用 `--phase candidate` 跑这棵基线树。副本和现场目录已删。

命令（`rework-red-01/command.txt`）：

```
cd /tmp/t086-rework-baseline
python3 -B workbench/tests/test_worktree_lifecycle_e2e.py --phase candidate --case test_conflict_active_worker_reworks_and_integrates --case test_conflict_ended_session_gets_new_attempt --output /Users/luckye/Documents/Code/a2a-wt-t086/evidence/2026-10-15-batch15/T-086/rework-red-01
```

`run.json`：`status` `INCOMPLETE`，`phase` `candidate`，`real_codex_turns` 0，`cwd` `/private/tmp/t086-rework-baseline`，`fixture_root` `/tmp/s3-xp8s5tmf`。`stdout.txt` 两案都是 `failures` 1、`errors` 0、`business_red` false。`stderr.txt` 为空。

两案都在 verify 上失败，错误是 `trailer_identity_mismatch`。活动案提交 `2521a872193950352dbadf48d4e311b81641884f`，结束会话案提交 `c1fe5af004ec217a413eaf9afa017d9d39cd1711`。尾注 Tool `Codex 0.162.1`、Model `fixture`、Effort `xhigh`，Launch 与 Native-Session 相同。活动案二者都是 `3cefda50-f8c0-4c41-b588-f5d14b1876d4`。断言全文在各自的 `unittest.txt`。

## 绿态

同一两案，工作树为当前未提交宿主。命令见 `rework-green-01/command.txt`，输出目录 `evidence/2026-10-15-batch15/T-086/rework-green-01`。

`stdout.txt` 两案 `failures` 0、`errors` 0，末行 `{"status": "PASS", "phase": "candidate", "red_confirmed": null, "real_codex_turns": 0}`。`run.json` 两案 `exit_code` 0、`target_passed` true。`stderr.txt` 为空。`fixture_root` 当时是 `/tmp/s3-k9jvi4p3`，目录已删，jsonl 留在 `fixtures.tar.gz`。

- `t-l3csilao` 两行。attempt `c4376692-1d87-4ba1-a892-6c16746d9104` 的 `id` 是 `launch-c4376692-1d87-4ba1-a892-6c16746d9104`，thread `b059801b-46fe-42e2-bec1-34a6960c0c45`。attempt `38a4e157-3237-42ce-b245-7ca4d568f6b3` 的 `id` 是 `launch-38a4e157-3237-42ce-b245-7ca4d568f6b3`，thread `bdfa72cf-e442-48f9-92e6-887a42013e4a`。
- `t-m6x69e34` 一行。attempt `3dcb5ceb-e5df-4f12-98c9-43d122c3c2c6` 的 `id` 是 `launch-3dcb5ceb-e5df-4f12-98c9-43d122c3c2c6`，thread `0a1859ca-7ef6-46a9-9a65-fec5c18425aa`。

每行的 cli、model、effort 都是 `conflict-cli-<attempt>`、`conflict-model-<attempt>`、`conflict-effort-<attempt>`。Launch 与 thread id、与任务卡都不同。

第一轮的 `green-01` 与 `conflict-suite-01` 用的仍是 `controlled-conflict-runtime`、`gpt-6.1-sol`、`xhigh`，Launch 等于 thread id。那是审查否掉的取值，不作为本轮候选的证据。

## 变异 M1–M5

一次性副本 `/tmp/t086-rework-candidate`：`git archive` 自 HEAD `8f3d1b5e`，再叠上工作树里未提交的 `conflict_acceptance_host.ts`，本地提交后只改副本里的 `test_worktree_lifecycle_e2e.py`。`workbench/src/gates/core.ts` 与工作树该文件相同。每个变异跑上面两案，`--phase candidate`。副本已删。门禁比较未改。

| 变异 | 改法 | 输出目录 | 结果 |
| --- | --- | --- | --- |
| M1 | 不读 jsonl。Tool `Codex 0.162.1`，Model `fixture`，Effort `xhigh`，Launch `attempt['thread_id']` | `rework-m1` | `INCOMPLETE`。两案 `failures` 1。verify 错误 `trailer_identity_mismatch`，尾注就是这些字面量 |
| M2 | jsonl 非空时固定取第一行，不按 attempt 过滤 | `rework-m2` | `INCOMPLETE`。活动案 `failures` 0（该案只有一行）。结束会话案 `failures` 1，`trailer_identity_mismatch` |
| M3 | 不读 jsonl。Tool `controlled-conflict-runtime`，Model `gpt-6.1-sol`，Effort `xhigh`，Launch `attempt['thread_id']` | `rework-m3` | `INCOMPLETE`。两案 `failures` 1。verify 错误 `trailer_identity_mismatch`，尾注就是这些常量 |
| M4 | 不读 jsonl。Tool `controlled-conflict-runtime`，Model/Effort 读 `conflict-card.json` 的 executor，Launch 用 `thread_id` | `rework-m4` | `INCOMPLETE`。两案 `failures` 1。尾注同样是 `controlled-conflict-runtime`、`gpt-6.1-sol`、`xhigh`，Launch 等于 Native-Session |
| M5 | `commit_worker` 开头若 `attempt.get('delivery')` 则抛 `delivery present at commit`，否则仍读 jsonl | `rework-m5` | `PASS`。两案 `failures` 0、`target_passed` true。两份 `unittest.txt` 都是 `OK`，没有 `delivery present` |

命令都在各目录的 `command.txt`，工作目录是 `/tmp/t086-rework-candidate`，`--output` 指向对应证据目录。五次 `real_codex_turns` 都是 0，`stderr.txt` 都为空。

M2 结束会话案的被拒尾注属于另一条 attempt：提交上的 attempt 是 `05fb25c3-556f-409a-bc20-2f5017f056fb`，Tool/Model/Effort/Launch 却是 `conflict-cli-df3b036d-8b58-46cd-a59b-655e86e58c47` 和 `launch-df3b036d-8b58-46cd-a59b-655e86e58c47`。Native-Session 是 `5bda87dc-a2d6-44ce-8287-53595afdaa38`。

M3 活动案 Launch 与 Native-Session 都是 `80f93cf9-b56e-4ef5-af50-61e009dd6be0`。结束会话案二者都是 `11ed8c5b-e4c5-4fb2-9e83-b229bcba6f6b`。M4 活动案二者都是 `57fc3c3c-0dbc-428a-b511-cd0562f311b9`。

M5 走到的是 jsonl 分支。`prepare_conflict` 在 `submit` 之前调用 `commit_worker`。活动案的返工提交在 `repair` 里，也在 `submit_request` 之前；随后还有一次未获准的第三次 `commit_worker`，用的仍是当时的 attempt 字典。结束会话案对替换 attempt 先 `commit_worker`，再 `submit`。这三处调用的对象上都没有 `delivery`。本轮没有为了让 M5 失败去造一条 delivery 路径。

## 冲突套件

七案都在当前工作树上、`--phase candidate`。命令见 `rework-conflict-suite/command.txt`，输出目录 `evidence/2026-10-15-batch15/T-086/rework-conflict-suite`。

`stdout.txt` 七案都是 `failures` 0、`errors` 0、`business_red` false，末行 `{"status": "PASS", "phase": "candidate", "red_confirmed": null, "real_codex_turns": 0}`。`run.json` 七案 `exit_code` 0、`target_passed` true。`fixture_root` `/tmp/s3-glu7lpg4`，目录已删。`stderr.txt` 为空。

七案：`test_conflict_active_worker_reworks_and_integrates`、`test_conflict_ended_session_gets_new_attempt`、`test_conflict_unknown_session_preserves_scene_and_reports`、`test_conflict_unknown_delivery_does_not_resend`、`test_merge_command_error_is_not_text_conflict`、`test_conflict_rework_still_rejects_forbidden_path`、`test_conflict_rework_still_rejects_foreign_trailer`。

## 质量套件

审查指出清单漏了经 `QualityCase.commit` 写受管尾注的两个文件。本轮按各自入口重跑，`real_codex_turns` 都是 0。现场目录已删，`run.json` 里仍记着当时的 `artifact_root`。

| 入口 | 命令与输出 | 结果 |
| --- | --- | --- |
| `workbench/tests/test_quality_tracer_e2e.py` | `quality-tracer/command.txt`，目录 `quality-tracer` | `run.json` `status` PASS，`card_dialect` `legacy`，13 案 `outcome` 都是 `passed`。`stdout.txt` 末行 `TRACER_EXIT:0` |
| `workbench/tests/test_quality_widen_e2e.py --group wide` | 与 tracer 同时启动。目录 `quality-widen-wide` | `run.json` `status` INCOMPLETE，`card_dialect` `current`，15 案里 14 案 `passed`。`widen_score_after_cas` 为 `harness_error`。`stdout.txt` 末行 `WIDEN_WIDE_EXIT:1` |
| 同一 wide 命令，稍后单独重跑 | 目录 `quality-widen-wide-solo` | `run.json` `status` PASS，15 案 `outcome` 都是 `passed`，含 `widen_score_after_cas` |
| `test_quality_widen_e2e.py --group review-red` | 目录 `quality-widen-review-red` | `run.json` `status` PASS，`card_dialect` `current`，3 案 `passed`。`stdout.txt` 末行 `WIDEN_REVIEW_EXIT:0` |

并行 wide 的失败在 `test_quality_widen_e2e.py` 第 250 行，`score_cas_recovery('after')` 调用 `wait_for`。`test_quality_tracer_e2e.py` 第 16–23 行把等待限制为 5 秒，超时抛出 `HarnessFailure('Expected explicit fixture boundary was not reached: false')`。traceback 里没有 `trailer_identity_mismatch`。本轮没有改这个等待。目录 `quality-widen-wide` 保持 INCOMPLETE，不改成通过。单独重跑的 PASS 才是当前候选上这 15 案的回归结果。

这条失败在基线 `bb6c0ba3` 上可以复现，而且只在并发时出现。`git diff bb6c0ba352ff7cab1f470d2db055caac36387bab -- workbench/tests workbench/src acceptance/test_recovery_e2e.py scripts` 里，和质量套件相关的文件没有差异。有差异的是 `conflict_acceptance_host.ts`、`run_worker_delivery.py`、`test_worktree_lifecycle_e2e.py`。widen 不导入这三份。

基线副本 `/tmp/t086-baseline-quality` 来自 `git archive bb6c0ba352ff7cab1f470d2db055caac36387bab` 的 `workbench`、`acceptance/test_recovery_e2e.py`、`scripts`，`workbench/node_modules` 符号链接到本工作树。副本和下面两次的现场目录都已删除。

单独跑 wide，命令见 `baseline-widen-wide/command.txt`，`--source` 指向该副本。外壳退出码 0。`run.json` `status` PASS，`card_dialect` `current`，`real_codex_turns` 0，15 案 `outcome` 都是 `passed`，含 `widen_score_after_cas`。当时的 `artifact_root` 是 `/private/tmp/q76-51wrcbks`。

同一副本上把 wide 和 tracer 一起启动。wide 的输出目录是 `baseline-widen-wide-loaded`，tracer 是 `baseline-quality-tracer-loaded`。wide 的 `run.json` `status` 为 INCOMPLETE，15 案里只有 `widen_score_after_cas` 是 `harness_error`，错误文本与 `quality-widen-wide` 相同。traceback 落在副本里的 `test_quality_widen_e2e.py` 第 274 行和第 250 行，以及 `test_quality_tracer_e2e.py` 第 23 行。这次没有把进程退出码写进 stdout，以 `run.json` 为准。tracer 13 案 `status` PASS，`card_dialect` `legacy`，`real_codex_turns` 0。两份 `artifact_root` 是 `/private/tmp/q76-t03zepwy` 和 `/private/tmp/q76-hm8gk8l5`。

因此这是基线上就有的 5 秒等待时序，不是本票宿主或尾注期望引进的失败。单独跑在基线和当前候选上都通过。

tracer 13 案：`tracer_success`、`tracer_score_required`、`tracer_wrong_candidate`、`tracer_malformed_review`、`tracer_review_needs_fix`、`tracer_reused_native`、`tracer_third_rejection`、`tracer_writer_cannot_review`、`tracer_run_waits`、`tracer_missing_delivery_context`、`tracer_identity_score`、`tracer_launch_policy_worker`、`tracer_launch_policy_reviewer`。

wide 15 案：`widen_red_rules_success`、`red_manifest_missing`、`red_base_not_failing`、`red_candidate_fails`、`red_rules_failing`、`red_rules_frozen`、`widen_red_manifest_paths`、`widen_red_symlink`、`widen_bad_project_config`、`widen_abandon`、`widen_upgrade`、`widen_ending_invalid_fields`、`widen_scores_roundtrip`、`widen_score_before_cas`、`widen_score_after_cas`。

review-red 3 案：`reviewer_create_red`、`reviewer_restart_red`、`reviewer_reclaim_red`。

## run_worker_delivery.py

用户 2026-10-15 经构思主控 `20261015T131159Z-ideation-answer-001` 决定，原话是「只改脚本期望」。脚本第 99 行把 `~/.codex/auth.json` 复制到隔离的 `CODEX_HOME`，后面会调用真实模型。本票未运行该脚本。判定：未运行。这不是通过。

期望改为：从 `orchestration_events` 里取出与 `attempt.delivery.turn_id` 相同、且文件名对应该 pane 的 `native_session` 的 `turn_context`，用最后一条的 `model`，以及 `effort` 或 `reasoning_effort`。二者都不得为 `unknown`，并且等于 `delivery` 的 `model` 与 `effort`。尾注 Model/Effort 用这两个值。Tool 仍是 `codex-cli 0.162.1`，Launch 仍是 `launch['id']`。钩子、门禁和「尾注必须与启动记录一致」都没有改。

其余会复制 auth 或调用真实模型的脚本仍只做静态核对，本轮未运行，也不记为通过：`run_t076_real.py`、`run_t076_quality_real.py`、`run_pane_lifecycle.py`、`run_t076_red.py`。`run_t076_red.py` 仍是设计好的红态夹具。

## 本轮只读、没有重跑的存档

这些目录是第一轮或审查留下的，本轮没有重跑，也没有改其中的 `run.json`：

- `red-01`、`green-01`、`conflict-suite-01`：第一轮宿主。取值等于本轮 M3 写死的常量。
- `hook-environment`、`hook-turn-facts`、`herdr-trace`、`t084-green-04`、`daemon-gates`、`trailer-proofs`、`multiturn`、`relay`、`quality-controls`、`quality-red`、`lifecycle-managed`
- `task-cards`、`task-cards-baseline`：直接运行 `test_task_cards_e2e.py` 的既有失败，原因是该入口不启动 daemon。第一轮已在 `bb6c0ba3` 副本上复现。本轮没有改这个文件，也没有把它算进尾注失败。
- `independent-review-01.md`

`test_offline_trace_e2e.py` 源码里没有 A2A 尾注，两轮都没有跑。产品钩子 `workbench/hooks/hook.py` 与 `scripts/git-hooks/hook.py` 未改。

本轮启动的临时目录已删除：`/tmp/t086-rework-baseline`、`/tmp/t086-rework-candidate`、`/tmp/t086-baseline-quality`、`/tmp/s3-xp8s5tmf`、`/tmp/s3-k9jvi4p3`、`/tmp/s3-glu7lpg4`，以及质量套件的 `/private/tmp/q76-avr0z9vx`、`q76-s2getttc`、`q76-_d7ffdbi`、`q76-rhdq21rl`、`q76-51wrcbks`、`q76-t03zepwy`、`q76-hm8gk8l5`。`workbench/node_modules` 仍在。写报告时 `ps -p 23492` 没有进程；本票没有向它发信号。本轮也没有留下 `a2a-wt-t086` 的 daemon。

## 地图状态

补上基线 widen 之后再跑一次 `project_map.py status`。工作目录是本工作树。命令：

```
python3 /Users/luckye/Documents/SKILLS/project-map-skill/project-map/scripts/project_map.py status --root .
```

退出码 0。输出：

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

## 第一轮存档

下面是审查 01 之前的记录，HEAD 当时写成 `bb6c0ba3`，宿主把任务卡和固定常量写进启动记录。其中的通过结论、diffstat，以及文末「T-078 的 daemon 仍在」和那次地图状态，都停在那一轮。本轮结论以上面各节为准。


工作树 `/Users/luckye/Documents/Code/a2a-wt-t086`，分支 `exec/t086`，HEAD `bb6c0ba352ff7cab1f470d2db055caac36387bab`。改动未提交、未推送。`workbench/src/` 未改。票据验收框未勾。

结论：冲突夹具的尾注改为读取该 attempt 的启动记录后，`CONFLICT-ACTIVE-WRITEBACK` 与 `CONFLICT-ENDED-NEW-ATTEMPT` 在真实门禁入口上通过；冲突套件 7 案通过。其余会进门禁的尾注夹具按下面清点回归，通过。直接运行 `test_task_cards_e2e.py` 的失败在基线 `bb6c0ba3` 上复现，原因是没有拉起 daemon，见「基线上的既有失败」。

`git diff --stat`：

```
 workbench/tests/conflict_acceptance_host.ts    |  7 +++++--
 workbench/tests/test_worktree_lifecycle_e2e.py | 20 +++++++++++++++++---
 2 files changed, 22 insertions(+), 5 deletions(-)
```

### 红态

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

### 夹具

只改测试宿主和 `commit_worker`。门禁比较未改。

`conflict_acceptance_host.ts` 的 `createThread` 把 `sessionFacts` 返回的同一个对象写入 `worker-creations.jsonl`，并带上 `attempt` 以便按 attempt 查找。`cli_version` 仍是 `controlled-conflict-runtime`，`model` 与 `effort` 仍取任务卡 executor。`id` 仍是 `attempt.thread_id`。

`test_worktree_lifecycle_e2e.py` 的 `launch_record` 只取 `attempt` 字段等于该 `attempt_id` 的一行。若 `attempt.delivery` 已经存在，则核对 `launch_id`/`id`、`cli`/`cli_version`、`model`、`effort`，不一致就抛错。`commit_worker` 用这一行写 `A2A-Tool`、`A2A-Model`、`A2A-Effort`、`A2A-Launch`。`foreign=True` 仍只把 `A2A-Task` 写成 `foreign-task`。`A2A-Native-Session` 仍是 `attempt['thread_id']`。

提交发生在 submit 把记录抄进 `attempt.delivery` 之前，所以提交时读的是宿主 jsonl；delivery 出现后与同一行核对。

### 绿态

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

### 清点与回归

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

### 基线上的既有失败

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

### 地图状态

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
