# T-037：18 项边界差异（2026-10-07）

原文件 `acceptance/test_run_e2e.py` 未修改。副本为 `test_run_native_e2e.py`，完整差异为 `run-boundary-copy.diff`。原业务 oracle、候选输入、Git/SQLite 回读、task/attempt/fence、状态、退出码和错误预期均保留。这里的原生 thread 服务是隔离替身，不证明真实 provider 或模型成功。

## 公共边界

| 原边界 | 新边界 | 影响与限制 |
| --- | --- | --- |
| Muster pane、agent、进程信息命令 | 外部受控 thread 服务；所有请求与原始返回追加到 boundary.jsonl | 不调用 Herdr/Muster，不启动模型；生产核心不含替身或故障开关 |
| terminal/shell/前台领导者/cwd | 由核心创建的 thread_id、turn_id、worktree | 辅助活动不更换身份；换 turn 或 worktree 必须暂停。真实 ProviderService 的 cwd/turn 回读另由 native-service-check.ts 核对 |
| parent-pane 与 agent name CLI 参数 | 显式 runtime-mode=approval-required；原 run 名称只用于夹具调度 | 不把界面焦点或名称当运行身份；父 thread 与无关 thread 仍逐字段核对不变 |
| create 不带 project | 证据转接器给隔离 task 分配同名 project | 生产 create 的显式 project 校验不删；额外真实 engine 探针用独立 literal-project |
| worker 在 state root 写 CLI submit | 受管 thread 经真实 a2a_submit handler，替身只提供活跃 turn 身份；独立 claim 仍走原 CLI | 不直接写产品 SQLite，不从实现取预期；MCP 认证/provider 活跃状态是替身边界，真实模型留给 T-039 |
| Codex `--add-dir` 只含 state root 的 argv 断言 | 原生服务的 worktree 环境、所属 workspace、集成头断言 | 这是运行时配置断言的移植，不宣称旧 argv 或真实沙箱/Git 权限已经验证；原生模型、effort、fastMode 在真实 engine 的服务配置中另查 |
| close pane 并确认不在 live 清单 | stop 后确认、archive 后确认，并从 live thread 清单移出；归档记录保留 | 只回收绑定 thread；worktree、历史与未提交 commit 继续保留 |

## 逐项映射

| 项 | 原验收方法 | 新边界变化；业务预期 |
| --- | --- | --- |
| 1 | run_entry_point_completes_registered_task | worktree 配置代替 CLI add-dir；显式 submit、真实新 commit 集成、原分支不变、oracle 新输入、仅回收自己不变 |
| 2 | transient_shell_member_keeps_same_agent_owner | 同 turn 的临时工具活动代替同前台组辅助 shell；仍必须正常完成 |
| 3 | new_foreground_leader_is_not_owned_even_with_old_pid_present | 原 thread 仍在而 turn 更换；仍拒绝验收、集成与错误回收 |
| 4 | verify_expected_attempt_uses_real_gate | 无业务或预期变化；真实 CLI/Git/oracle |
| 5 | integrate_expected_attempt_uses_real_git_gate | 无业务或预期变化；首次真实引用与 reflog 更新 |
| 6 | fixture_existing_dispatch_submit_oracle_integration_and_reclaim | 原生 dispatch 与 MCP submit；done 不接受、一次 oracle、仅回收自己的预期不变 |
| 7 | done_without_submit_hits_deadline_and_cannot_accept_committed_candidate | thread 空闲且已有真实 commit；输入期限仍为 2 秒，必须 run_deadline、零 oracle、引用/reflog 不变 |
| 8 | concurrent_duplicate_run_has_one_prompt_and_one_attempt | first run 与重复请求的 wait 输入 8→30 秒；第二次仍须 3 秒内 run_busy、一个 attempt/一个 prompt、第一执行者可完成 |
| 9 | invalid_wait_values_have_no_worker_or_business_side_effect | 原输入 0/-1/1.5/true/not-a-number/空值保留；无 run 收据、无创建/投递、业务/Git 不变 |
| 10 | replacement_attempt_is_not_verified_integrated_or_closed_by_old_run | old run 的 wait 输入 10→30 秒；外部观察屏障 12→60 秒；仍须 run_superseded，不能验收、集成或回收 replacement，只能清理历史自己 |
| 11 | oracle_failure_is_not_success_and_reclaims_only_owned_pane | 原生 thread 收尾；独立 oracle 的真实非零、引用不变、仅回收自己不变 |
| 12 | startup_blocked_preserves_scene_without_prompt_or_close | thread 服务在创建后报告 pending approval；仍零 prompt、零回收、保留现场 |
| 13 | post_prompt_blocked_preserves_scene_without_answer_or_reprompt | thread 服务报告 pending approval；仍一个 prompt、零自动回答/重投递/回收 |
| 14 | unknown_identity_cannot_succeed_or_close_replaced_terminal | worktree 身份更换代替 terminal 更换；仍零 oracle、一个 prompt、保留未知对象 |
| 15 | stale_verify_integrate_guards_preserve_current_and_accepted_state | 无业务预期变化；stale_attempt、状态/Git/历史不变、accepted 幂等仍检查归属 |
| 16 | reclaim_guard_targets_history_and_rejects_foreign_and_unknown_attempt | 历史 thread 停止/归档；foreign/current 仍存活，历史重放与跨任务拒绝不变 |
| 17 | matching_reclaim_guard_is_idempotent_after_automatic_success | 已归档自己的 thread；幂等重放不额外 stop/archive，状态/Git 不变 |
| 18 | attempt_guards_preserve_existing_live_operation_lock | 无业务预期变化；活跃 oracle 期间 verify/integrate 仍 operation_busy，零第二 oracle |

## 时间输入与实测

时间改动经 `controller-decision-02.md` 批准；最终只保留上述第 8、10 项的改动。第 1、2、11、17 项的 8 秒输入恢复原值。成功预算增加不改变 submit 要求；no-submit 的 2 秒期限、重复请求的 3 秒拒绝、业务状态/引用/副作用断言保持原值。独立审查须复核。

`run-candidate-03` 保留两个原始失败。`timing-observations.json` 从原始 boundary 与 CLI trace 回读：第 8 项 prompt 响应结束→submit 发起为 8.020 秒，→submit 完成为 9.628 秒；CLI run 启动→submit 完成为 11.363 秒。因此原 8 秒输入不足以容纳这次独立核对。这个约 11 秒观察不构成新旧路径的性能结论。T-039 应另外核对真实模型路径。

第 10 项的替身明确记录 `Observation barrier expired`，原屏障在 12 秒到期。该轮 replacement submit 命令从 `03:42:08.694064` 到 `03:42:23.363928 UTC`，单次耗时 14.670 秒；原 run prompt 响应结束→replacement submit 完成为 60.287 秒。记录中 cleanup 会重写 release 文件，`timing-observations.json` 的 release mtime 间隔只作为支持材料，不能当第一次人工释放的精确时刻。原屏障失败原样保留；30/60 秒输入需以当前候选的实际通过和副作用断言证明，不能以预算增加自行宣称通过。

`run-candidate-04` 是探索轮：两个目标场景通过，但首项在 5 秒 prompt 观察窗口未到边界；同轮源文件仍在迭代，不能作冻结候选的通过结论。未放宽这个 5 秒观察窗口。原 30 秒核心测试超时也保留，后续顺序执行复核，不把超时改成业务通过。
