# T-081 结果

## 第 7 项结论

用户决定（answer `20261015T044138Z-ideation-answer-001`，2026-10-15，会话「a2a-构思主控」，逐字）：「记为已知行为，不改 (Recommended)」。选项原文：「生产布局下 worker 碰不到主分支；钩子是我方脚本，路径也不在 worker 可写处。T-081 结果里写明结论和未覆盖项（objects 未逐字节清点、pre-commit 钩子在 --no-verify 下未测），然后合并。」按该决定，CAS 重验行为不改。6e 不在本节，等 T-084 合入后再派。

### run-04 是 /tmp 夹具的误报

run-04 观察到 worker 移动共享分支并 push：两条命令各一次 exit 0，共享 `refs/heads/main` 从 G 到 T，本地裸仓库出现 `t081-probe`。夹具在 `/private/tmp/t081-capability-01/run-04/`，见 [capability-run-04/actual-command-results.json](capability-run-04/actual-command-results.json)。`workspace-write` 默认可写 `/tmp`，所以这次成功不能当成生产布局下 worker 碰得到主分支。

生产布局复测在外置盘夹具上，原件 [CAPABILITY-RECHECK-03/run.json](CAPABILITY-RECHECK-03/run.json)（[CAPABILITY-RECHECK.md](CAPABILITY-RECHECK.md) A 节）。同一 `codex sandbox --permission-profile :workspace`：`git update-ref` exit 128（`main.lock`：Operation not permitted），`git push` exit 1（不能创建临时对象目录，远端拒绝 unpacker error）。读回 `main` 仍为 G，裸仓库没有 `t081-probe`。对照夹具 `/tmp/t081-capability-recheck-02` 上两条都是 exit 0，`main` 变为 T，裸仓库新增 `t081-probe`。

### 沙箱外 git commit 的实际范围

要点来自 [COMMIT-SCOPE.md](COMMIT-SCOPE.md)，原件 [commit-scope-run-01/run.json](commit-scope-run-01/run.json)。夹具在外置盘。19 步都是 `MEASURED`，没有模型回合。

`prefix_rule` 判为 `allow` 的 `git commit`，包括其后的 `--template`、`-F`、`--fixup`、`--amend`、`--no-verify`、`--trailer`、`--cleanup`，在沙箱外、cwd 为检出 `main` 的 worker worktree 时 exit 0，并推进共享 `refs/heads/main`。基线 `post-commit` 调用的 `git update-ref refs/heads/hook-side` 也成功。这些命令没有改 `packed-refs`、`config`（含 `core.hooksPath` 与 `include.path`）、钩子脚本、他人分支 `other`、`packed-keep`，以及另一个 worktree 的 `.git/worktrees/<name>/`。

不匹配 allow 的 argv 在 `codex sandbox --permission-profile :workspace` 里运行：`commit` 前的 `-c`、`--git-dir`、`--work-tree`、`-C`，以及 `GIT_DIR`、`GIT_WORK_TREE`、`GIT_INDEX_FILE`、`GIT_CONFIG_PARAMETERS`、`GIT_CONFIG_COUNT`/`KEY`/`VALUE` 的 shell 前缀。它们在创建 `index.lock` 时得到 Operation not permitted，exit 128，指定读回与命令前相同。`git config core.hooksPath` exit 255，不能锁定 `config`，随后那条 allow 的 `git commit` 仍走原来的钩子目录。

生产启动把 `core.hooksPath` 指到编排方自己的目录，不在 worker worktree 里：

- [`workbench/src/panes.ts:172`](../../../../workbench/src/panes.ts:172) 对非审查会话设置 `GIT_CONFIG_COUNT=1`、`GIT_CONFIG_KEY_0=core.hooksPath`，`GIT_CONFIG_VALUE_0` 为 `fileURLToPath(new URL("../hooks/", import.meta.url))`，即本仓库 `workbench/hooks/`。
- [`scripts/launch-worker:46`](../../../../scripts/launch-worker:46) 取 `scripts/git-hooks`，[`scripts/launch-worker:90`](../../../../scripts/launch-worker:90) 把它写入 `GIT_CONFIG_VALUE_0`。

### CAS 外部移动

