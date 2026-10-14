# T-080 FINAL-02 交接（2026-10-14）

状态：INCOMPLETE。#149 的归因核对完成，修正后的运行尚未开始。原 `final-01` 和 `/private/tmp/q76-8hermkdo` 保留；本轮不重试旧目录或旧后台。

结论：测试期望错误，不是本次 oracle 打回未计入或上限未写出的产品缺陷。证据见 `limit-replay-diagnosis-01.json`。

依据来自规格及此前验收，不以实际错误码反推预期：

- native-cli-orchestration spec 第 3 节第 4 步与 T-076 What to build 第 2 条规定：同一 attempt 连续三次打回后停止自动回写，交执行主控；没有规定暂停后重放 verify 的特定错误码。
- T-076 的 `tracer_third_rejection` 检查 paused、stopped、计数 `[1,2,3]`、两次修复注入、窗格空闲/空队列、问题上报和工作分支不变。旧受控正例通过；`third-rejection-keeps-writing` 变异体在 `TRACER-THIRD-STOP` 业务断言失败。原验收没有把 `quality_rejection_limit` 作为重放的必要返回码。
- `final-01/protected/oracle_three_rejections/database-readback.json` 读回三条 `delivery_rejected`，check 均为 oracle，计数为 1、2、3；第三次 stopped=true、task=paused。有一条绑定原 launch/attempt/第三次 repair 的 `quality_feedback_stopped`，以及一条给 executor 的 blocking 问题，body 为该 repair。修复回写只有两次。
- 候选 C3 仍保留，不是被清空。公开 request 对 verify 先要求 submitted/verifying，因此 paused 在进入私有 `verifyCandidate` 的上限检查前就返回 `not_submitted`。原断言把内部错误码当成了公开契约。

修正只在测试与阶段运行器：

- 删除特定重放错误码的假定；仍要求请求被拒绝，额外核对三次 oracle 计数、暂停、停止回写事件、完整问题上报及原 worker 空闲空队列。
- 重放后核对 repair、候选、attempt、fence、verification 身份、拒收次数、回写消息、工作分支及 reflog 不变；不得产生新的验证、完成条件、审查、打回或集成进展。拒绝响应原文保留在 `limit-replay.json`。
- 保留原去验收文件检查的变异体；新增一次性副本把停止阈值从第三次改为第四次，仅运行 `oracle_three_rejections`，必须在 `ORACLE-THREE-LIMIT` 业务断言失败。语法、harness 或清理错误不能算变异红态。

未修改生产门禁、打分脚本或 README；已逐字节核对相关生产文件与 `final-01/candidate-source.tar.gz` 相同。`final-01/protected/run.json` 实际记录 11 个 passed、1 个 contract_failure；整个阶段为 INCOMPLETE，其后的变异体和 T-075/076/077 回归没有运行。旧通过结果不替新测试候选背书。

在本 worker worktree 中运行同一阶段入口，使用新目录：

```sh
python3 -B evidence/2026-10-14-batch14/T-080/run_final01_outside.py --output evidence/2026-10-14-batch14/T-080/final-02
```

它重新冻结当前候选，重新运行 schema 混合读写、三个既有打分 CLI 方法、完整验收文件套件、两个有明确业务失败要求的变异阶段，以及原定 T-075/T-076/T-077 回归；不使用旧候选的通过结论。运行失败则保存现场，不重试、不覆盖。既有共享 schema=2 决定、主仓 records 不改写、无真实模型等约束继续适用，详见 `FINAL-01.md`。

全量 PASS 后，提交入口不变，仅绑定新验证目录和新的主仓收据目录：

```sh
python3 -B evidence/2026-10-14-batch14/T-080/commit_outside.py --validation evidence/2026-10-14-batch14/T-080/final-02 --output /Users/luckye/Documents/Code/a2a/evidence/2026-10-14-batch14/T-080/commit-02
```

本 worker 未运行沙箱外场景、变异体、回归或提交；这些检查仍为 INCOMPLETE。主控独立审查和最后的交付、集成继续按原门禁流程执行。
