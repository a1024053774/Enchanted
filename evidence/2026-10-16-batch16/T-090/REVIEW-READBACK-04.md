# green-regression-04：审查超时与门禁拒收码只读核对

2026-10-16。整体 INCOMPLETE。候选 `8c971b99d46094bc3e9cb3f0bf772de6f6ab3f4a`，recovery 原 9 方法为 7 方法通过、2 方法各产生正文及清理 error，共 4 errors、0 failures、0 skip。ready、focused、coop 8 已通过；编排 18、CAS、cards、worker/T-082 及变异阶段未执行。

原件 `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/green-regression-04/recovery/`。只读取已保存 readbacks、run.json、fixtures.tar.gz；没有打开停机 SQLite、重跑或更改任何产品、验收、期限、driver 或重试逻辑。

## 关键结论

两个用例的保存事件均没有 `review_lifecycle_failed`、`review_worker_workspace_changed`、`review_protocol_failed`、`rejected` 或其他门禁拒收记录。after-CAS 已实际通过 worker 快照比较并最终完成回收；before-CAS 在读回时仍 running，尚未进入结束核对。因此本轮不满足“出现 worker 边界拒收则停止”的条件，不能仅凭相同的 driver 超时报错归为原 T-090 缺陷复发。

## after-CAS：回收晚于 driver 的观察期限

`test_after_CAS_recovers_bookkeeping_without_Git_write`：task `check-639edc6787b04cdea061f679e8914422`，读回截止 17:07:08.631490Z。

- review_requested seq 97（17:06:50.670Z）绑定 HEAD=`4ef0121cda58f4f2fc956feb3331e1f4c941422a`、原受管分支、status 为空。
- review_result seq 104（17:07:01.101Z）入库；review_reclaim_intent seq 105（17:07:01.165Z）。
- 结束核对的 worker HEAD、分支、status 分别在 17:07:03.812Z、17:07:04.163Z、17:07:04.473Z 返回 0，值与快照相同且干净；随后 candidate copy 清理已完成。
- driver 最后一次 events 的服务端结果在 17:07:06.853Z 返回，其原始响应里尚无 review_reclaimed；当时最后事件是审查 worktree 登记核对的 command_intent。
- 后台在 17:07:07.160Z 写 review_reclaimed（seq 138），比该次服务端 events 结果晚 0.307 秒。截止读回 task=verified、review=passed，完整回收事件存在。

原 driver 的 8 秒期限由 pane_release 后设定，先等 reviewer 输入，再发送 signal、轮询回收，共用该期限；pane_release 服务端结果在 17:06:58.067Z，最后 events 结果在 17:07:06.853Z。客户端准确起算时刻未单独打点，但实际异常与最后响应均已保存，证明 driver 的观察先结束、后台随后完成，并非 worker 快照拒收。

清理阶段再次调用 complete 时，原 follow-up 标记仍为 started，故 adapter 以 `Review follow-up changed or remains incomplete; do not repeat it.` 拒绝重复驱动。这条是测试工具的防重复 error，不是门禁报告绑定变化，更不是新的审查拒绝；本轮不改这个保护。

## before-CAS：原件与转述不同，先发生 verify 客户端超时

`test_before_CAS_recovers_same_intent_once`：task `check-ce7f4914af2846c2821526b0a15993b2`，读回截止 17:08:03.719514Z。

该方法正文的原错误不是 `Reviewer result/reclaim did not complete`：它在原 complete 的 12 秒期限内未等到 verify 子进程退出，尚未调用 reviewer driver。服务端 verify 从 17:07:40.622Z 处理到 17:08:00.294Z 后返回 ok=true。

review_requested seq 97（17:07:57.937Z）已绑定 HEAD=`d3df5c31f2a8ee75295821e70da1e3a570389fad`、原受管分支、空 status；review_started seq 103（17:08:00.285Z）。读回 task=reviewing、review=running；没有 reviewer signal、review_result、review_reclaim_intent 或结束核对。该条不能补称结束核对已通过，也没有证据支持结束核对拒绝。

清理的第二个 error 来自原 3 秒 CLI 等待及后续身份核对：ps 已看到 PID 44751 为 `<defunct>`，无法再次确认活的 CLI argv，于是在发信号前拒绝处理；artifact 的 signals 为空。它不是门禁拒收码，亦不能转述成该方法的 review follow-up error。两条 CAS 恢复方法本轮都尚在 setup_candidate 阶段，没有进行预定 CAS 故障注入。

两个 daemon 的 stderr 均为空，均已确认正常退出 0（PID 42674、44111）；未观察到后台崩溃导致本轮失败。

## 负载记录与结论边界

主控 #15／#9 报告的每分钟 1 分钟负载：本地 13:03 为 6.57，13:07 为 33.44，13:09 为 42.83，13:11 为 13.40，期间由用户其他项目推高。按当前 America/New_York 时区，审查延迟发生在约本地 13:06～13:08，处于该次负载升高窗口；不能因启动样本较低就称整轮处于低负载。

本轮按所给负载记录，归为时间窗口内未及时观察到完成的现象，不作为 T-090 worker 边界修复不完整的证据；具体负载因果和耗时贡献没有单独测量。负载原始日志由主控另行放入证据，当前仅保存明确来源的转述 `load-report-04.json`，不补造原始 stdout 或采样精度。

原 4 errors 与整体 INCOMPLETE 均保留；未提出或执行下一轮自动重试。主控决定后续稳定负载安排、完整回归和独立审查。本轮仅提交只读核对记录，不能代替验收通过。