[CAPABILITY-RECHECK.md](CAPABILITY-RECHECK.md) C 节的代码事实：门禁第一次发现工作分支已经移动时不立即拒绝。它清除集成意图，重新验收并重新审查；前三次 miss 重验，第四次进入 `paused`。若重验与审查通过，被移入的提交可以作为新 G 的祖先留在工作分支上，并且不出现在审查 diff（`attempt.base_commit..C`）里。用户决定这条行为不改。

### 未覆盖项

- `objects/` 未逐字节清点。`rev-parse` 能解析新提交，只说明引用指向它。
- `--no-verify` 下的 `pre-commit` 与 `commit-msg` 未测。commit-scope 夹具只装了 `post-commit`，该钩子在 `--no-verify` 下仍然运行。本机 `git commit -h` 写明 `--no-verify` 绕过的是 `pre-commit` 和 `commit-msg`。
- [`panes.ts:160`](../../../../workbench/src/panes.ts:160) 的三个动态 `-c`（`hooks.UserPromptSubmit`、`hooks.Stop`、`hooks.PermissionRequest`）未进入这次沙箱包装。

### 注意事项

测试夹具不要放在 `/tmp` 或 `$TMPDIR`。`workspace-write` 默认可写这些位置，沙箱拒绝会被测成允许。

## 6e 尾注身份

状态：INCOMPLETE。6e 五案、6a 与三个正例已在真实门禁入口跑完，误拒绝为 0。T-077 生命周期冲突有两案被现行门禁拒收，整项回归因此不能记通过。未改 `workbench/src/gates/core.ts`，未 commit，未 push。

### 变基

矩阵跑在 `193ffa6e69f139b71361e88b541602685ce0faaa`。变基后的 HEAD 是 `bd6085b97d9f8f1a641fad7da1889c83631a0d66`，变基当时的 main 是 `1275f18349862fe44f923025fde9eb2e4dc7bab3`。从矩阵到这次变基，main 上多出的 `0b31611a` 与 `1275f183` 只改 `evidence/2026-10-11-batch13/T-078/controller-decision-04.md`。收尾时 main 为 `b00b9d57ea91143fec0dc4528bbb5e73153b3d98`，中间还有 `e7c57f7e` 与 `47c955df`，三条都只改同一份 T-078 证据。没有为这三条再变基，回归记录钉在 `bd6085b9`。`git diff main -- workbench/src workbench/hooks` 在变基当时和收尾时都为空。产品状态记为 MATCHES_MAIN。

### 矩阵

原件 [6e-full-02/run.json](6e-full-02/run.json)。HEAD `193ffa6e69f139b71361e88b541602685ce0faaa`，`real_codex_turns` 0，`false_rejections` 0，`positive_cases_executed` 4。套件总状态 INCOMPLETE，因为停在当时的 `t075-recovery`。更早的 [6e-full-01](6e-full-01) 停在旧的 `trailer_partial` 红态，保留，不作为本结论。

绿态实际拒收码与红态（变异体在该次套件的 `/tmp` 副本里，删掉对应比较后 `reply.ok` 为 true，状态 `reviewing`）：

| 案例 | 绿态拒收码 | 红态 |
| --- | --- | --- |
| trailer_launch | trailer_identity_mismatch | BW-REJECT-trailer_launch |
| trailer_tool | trailer_identity_mismatch | BW-REJECT-trailer_tool |
| trailer_model | trailer_identity_mismatch | BW-REJECT-trailer_model |
| trailer_effort | trailer_identity_mismatch | BW-REJECT-trailer_effort |
| trailer_no_launch | trailer_launch_record_missing | BW-REJECT-trailer_no_launch |

无启动记录那案只有一条 `trailer_check`：`passed` false，`error` `trailer_launch_record_missing`，`reason` `缺启动记录`。五案绿态工作分支未动，任务状态 `submitted`。

6a（`trailer_absent`）`intervention_count` 1，集成状态 `accepted`。`positive_single`、`positive_multi`、`positive_red_card` 均为 `accepted`。

### 恢复与 T-075

套件内恢复两次都是同一超时，单独重跑都通过。错误文本是 `FixtureError: Released external wrapper did not finish`（`wait_done` 的 12 秒期限，after-CAS 三案）。记录里没有 `review_launch_config_required`。

