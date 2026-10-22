# T-124 候选 2 验收结果（2026-10-22）

结论：各验收项都有真实入口的绿态，以及失败在预期检查点的反例。独立审查（agy）待做，整票暂记 **INCOMPLETE**。

候选 2 做了三件事：
- 落实用户 2026-10-22 的四条裁定：“1.a  2 放宽 3 也要支持一下 cluade 和 codex 的额度监控 4.这个要解决”。
- 修复候选 1 审查（`../review-02.md`）的四条发现。
- 把原生提问一条的验收改写为“受管会话拿不到原生提问工具”。

## 场景

沿用 `workbench/tests/test_t124_controller_e2e.py`（候选 1 的场景见 `../RESULTS.md`），新增变体：

| 选项 | 内容 |
| --- | --- |
| `--controller-cli codex` | 主控是 Codex：会话环境为 `CODEX_THREAD_ID`、`CODEX_HOME`，额度记录用 Codex 0.163 的日志格式 |
| `--end restart-working` | worker 等待回答时重启编排后台：run 先经门禁回收，再重新派发，做到集成；monitor 恢复 |
| `--end restart-verified` | 审查通过后重启：run 接着验收并集成，monitor 恢复 |
| `--gui` | 用同一份源码构建真实工作台窗口，读窗口文字核对额度通知的出现与消失，并截图 |

所有变体都新增了这几项核对：
- 额度日志里一行写坏只记录一次，后面的行照读；
- worker 和 reviewer 发给模型的工具列表里没有 AskUserQuestion；
- monitor 经门禁回收。

## 结果

命令：在 `workbench/` 下运行 `evidence/2026-10-22-batch20/T-124/candidate-2/e2e/commands.sh <组名>`。依次跑了 green1 green2 green3 red1～red7，之后补跑 codex2、red8、red9，退出码见 `e2e/exits.txt`。

### 绿态

| 运行 | 结果 |
| --- | --- |
| green-01-release | PASS，25 项 |
| green-01-release-02（加入 `worker_offered_no_native_question` 后重跑） | PASS，26 项 |
| green-02-quota | PASS，23 项 |
| green-03-codex-monitor-02 | PASS，25 项 |
| green-04-restart-working | PASS，18 项 |
| green-05-restart-verified | PASS，25 项 |
| green-06-restart-working-codex-monitor-02 | PASS，18 项 |
| green-07-codex-controller-gui | PASS，27 项 |
| green-08-codex-controller-quota | PASS，23 项 |
| green-09-claude-controller-gui | PASS，27 项 |

restart-working 的项数比较少：重启时 worker 正在等待回答，主控回答和界面回答这两段在这个变体里不核对。release 后新工作被拒，只在走 release 结尾的 green-01、03、07、09 里核对。

green-04 的 run 记录了 `resumed: [{phase: "waiting_submit", task_state: "claimed", redispatched_from: <原 attempt>}]`。原 attempt 和新 attempt 都经门禁回收。

窗口截图在 `e2e/screens/`：Codex 主控是 green-07，Claude Code 主控是 green-09，每个都有通知出现和消失两张。两张通知图都显示“主控额度用完 · demo · 执行主控 · 已派出的工作继续 · 约 HH:MM 恢复”。图中的 HH:MM 来自测试写入日志的重置时间，按本机时区换算。

其他绿态是在加入 `worker_offered_no_native_question` 之前跑的。它们最后的 `managed_sessions_offer_no_native_question` 都通过了，而 worker 的工具集合只增不减，所以提前做的这次核对必然也通过。

### 反例

| 运行 | 停在 |
| --- | --- |
| red-01-parent（`--revision b25d44045`） | 超时：额度用完通知 |
| mutant-01-answer-as-user | `controller_answer_recorded_as_controller`：`from: user` |
| mutant-02-run-waits-for-score | `run_integrates_after_role_ends`：停在 verified |
| mutant-03-run-ignores-active | `run_waits_for_active_controller_score` |
| mutant-04-unscored-without-reason | `integration_recorded_unscored` |
| mutant-05-quota-unread | 超时：额度用完通知 |
| mutant-06-monitor-writable | `monitor_launch_recorded_read_only` |
| mutant-07-issue-provider-codex | 超时：第一个问题 |
| mutant-08-snapshot-denies-privileged | 超时：审查通过（run 停在 `run_external_unknown`，`proc_pidinfo_failed_or_short` errno 1） |
| mutant-09-codex-monitor-unbound-02 | `restore_cli_unsupported` |
| mutant-10-reclaim-monitor-repo | `monitor_reclaimed`：`identity_conflict` |
| mutant-11-quota-stops-at-bad-line | 超时：额度用完通知（坏行后面的记录没读到） |
| mutant-12-runs-not-resumed | 超时：续跑的 run 结束 |
| mutant-13-gone-not-registered | `previous_worker_confirmed_gone` |
| mutant-14-monitor-not-restored | `monitor_restored_after_restart` |
| mutant-15-resume-without-redispatch | 超时：重新派出的 worker 再次提问 |
| mutant-16-worker-asks-natively-03 | `worker_offered_no_native_question`：`['AskUserQuestion']` |
| mutant-17-codex-reset-unread-02 | `quota_exhausted_noticed`：`resets_at: null` |
| mutant-18-notice-not-rendered（`--gui`） | 超时：窗口里的额度通知 |

