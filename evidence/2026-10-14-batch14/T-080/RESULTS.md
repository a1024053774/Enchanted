# T-080 验证结果（2026-10-14，final-03 运行前）

状态：INCOMPLETE。final-03 全量尚未运行；尚无本候选的完整回归、独立审查、提交或集成结论。所有受控运行均未调用真实模型。

已保存的结果：

- `red-01`：INCOMPLETE，Python 3.9 不支持 tarfile filter 参数，业务场景未运行，原件保留。
- `red-02`：红态 PASS。候选只改验收文件使之恒过，产品仍为 base，独立原断言 exit=1；旧门禁 verified 且 integrated。门禁缺口成立。
- `final-01`：INCOMPLETE。上限场景错误地要求暂停后重放 verify 返回内部错误码，修正依据和原件见 `FINAL-02.md`、`limit-replay-diagnosis-01.json`。生产代码未为该错误期望改动。
- `final-02`：INCOMPLETE。已通过 schema 混合读写、三个既有打分 CLI 方法、protected、T-075 cards/coop/recovery/run/cas、T-077 lifecycle-conflicts/conflict-panes、T-076 tracer/controls。去 oracle 检查的两案均在 `ORACLE-MODIFIED` 业务断言失败；把上限改为第四次的变异体在 `ORACLE-THREE-LIMIT` 失败，均为预期红态。quality red 组前九案 passed，第十案 `red_run_reject_preserves_worker` 为 harness_error，第十一案及后续阶段未运行。

本轮确认的既有夹具缺陷：

`run-repair-probe-01/result.json` 为最小对照 PASS：cdf8fe9b 原产品与 T-080 候选，在同一受控合法时序下均出现原夹具的 idle 轮询超时。这里的 PASS 只表示成功复现夹具缺陷；两侧 case 的实际 outcome 均为 harness_error，不是业务红态或产品验收通过。

两侧均由真实 run 完成 completion 打回，repair 消息绑定原 launch/attempt。ACK turn-2 已有持久 `pane_idle`，随后 repair 进入 turn-3；最后窗格 healthy/busy，原 worker 未回收、主分支未推进。当前候选的 oracle 检查已通过。归因是 ACK 后队列可立即启动修复回合，夹具轮询错过短暂 idle 窗口；这是 cdf8fe9b 上已有的夹具缺陷，不能归为 T-080 产品回归。

历史覆盖核对：`evidence/2026-10-11-batch13/T-077/outside-rebase-final-05/run.json` 记录 39 阶段 PASS；其中调用 `test_quality_chain_e2e.py` 的阶段只有 `t076-final-controls`，参数为 `--group controls`。`run-rebase-final-05.py` 的阶段表同样没有 `--group red`。因此 T-077 的 rebase-final-05 没有覆盖本次失败的 quality red 组；该历史 PASS 不能替该组背书。供主控登记的 issue 正文见 `ISSUE-run-repair-fixture-01.md`。

修正范围经主控 #154 授权，仅修改共享夹具 `worker_submit` 的 ACK 就绪条件：读取绑定 launch、attempt、task、submission、native session 和 ACK turn 的唯一持久结束事件，并保存原始回执。移除原瞬时 idle/ended 轮询分支；不增加任意 busy 即成功的路径，不延长期限，不自动重试。全部 22 个业务 `self.check(...)` 调用与 cdf8fe9b 的 AST 完全一致，两个 run 场景的业务断言保持不变。生产门禁、panes、daemon、CLI、打分和 README 与 final-02 冻结候选逐字节相同。

final-03 已准备、未运行：先引用上述两侧修前红态，再在 cdf8fe9b 原产品中仅替换本次测试夹具，在候选中使用相同修正；两侧均固定原红态的 ACK/repair 时序，必须通过原 `RED-RUN-REPAIR`，读回 ACK 结束事件、后续修复提交事件及有限期限返回。任一失败立即停止。随后重新运行原定全量，包含完整 quality red 组及 final-02 未运行的阶段。所有结果写入新目录，不从失败点续跑。

准备检查 PASS：Python 3.9 语法、业务断言不变、原产品归档与 Git cdf8fe9b 夹具一致、生产文件不变、T-077 覆盖清单、`git diff --check`。运行证据和 project-map status 保存到 `final03-readiness-01.json`。沙箱外修后两侧绿态和全量回归仍为 INCOMPLETE，交主控运行。
