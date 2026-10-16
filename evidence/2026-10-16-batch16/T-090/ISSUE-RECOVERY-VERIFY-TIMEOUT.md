# 非阻塞：两个恢复用例在整组运行中偶发 verify 客户端超时

上报者：worker `s16-t090`，task `T-090`，attempt `a1`。本 issue 为非阻塞；不修改验收、期限或重试策略。

## 现象与影响

`test_after_CAS_deleted_ref_requires_reconciliation` 和 `test_after_CAS_external_X_requires_reconciliation` 在 `setup_candidate(verified=True)` 中偶发等待 verify 客户端超过原 12 秒期限，原方法报 error，尚未完成各自的 CAS 后故障场景。整组 runner 因此可能停在 recovery，后续组没有执行。

具体调用位置：`acceptance/test_recovery_e2e.py:371` 调用 complete；`:210` 等待子进程；`workbench/tests/daemon_acceptance_adapter.py:140` 转交原 complete。后台事件显示仍在推进验证清理／审查启动，不能把客户端超时直接归为 review_lifecycle_failed 或审查拒绝。

## 三处原件

1. `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/green-regression-02/recovery/`：T-090 `18dd12c29...`，原 9 项为 7 通过、两条上述方法 error。详见 unittest.txt、run.json、readbacks 和 fixtures.tar.gz；没有 review_lifecycle_failed。仓库入口：`green-regression-02.json`。
2. `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/recovery-three-versions-01/pre-T082/recovery/`：exec/t078 `150ef6516...`，同两方法中 deleted-ref error、external-X 通过。比较器误拒预期故障退出导致采集停止的问题已单独修复，未改原测试结果。仓库入口：`recovery-three-versions-01.json`、`EXIT-CHECK-DIAGNOSIS-01.md`。
3. `/Volumes/WD-Elements/a2a-evidence/2026-10-16-batch16/T-090/recovery-four-versions-02/`：main 合入前 `271ac55d8...`、main T-082 `0e6c2b833...`、T-090 `18dd12c29...` 各运行同两方法，均为 run 2 / error 0 / failure 0。仓库入口：`recovery-four-versions-02.json`。

## 主控裁定及边界

当前对话主控 #13／#7 明确裁定（逐字）：

> 这两例是偶发、对时序/负载敏感的失败，不是 T-090 引入，也不是 T-082 引入。

按该裁定作为既有测试时序问题非阻塞上报，不计为本次 worker 边界修复引入。当前没有测得负载与失败的因果关系，也未定位具体慢点机制；不把这些对照推广为稳定性保证。已发生的 error 均保留为 error，不补称为 PASS。

建议主控另行安排缺陷级调查，保留完整组与单例的调度／进程时点，确定如何消除时序敏感性。此 issue 不授权修改受保护验收、不加长超时、不加盲目重试；本轮仍按原验收执行完整回归并如实报告。
