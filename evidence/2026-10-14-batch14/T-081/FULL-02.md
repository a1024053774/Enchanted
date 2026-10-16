# T-081 full-02 交接（主控 #164 / #165）

状态：INCOMPLETE。full-02 脚本已准备，尚未运行；业务矩阵、四项新观察与回归均不宣称通过。第 7 项继续逐次等主控批准，真实 Codex 回合为 0。

主控已运行的 `full-01/` 原样保留，包括 rc=3 / NO_GO、原源码快照、同输入的 Launch 观察、命令输出和事件。该次原产品与当时候选均进入 reviewing，随后 integrated / accepted；Model、Effort、Tool 当时未运行。按主控 #164 / #165，后续将这一类记为“追溯字段一致性”发现，契约缺口交构思主控和用户裁定，T-081 不改产品。

主控在本 worker worktree 沙箱外运行：

```sh
python3 -B workbench/tests/run_t081_bad_worker_suite.py --output evidence/2026-10-14-batch14/T-081/full-02
```

输出目录存在即拒绝，不覆盖任何旧结果。运行顺序：

1. 冻结原产品 `391d70b07ceda29462c06b47116b36829d767001`、启动时本地 `refs/heads/main` 的完整提交号和本票未提交候选，分别保存源归档。准备时读到的 main 为 `490de67d05a08ccf8a453a78694a106288579b47`；正式证据以运行时 `main-head.json` 和 `source-manifest.json` 为准，不在运行中切换版本。
2. 原产品与该 main 各跑正确单提交对照，再对 Launch、Model、Effort、Tool 各做一个只有该字段与对应启动记录不一致的夹具提交。每对业务输入相同；各自的真实夹具 attempt/session/launch 和提交号另记。保留字段输入值、启动记录参考值、verify 返回、尾注事件、审查与集成结果、工作分支和集成状态，写入四份 `probe_*-pair.json`。
3. 每项只记 `FINDING`，进入审查的结果附发现判定 `NO_GO`；拒收则如实记录实际码，不补作拒收绿态。观察子运行的 `run.json` 保持 `status: INCOMPLETE`，以 `observation_complete` / `outcome: observed` 表示记录完成，明确 `counts_toward_acceptance: false`。结果如何都不在 6e 处整体停止，也不把它计入正例或误拒绝统计。
4. 继续原定 1–5、6b–6d：11 个输入各先跑对应变异业务红态，再跑候选拒收或 C1 绑定验证。继续单提交、多提交、带新增测试的红态卡三个正例；三个全部完成通过后报告误拒绝 0。其余非预期失败、基础设施错误或清理失败仍保留现场并停止，不能伪造红绿结果。
5. 继续已有 T-075～T-077、T-080 回归及 project-map 检查。6a 仍在表中列“待裁定”，第 7 项列“待逐次批准”，均不计通过。

正常完成时 rc=0 仅表示指定受控流程完成；顶层 `status` / `product_status` 仍为 INCOMPLETE，分别读取 `controlled_status`、发现列、正例数量和误拒绝数。任一后续验收或基础设施阶段未完成，保留未运行项，不能因 6e 已成为发现而放宽其他案例。

本轮只改 `workbench/tests/test_bad_worker_e2e.py` 和 `run_t081_bad_worker_suite.py`。与 full-01 的冻结源码逐项核对，21 个非 6e 方法的 AST 和全部变异配方保持一致；`full02-readiness-01/acceptance-scope.json` 及两份补丁可复查。静态语法、CLI 帮助与路径边界检查通过，不替代 full-02 运行。产品代码、任务卡预期、T-083 所有的 `acceptance/test_herdr_traceability_e2e.py`、隔离 home 和 hook 启用状态均未改。

T-081 FULL-02 READY