| 目录 | revision | 结果 |
| --- | --- | --- |
| 6e-full-02/t075-recovery | 193ffa6e69f139b71361e88b541602685ce0faaa | INCOMPLETE，tests_run 9，failures 0，errors 3 |
| 6e-recovery-rerun-01 | 同上 | PASS，tests_run 9，failures 0，errors 0，skipped 0 |
| 6e-regress-rest-01/t075-coop | bd6085b97d9f8f1a641fad7da1889c83631a0d66 | PASS，tests_run 8，failures 0，errors 0 |
| 6e-regress-rest-01/t075-recovery | 同上 | INCOMPLETE，tests_run 9，failures 0，errors 3 |
| 6e-recovery-rerun-02 | 同上 | PASS，tests_run 9，failures 0，errors 0，skipped 0 |

[6e-regress-rest-02](6e-regress-rest-02/run.json) 里 `t075-run` tests_run 18、`t075-cas` tests_run 1、`t075-cards` tests_run 15，三者 status PASS，failures 0，errors 0。`6e-full-02` 的 `t075-coop` 在旧 HEAD 上 `passed` true。

### T-077 生命周期冲突

[6e-regress-rest-02/t077-lifecycle-conflicts](6e-regress-rest-02/t077-lifecycle-conflicts/run.json) 状态 INCOMPLETE。25 案里 23 案 failures 0、errors 0。下面两案 failures 1，`verify` 返回 `ok` false、`error` `trailer_identity_mismatch`：

- `test_conflict_active_worker_reworks_and_integrates`，提交 `06d7186f3c06f7411198e1ddd213ce54892f4bcf`，尾注 Model `fixture`，Launch 与 Native-Session 同为 `f08aeb5e-af7c-4d1a-9594-ef4c2283b0c5`
- `test_conflict_ended_session_gets_new_attempt`，提交 `1d3163f8223cde55fa40c7deacd014d6765bbd33`，尾注 Model `fixture`，Launch 与 Native-Session 同为 `117759c2-48df-460a-93d8-84bdee5e70cd`

两案的目标断言 `CONFLICT-ACTIVE-WRITEBACK` 与 `CONFLICT-ENDED-NEW-ATTEMPT` 都是 `target_passed` true，分类为 `non_target_assertion_failure`。`commit_worker` 把 Model 写成 `fixture`，把 Launch 写成 `attempt['thread_id']`（`workbench/tests/test_worktree_lifecycle_e2e.py`）。这与 T-084 之后的核对不一致：受管 attempt 的 Launch、Tool、Model、Effort 要与启动记录一致，只有 Model 可以是字面量 `unknown`。

最小改法是只改这个夹具的对应尾注，使它们等于该 attempt 的启动记录，然后重跑这两案。门禁代码不动。本次没有改这个文件。

### 其余回归

[6e-regress-rest-03/run.json](6e-regress-rest-03/run.json)，HEAD `bd6085b97d9f8f1a641fad7da1889c83631a0d66`。下列步骤 status PASS，报告里的 `real_codex_turns` 为 0；`t076-score-schemas` 的 run.json 没有这个字段：

`t077-conflict-panes`，`t080-protected`，`t076-tracer`，`t076-controls`，`t076-red`，`t076-legacy-boundaries`，`t076-review-faults`，`t076-score-schemas`，`t077-review-worktrees`，`t077-joint`，`t077-relay-conflict`（tests_run 未单列，failures 0，errors 0），`t077-trailer-conflict`（tests_run 2，failures 0，errors 0），`t076-startup-shutdown`（tests_run 4），`t076-attachment`，`t075-multiturn-identity`（tests_run 4，failures 0，errors 0），`t081-cas-counterfactual`。

`t076-wide` 状态 INCOMPLETE。计划 15 案，14 案 outcome `passed`，`widen_score_after_cas` 为 `harness_error`：`HarnessFailure: Expected explicit fixture boundary was not reached: false`。`wait_for` 的期限是 5 秒，after-CAS 释放后没有看到 `.done.json`。单独重跑 [6e-wide-rerun-01/run.json](6e-wide-rerun-01/run.json)：status PASS，该案 outcome `passed`，`real_codex_turns` 0，`--source` 为仓库根。

