# T-081 full-04 交接（主控 #171）

状态：INCOMPLETE。full-03 原件保留，full-04 尚未运行。第 7 项脚本同时准备完成，未启动。

## full-03 读回与归因

full-03 顶层为 INCOMPLETE / rc=2，11 个坏行为案及其变异体已取得所需结果，三个正例均集成、误拒绝 0。T-075 五套、T-077 生命周期、T-080 protected、T-076 tracer/controls/red/legacy-boundaries 已结束通过；后续回归没有据此上调。

中断点是 `t076-wide/widen_red_rules_success` 的 `configure_host`，尚未启动该场景 daemon：它读取 `q.SOURCE/acceptance/test_recovery_e2e.py` 以提取原故障夹具，候选快照却没有 acceptance 目录。不是卡格式或工作目录断言失败，不是产品门禁缺陷。

`wide-source-diagnosis-01/run.json` 使用当前 main `09e40f033c5b57287ce769bd287416fef15b5f94` 的同一用例方法做最小对照：指向 full-03 候选快照时复现 FileNotFoundError；指向 main 快照时正常生成 Git 故障夹具。`wide-source-repair-01/run.json` 再用 runner 实际组装循环生成修后候选，该步骤通过。这些只证明失败前置步骤的归因，不冒称完整 main 场景端到端通过。

## 修正与完整重跑

快照边界改为回归真正使用的四个源码目录：workbench、scripts、acceptance、fixtures；依赖与构建输出继续排除，依赖只共享现有 node_modules。候选以及原产品/main 的归档均保存这些目录，相关输入纳入冻结核对。删除只挑三个 score 文件的局部投影。没有修改门禁、现有测试或验收断言，没有旧格式兼容分支。

```sh
python3 -B workbench/tests/run_t081_bad_worker_suite.py --output evidence/2026-10-14-batch14/T-081/full-04
```

脚本先引用 full-03 原始失败，再通过真实 CLI/daemon 跑 main 与修后候选的完整 `widen_red_rules_success` 单用例。两侧任一失败立即保留并报告。两侧通过后，从头跑四项追溯观察、坏 worker 矩阵、三个正例和所有回归；不从旧失败位置续跑、不重试、不省略 wide 余下案例。主控读取 `wide-source-control-main/`、`wide-source-control-candidate/` 及顶层 `controlled_status`；整体状态仍受 6a、第 7 项和独立验收未完成约束。

## 第 7 项

按主控 #169 已批准的 `T-081 controller-decision-01 capability-turn-1`，已新增 [首轮运行脚本](../../../workbench/tests/run_t081_capability_turn.py)，用标准产品 CLI 的 daemon_start/dispatch/release/stop 完成一次观察，实际 spawn 前校验 argv。主控按 [运行交接](CAPABILITY-RUN.md) 依次执行 home prepare、首轮脚本；home cleanup 仍另批。当前没有实际 Codex 启动。

T-081 FULL-04 READY
