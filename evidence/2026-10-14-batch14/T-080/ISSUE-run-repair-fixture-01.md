# 既有夹具缺陷：ACK 后修复回合启动，使 quality red 组错过 idle 窗口

状态：INCOMPLETE（已确认归因，修正已获主控 #154 授权，修后沙箱外验证待运行）。发现者：T-080 worker `s14-t080`，任务 `T-080/a1`。本正文交主控登记主仓收件箱，worker 未执行发送命令。

位置：`workbench/tests/test_quality_chain_e2e.py` 的 `QualityCase.worker_submit`，原逻辑在停止 ACK 回合后轮询窗格 idle/ended。受影响场景是 `red_run_reject_preserves_worker`。

现象：T-080 的 final-02 在该场景报 `HarnessFailure('Controlled pane did not reach its expected boundary')`。原件的 oracle 检查通过，completion 按预期 exit=1；门禁已打回并把修复消息送回原 worker。ACK turn-2 已结束，窗格随后执行修复 turn-3，状态 busy 且无 failed/stopped。夹具仍等待已经过去的 idle 窗口，因而没能执行原本应核对的业务断言。

对照：主控运行 `probe_run_repair_outside.py --output .../run-repair-probe-01`，rc=0、对照 PASS。cdf8fe9b 原产品和当前 T-080 候选均在相同受控时序下出现同一 harness_error；两侧都读回 ACK idle 事件先于修复消息的 turn_submitted，原 worker 未回收、主分支未推进。证据分别为 `run-repair-probe-01/baseline/`、`candidate/` 的 case、数据库、Git 读回和 `ack-repair-barrier.json`。这是 main 上既有的夹具缺陷，不是 T-080 引入的 run 产品回归。

覆盖缺口：T-077 的 `rebase-final-05` 未运行这一 quality red 组。`evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/run.json` 有 39 个通过阶段，但 quality-chain 只以 `--group controls` 运行；`run-rebase-final-05.py` 第 260 行附近的阶段表列了 tracer、wide、review-red、controls、provenance，没有 `test_quality_chain_e2e.py --group red`。因此不能把该次历史通过视为本 red 组已通过。

影响：健康的修复回写被误判为 harness_error，阻断回归并遮蔽 run 保留 worker 的业务结论。未发现该原件中的产品回收、身份或 oracle 拒收缺陷。

处理：按 #154 在 T-080 内修共享夹具，结束 ACK 后核对绑定本次身份与 submission 的唯一持久 pane_idle 事件，保留原业务断言；final-03 先在 cdf8fe9b 原产品与候选上重放同一时序，两侧均须通过，再运行全量（明确包含完整 red 组）。修前两侧红态、final-02 失败及历史证据全部保留。

建议主控将本条作为既有夹具缺陷与历史覆盖范围登记；待 final-03 两侧修后绿态及完整 red 组通过后补充结果。不要回写或扩大 T-077 原 39 阶段的通过范围。
