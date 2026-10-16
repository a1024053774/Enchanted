# T-076 launch-policy fixture mismatch

`outside-command-06-01` 的 `worker-missing-override-red` 没有到达 argv 断言。`run_t076_launch_policy.py` 将当前 runner/fixture 与 `real-delivery-01/source-snapshot.tar.gz` 的旧 baseline 混用：baseline 快照的 `taskCards.ts` schema 不含 `oracle_paths`，而当前 `test_quality_chain_e2e.py` 生成的卡按 T-080 schema 含 `oracle_paths`。`card_save` 因 `invalid_task_card` 在启动策略断言前失败，故这是夹具/快照不配套，不是产品或 D3 断言缺陷。

T-082 不修改 T-076 runner 锚点、快照或审计逻辑。三项质量性质改用当前候选上的直接 tracer 用例复验：候选绑定、原生会话不续接、写入会话不能审查。