### 不作数的运行

这些运行的结果都保留，但不作为证据使用：

- `e2e/aborted-01-enospc/`：磁盘满（数据卷剩 165 MB）时中断的一轮，说明见该目录的 README.txt。
- green-03-codex-monitor、green-06-restart-working-codex-monitor、mutant-09-codex-monitor-unbound：跑的时候用户的 Codex 安装（`~/.codex/packages`）已被删除，三个都在 `attach` 报 ENOENT。mutant-09 的失败因此不算红态。07:23 用官方脚本装回 Codex 0.163.0 后，三个都以 `-02` 重跑。
- mutant-16-worker-asks-natively：这一版变异去掉了所有 Claude Code 会话的参数，被门禁的 reviewer 启动边界（`review_launch_boundary`）拒绝，没有走到工具列表那条检查。
- mutant-16-worker-asks-natively-02：只对 worker 去掉参数后，门禁在审查时核对 worker 的 argv，仍然先拒绝。worker 工具列表的核对因此提前到 worker 第一次提问之后，-03 停在这条检查上。两次被门禁拒绝都是真实拦截，只是证明的是门禁边界，不是 e2e 检查本身。
- mutant-17-codex-reset-unread：变异把赋值整行删掉，`if (...)` 后面直接跟了 `const`，后台因 TypeScript 语法错误没能启动，不是红态。-02 改为保留赋值形式。

### 单元证据

`unit/commands.sh`，退出码见 `unit/exits.txt`：

- `test_t093_process_snapshot.py`：新代码 PASS（31 项）。三个反例都按预期失败：
  - 28a0550cc 的 `processSnapshot.py`：没有 `settled_snapshot`；
  - 根进程变化也重试的变异：`root_changes` 重试到第 3 次；
  - 重试时复用同一个读取器的变异：`child_changes_once` 第 1 次就失败。
- `test_t124_quota_notice.mjs`：PASS（6 项）。
- `test_t096_restore.mjs`：PASS（23 项）。panes.ts 的恢复逻辑挪进了 `restore()`，变异的定位串随之改成 `native`。拿 28a0550cc 的 panes.ts 跑会失败，原因是新的定位串在旧代码里找不到，失败的是测试本身，不算红态。
- `test_t121_role_request_e2e.py`：PASS（49 项）。

回归（同一工作树，开发期运行）：
- 通过：T-122 e2e（23 项）、T-127 e2e（19 项）、t110_snapshot、t112_execution、test_t096_daemon_restart、test_t096_restart_cleanup、test_t096_process_probe。
- 没跑：`test_t096_process_tree.py` 要求把原始输出写到外置盘。

## 验收项

| 验收项 | 状态 | 依据 |
| --- | --- | --- |
| 终端主控回答 worker 的问题，记为主控的回答，`user_inputs` 不增 | PASS | green-01、02、03、05、07、08、09；mutant-01 |
| 界面回答仍记为用户输入 | PASS | green-01、02、03、05、07、08、09 |
| `run` 中途 release 并关闭终端，任务经门禁做到集成，并记录发起者身份已结束 | PASS | green-01；mutant-02、04 |
| 身份结束后，这个终端的 `run`、`attach`、派发被拒并留记录 | PASS | green-01、03、07、09 `new_work_refused_after_release` |
| 额度用完时工作台内出现通知，worker 不受影响 | PASS | green-02、08；quota-notice 单元；mutant-05、11 |
| 两种主控的额度通知都在真实应用窗口里核对 | PASS | green-07、09 与截图；mutant-17、18 |
| （裁定 1）受管会话拿不到原生提问工具 | PASS | green 各运行；mutant-16-03 |
| 非主控窗格仍出现的原生提问记 `native_question_ignored`、不登记为等主控回答 | 无直接证据 | 工具已不提供，脚本化 worker 不会走到这条路径；只有代码 |
| （裁定 2）非根进程的瞬时身份变化不让 run 停下，根进程变化仍拒绝 | PASS | t093 单元及其三个反例 |
| （裁定 4）后台在 run 进行中重启：run 接着跑到集成，monitor 恢复 | PASS | green-04、05、06；mutant-12、13、14、15 |
| 身份结束后 run 自己集成，记为未评分；主控在时仍等主控 | PASS | green-01、02；mutant-03 |
| `attach` 的 monitor 只读，身份结束后照常运行，可经门禁回收 | PASS | green 各运行；mutant-06、09-02、10 |
| 修改前的版本跑同一场景失败 | PASS | red-01 |
| `project_map.py status` 0 问题 | PASS | 提交前运行 |

## 已知限制

- 进程快照偶发“身份变化”的根因仍未确认。按裁定 2 放宽之后，候选 2 的运行里没有再出现。
- 工作台界面还没有回答 issue 的面板；用管理凭据调用 `answer_issue` 可以回答。
- 下列测试在 HEAD 上就已经失败，与本票无关，本票没有处理：t091_pane_ipc、t107_sidebar、t108_questions、t093_process_diagnostics、pane_dispatch_state、conflict_panes、t107_daemon_readonly。

夹具目录已归档到外置盘，清单见 `fixtures.archive.json`；候选 1 的夹具清单见 `../fixtures.archive.json`。