同一次收尾的项目地图检查：Problems 0，Stale living docs 0。第 7 项结论不改，本节不重跑那项测量。

## T-086 合入后的重跑

状态：所要求的 6e、6a、三个正例和回归都有通过记录。HEAD `ca6730f13850d712ba561699d00463766f60a24f`，`e38b87cb1` 与当时的 main `1c183271f359762f217f3b9c4e9e87b74e22c2ec` 都是祖先。`git diff main -- workbench/src workbench/hooks` 为空。未改 `core.ts`，未 commit，未 push。`real_codex_turns` 为 0。6e 五案在变基前已经写在工作区里，变基后针位仍各只出现一次，本轮是在新 HEAD 上重跑。

### 矩阵

原件 [6e-rerun-01/run.json](6e-rerun-01/run.json)。套件进程状态 INCOMPLETE，停在 `t075-recovery`。矩阵本身：`false_rejections` 0，`positive_cases_executed` 4。

| 案例 | 绿态 | 红态 reply.ok |
| --- | --- | --- |
| trailer_launch | trailer_identity_mismatch，分支未动，submitted | true |
| trailer_tool | trailer_identity_mismatch，分支未动，submitted | true |
| trailer_model | trailer_identity_mismatch，分支未动，submitted | true |
| trailer_effort | trailer_identity_mismatch，分支未动，submitted | true |
| trailer_no_launch | trailer_launch_record_missing，一条 trailer_check，reason 缺启动记录，passed false | true |

6a `intervention_count` 1，状态 `accepted`。`positive_single`、`positive_multi`、`positive_red_card` 均为 `accepted`。`t075-coop` PASS，tests_run 8，failures 0，errors 0。

### 恢复与 wide 的套件内超时

[6e-rerun-01/t075-recovery](6e-rerun-01/t075-recovery/run.json)：INCOMPLETE，tests_run 9，failures 0，errors 3。三案都是 `FixtureError: Released external wrapper did not finish`。单独重跑 [6e-recovery-rerun-03/run.json](6e-recovery-rerun-03/run.json)：PASS，同一 revision，tests_run 9，failures 0，errors 0，skipped 0。

[6e-rerun-rest-01/t076-wide](6e-rerun-rest-01/t076-wide/run.json)：15 案里 14 案 `passed`，`widen_score_after_cas` 为 `harness_error`（5 秒内没有 `.done.json`）。单独重跑 [6e-wide-rerun-02/run.json](6e-wide-rerun-02/run.json)：status PASS，该案 outcome `passed`，`real_codex_turns` 0。

### 其余回归

[6e-rerun-rest-01/run.json](6e-rerun-rest-01/run.json)。`t075-run` tests_run 18，`t075-cas` tests_run 1，`t075-cards` tests_run 15，三者 PASS，failures 0，errors 0。

`t077-lifecycle-conflicts` status PASS，25 案 exit_code 都是 0，failures 0，errors 0。冲突七案的 `target_passed` 都是 true：

- `test_conflict_active_worker_reworks_and_integrates`
- `test_conflict_ended_session_gets_new_attempt`
- `test_conflict_unknown_session_preserves_scene_and_reports`
- `test_conflict_unknown_delivery_does_not_resend`
- `test_merge_command_error_is_not_text_conflict`
- `test_conflict_rework_still_rejects_forbidden_path`
- `test_conflict_rework_still_rejects_foreign_trailer`

同目录其余步骤 status PASS：`t077-conflict-panes`，`t080-protected`，`t076-tracer`，`t076-controls`，`t076-red`，`t076-legacy-boundaries`，`t076-review-faults`，`t076-score-schemas`（run.json 没有 `real_codex_turns`），`t077-review-worktrees`，`t077-joint`，`t077-relay-conflict`（failures 0，errors 0），`t077-trailer-conflict`（tests_run 2，failures 0，errors 0），`t076-startup-shutdown`（tests_run 4），`t076-attachment`，`t075-multiturn-identity`（tests_run 4，failures 0，errors 0），`t081-cas-counterfactual`。报告里有 `real_codex_turns` 的都是 0。

上一节记录的 T-077 两案失败留在 `6e-regress-rest-02`，那是 T-086 合入前的现场。第 7 项仍不改。
