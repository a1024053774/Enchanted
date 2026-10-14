# T-080 FINAL-03 交接（2026-10-14）

状态：INCOMPLETE，脚本就绪，修后沙箱外验证尚未运行。结果与既有夹具归因见 `RESULTS.md`；主控登记 issue 使用 `ISSUE-run-repair-fixture-01.md`。

修前两侧红态已经由主控取得并读回：`run-repair-probe-01` 中 cdf8fe9b 原产品和候选均为同一 ACK 后 idle 轮询 harness_error。此后仅修 `workbench/tests/test_quality_chain_e2e.py` 的共享 ACK 结束边界，业务断言不变；生产文件未改。

在本 worker worktree 运行：

```sh
python3 -B evidence/2026-10-14-batch14/T-080/run_final01_outside.py --output evidence/2026-10-14-batch14/T-080/final-03
```

入口先做两版本修后复验：原 cdf8fe9b 产品只替换修正后的测试夹具，当前候选使用同一夹具；固定修前已观察到的 ACK/repair 时序。两侧均须在原 `RED-RUN-REPAIR` 断言通过，并保存持久 ACK 结束事件、后续修复消息提交事件、run 有限期限返回及清理读回。不会更改旧产品、新产品或任务卡解析器以兼容另一种卡格式。

随后完整重跑 schema 正反例与三个既有打分 CLI 方法、protected、两案去 oracle 检查变异、第三次打回阈值变异、T-075 cards/coop/recovery/run/cas、T-077 lifecycle/conflict-panes、T-076 tracer/controls/完整 red 组/来源冻结/wide/审查故障、T-077 reviewer worktree/joint/relay/trailer conflict、启动停机和 attachment 套件。目录存在即拒绝；任何非预期失败立即停，保留原件，不重试、不从中间续跑、不调用真实模型。

先核对顶层 `final-03/run.json` 为 PASS，且 `run-repair-baseline-fixed/` 和 `run-repair-candidate-fixed/` 均为 PASS。全量 PASS 后提交命令为：

```sh
python3 -B evidence/2026-10-14-batch14/T-080/commit_outside.py --validation evidence/2026-10-14-batch14/T-080/final-03 --output /Users/luckye/Documents/Code/a2a/evidence/2026-10-14-batch14/T-080/commit-03
```

提交清单已包含本次修正的 `test_quality_chain_e2e.py`、原有所有权文件及主控追加授权的三个文件；证据一起提交。脚本核对冻结候选、原 worker 身份和钩子尾注，不 push，收据放主仓以免弄脏 worker。独立审查和最终受管 submit/验收/集成继续由主控按原流程处理；本 worker 不把受控回归等同于独立验收。
