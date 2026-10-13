# run driver等待审查就绪修复

状态：**INCOMPLETE（完整run待跑）**。05已通过来源反事实、两个候选场景、coop8和recovery9；run第一项在fixture读取中间状态时error，后续未运行。05原证据保留。

## 诊断依据

同一review在事件71（20:56:08.972Z）为requested，事件76（20:56:09.447Z）为running，间隔475毫秒。期间已有pane_started和dispatch_queued。最终保存的task仍reviewing、review running且launch/runtime_identity齐备。没有“创建没调用”或锁/队列卡住的迹象。

`requestReview()`先保存意图，然后await worktree、diff、窗格创建与身份观察，最后保存review_started。run在后台独立执行这些步骤，driver的status查询可以读到中间的reviewing/requested；同步verify命令返回成功时则已经完成上述await。

旧`finalize_run()`只见task.state=reviewing就退出等待，随后complete_review读到requested而拒绝。这是fixture就绪条件太早，不是产品创建缺陷。

## 最小修复及边界

仍用原12秒期限，但状态查询本身也受剩余时间限制，查询前后均核对deadline。等待期间固定原attempt/C；第一次看到review后固定review_id。仅review=running且launch/runtime_identity齐备才调用complete_review；repair、失败/unknown、换绑定或超时立即失败。不把requested当通过、不重试创建、不补新review、不改产品或断言。

`QualityDriver.command()`增加可选timeout（其他调用仍默认45秒），调用前保存command-intent；超时直接抛出，保留未完成调用意图，不重试。增加的都是fixture日志，不进产品事件表。

## 相关路径静态核对

| method／调用点 | 路径与此次等待 |
| --- | --- |
| `test_run_entry_point_completes_registered_task` | submit后run异步verify，driver须跨过requested窗口；仍绑定原attempt/C，原8秒run期限不改 |
| `test_transient_tool_activity_keeps_same_thread_owner` | 调用上面主正例；helper-joins只改变外部观察附加项，同样使用新就绪等待，不放宽原身份断言 |
| `test_concurrent_duplicate_run_has_one_prompt_and_one_attempt` | 只驱动first handle的原attempt；第二个run仍被拒；等待同一个review，不能接管新attempt |
| `test_matching_reclaim_guard_is_idempotent_after_automatic_success` | 先经新等待完成review/评分，再取原run结果；之后的两次reclaim重放断言不变 |
| `test_fixture_existing_dispatch_submit_oracle_integration_and_reclaim` | 手工dispatch→同步verify；adapter收到成功响应后才驱动review，成功响应已越过创建await；不改为盲等、不增加自动run |
| `MultiTurn.test_run_after_receipt_turn` | 同一finalize_run调用；新等待也覆盖requested窗口，delivery-A/receipt-B和原身份断言不变 |

其余7个run反例不调用finalize driver，保持原流程。complete_review的running/身份/结论校验与Recovery收据去重不变。

## 离线复放

`offline-01/run.json`为PASS。使用保存的requested/running快照及虚拟时钟，旧finalize方法在requested就调用审查动作；新方法等到running才发出review/integrate回调。另验证paused、unknown、换attempt/C/reviewer、缺运行身份、一直requested超时均没有后续动作。

此probe仅测试fixture控制流：status来自保存快照，review/integrate只是被观察的回调；没有后台、socket、Git写入或真实模型，不构成产品验收。原文件为`legacy_quality_driver.py.before`，精确diff在`offline-01/fixture-fix.diff`。

再生成命令（换新输出目录）：

```sh
python3 -B evidence/2026-10-11-batch13/T-076/card-2/run-review-wait-repair-01/replay.py --output evidence/2026-10-11-batch13/T-076/card-2/run-review-wait-repair-01/offline-02
```

完整run及后续检查待legacy-green-06。真实仍0/8，不覆盖05。
