# green-regression-03 编排四项失败的只读核对

2026-10-16。整体 INCOMPLETE，不把本轮回归称为通过。绑定候选 `e50c16f5cf6bce138c62634952cf381b2251f859`。ready 探针、focused、coop 8、recovery 9 通过；run/orchestration 18 为 14 通过、2 failures、2 errors、0 skip。CAS、cards、worker 边界、T-082 及变异阶段均未运行。

原件 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/green-regression-03/run/`。只读取既存 run.json、readbacks、commands/assertions/artifacts 的压缩 JSON 和 fixtures.tar.gz，不打开停机 SQLite，不修改任何夹具、产品、验收、时限或重试策略。

## 环境证据及限度

主控 #14／#8 报告运行结束时 `uptime` 负载均值为 13.81 / 30.52 / 25.81，机器 10 核，主要负载为用户其他项目 sitecraft-ai 的 tsc 与 next-build。记录见 `load-report-03.json`。这是主控提供的结束时样本，未提供精确采样时间或原始 stdout；不补称为 worker 逐用例测得的 CPU 轨迹，也不据此证明负载是唯一原因。没有操作这些其他项目进程。

## 四条现场

| 原方法 | 观察到的触发链 |
| --- | --- |
| `test_new_native_turn_is_not_owned_even_with_old_thread_present` | 5 秒 prompt 观察窗口先超时。cli_started=16:39:24.474733Z，隔离线程边界的 start 在 16:39:30.780145Z～30.782586Z 才执行成功，prompts_after=1，已晚于启动记录约 6.31 秒；之后 run 按该负例预设的 leader-changed 情景报 identity_conflict。该 identity_conflict 是夹具期望，不是一个额外的未知身份缺陷。原方法报的是等待 prompt 的 FixtureError，后续预期断言未完成。 |
| `test_oracle_failure_is_not_success_and_reclaims_only_owned_thread` | 同样在 5 秒 prompt 窗口超时。cli_started=16:39:48.345581Z，边界 start 在 16:39:55.207700Z～55.210577Z 才执行成功，prompts_after=1，约晚 6.86 秒。读回 task=claimed、candidate=null，没有 submitted、verification 或 review；坏候选／oracle 负例尚未真正执行。没有额外 oracle 或门禁拒绝被超时掩盖的证据。 |
| `test_matching_reclaim_guard_is_idempotent_after_automatic_success` | 本用例自己的 run `86758563-4f5e-482b-909f-7dc7719e2fb5` 以 wait_seconds=8 运行。waiting_submit 于 16:39:06.601Z 开始；review_reclaimed 于 16:39:13.384Z 完成；run 于 16:39:14.603Z 在 integrating 阶段记录 run_deadline，integrated 晚至 16:39:14.727Z（约迟 0.13 秒）。自动成功的前提已失效；之后第一次显式 reclaim 才真正回收并创建 attempt ref、删除 worker worktree，所以原“成功后的重放不得改变现场”比较出现连带 failure。第二次显式 reclaim 仍走幂等路径，未观察到独立的重复回收缺陷。 |
| `test_run_entry_point_completes_registered_task` | 这是另一份完全独立的 task/run，不受上一方法污染。自己的 run `03b9f7a1-4995-43ee-b4b8-3e24348789c1` 在 16:43:37.520Z 进入 waiting_submit，wait_seconds=8；16:43:45.523Z 在 reviewing 阶段以 run_deadline 结束。之后 review_result=16:43:46.465Z、review_reclaimed=16:43:48.368Z，driver 的显式 integrate 仍在 16:43:51.251Z 成功；此时 task accepted，但原 attempt reclaimed=false、cleanup=null。 |

上述时间均来自各自原件。cli_started 到边界 start 的差值是日志间隔，不冒充对 wait_prompt 入口的精确打点；实际原异常已明确是 5 秒观察窗口未看到 prompt。

## 缺失 attempt ref 的因果链

缺失的是 `refs/a2a/attempts/check-52e6c3c587c14666980ddcbe07c2a781/a1`，属于最后一条自己的 run。门禁 `run` 的 catch 逻辑在 run_deadline 且已有 review 时保留 worker，未进入自动 reclaim；`cleanupAttempt` 只在 worker 已 reclaimed 后保留该 ref 并清理目录。

该用例事件中没有 reclaim_intent、reclaimed、worktree_cleanup_intent、worktree_removed 或针对该 attempt ref 的 update-ref；没有 retention_ref_conflict、worktree_preserved 或 review_lifecycle_failed。读回明确 reclaimed=false，worker 仍保留。归档里的 Git ref 文件同时保留 main、worker 分支与 verification ref，三者都指向候选 `f20c1eb65ae81af84fa61a63d3614a6ad0e4e6c3`，但没有 attempt ref。因此这是本用例自己的 deadline 导致自动回收没有执行、ref 尚未创建的连带结果；不是已创建的 ref 被丢失，也不是前一个用例的 run_deadline 影响了它。

四个宿主 stderr 都为空，均已确认正常退出 0。独立线程、task、attempt 和 run 的身份不交叉。所有失败结果均原样保留，没有把清理阶段继续推进或之后显式集成补称为原 run 成功。

## 判断与下一步

四项均有可观察的短时限触发链，当前没有发现无法由时限拖慢解释的额外门禁／Git ref 缺陷；不触发“发现独立问题则停止”的分支。所报高负载与这些链路一致，但尚不能证明它是唯一原因，也未单独测量 T-090 快照检查对耗时的贡献。低负载下同一候选完整重跑是下一步判别，不能把环境解释当作验收通过。

主控沙箱外在负载低时执行，时限、用例和步骤全部不变：

```sh
python3 -B /Users/luckye/Documents/Code/a2a-wt-t090/evidence/2026-10-16-batch16/T-090/run-host.py --phase green --label green-regression-04 --archive-owned /private/tmp/t090-source-m1buaeqm
```

旧 -03 的运行夹具已归档并清理，只剩其内置盘 source checkout；已核对该目录存在。新命令先归档该源码现场，核对文件数与字节数后清理原件，所有旧外置盘证据保持原样。原始新输出为本票外置盘目录下 `green-regression-04/`，源码与变异仍只在 /tmp。没有修改脚本的执行顺序、失败判断或任何测试，只有用户明确要求的独立新 label 运行，不增加自动重试。
