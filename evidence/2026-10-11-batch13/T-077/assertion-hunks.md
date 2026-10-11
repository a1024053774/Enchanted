# T-077-1 断言 hunk 对照（首批实现，2026-10-11）

状态：**INCOMPLETE**。依据主控决定 02 的 W01～W16 白名单；本表只列已修改的 hunk。红态来自 `outside-red-01` 的业务断言，主控 #28 已确认 13 个案例、0 errors；当前绿态待运行，不预填 PASS。

重现本表所核对的 diff：

```sh
git -C /Users/luckye/Documents/Code/a2a-wt-t077 diff --unified=3 14b57d22a84bcaebfa91c5051b9909b53a570fac -- acceptance/test_coop_e2e.py acceptance/test_run_e2e.py workbench/tests/test_task_cards_e2e.py workbench/tests/daemon_acceptance_adapter.py
```

| 文件 | hunk 的旧侧起始行 | 白名单 | 内容 | 独立红态案例 |
| --- | --- | --- | --- | --- |
| `acceptance/test_coop_e2e.py` | 158 | W13、W16 | 可选理由透传；在 claim 前取 fence 推演下一序号，不从返回路径反推 | `test_overlap_without_reason`、`test_worker_name`；带理由正例尚待补 |
| 同上 | 174 | W16 | 精确项目/任务/序号目录及 worker 分支 | `test_worker_name` |
| 同上 | 320 | W12 | alpha 轮结束后 revoke，再做 beta 的独立竞争，不默认补并行理由 | `test_overlap_without_reason`、`test_clean_revoke` |
| 同上 | 345 | W02 | 撤销干净目录消失，隐藏引用与保留分支指向 C | `test_clean_revoke` |
| 同上 | 453、467 | W01 | 一次 G 变化后同一 integrate 重验；核对新 G/M、独立 oracle、父提交、内容与幂等 | red-01 的 `test_r8_revalidates_on_new_head`；green-02 待跑 |
| `acceptance/test_run_e2e.py` | 217、234、243 | W03 | submit 前保存文件字节；完成后核对清理、引用与内容 | `test_integrated_run_cleanup`；辅助进程场景后续回归 |
| 同上 | 321 | W04 | 全量引用映射只增加明确的 worker 分支和 A(N)，未 submit 的提交从引用读回 | `test_timeout_cleanup_retains_unsubmitted_commit` |
| 同上 | 422 | W05 | 旧已回收目录删除、replacement 保留；旧基线从 A(1) 读回 | red-03 `test_superseded_run_retains_only_new_workspace` |
| 同上 | 439 | W06 | 全量引用映射只增加明确的 A(N)、V(N,1)，坏候选不能集成，终结后清理 | `test_rejected_run_cleanup` |
| 同上 | 523 | W07、W13 | 三个指定调用带理由；首次历史回收只允许添加旧 attempt 的 A(1) | red-03 `test_historical_cleanup_leaves_current_and_foreign_untouched`；red-01 交集默认拒绝 |
| 同上 | 562 | W07、W13 | 只删 old/current；保留 replacement/foreign；逐条核对理由和交集身份 | 同上 |
| `workbench/tests/test_task_cards_e2e.py` | 149 | W08 | 完成验收目录删除，M 经用途引用读回 | `test_completed_verification_cleanup` |
| 同上 | 284、293 | W10 | revise 前保留 C，清理后仍用原 C 验证 stale_attempt | `test_clean_revise` |
| 同上 | 387 | W09 | 同一次 integrate 自动重验，缺尾注干预不重复、外部内容保留 | red-03 `test_r8_missing_trailer_is_not_recorded_twice` |
| `workbench/tests/test_cas_race.py` | 1、17、27 | W11 | 实际写入前竞争后重验；核对新 G、双方祖先、外部内容及 oracle 第二次运行 | red-03 `test_cas_write_race_revalidates` |
| `workbench/tests/daemon_acceptance_adapter.py` | 290 | W14 | 故障屏障核对当前 verification 的精确路径，保留 PID/generation/release 检查 | `test_verification_name`；假目录反例后续补 |

没有修改 `acceptance/test_recovery_e2e.py`、通用 `unchanged()`、旧 run 不得接管新 attempt、外来身份拒收或 oracle 内容。没有过滤整个 `refs/a2a/*` 命名空间。主控 #38 确认 red-03 后，W05/W07/W09/W11 与 W13 的指定调用点已迁移。W15 由新增 `run_s3_regression.py`、`audit_s3_assertions.py` 实现；旧 `run_daemon_acceptance.py` 未改。

本轮 `check-01` 只运行 12 项 lifecycle 候选检查，再对冻结起点运行 R8 第 4 次失配的新增红态。完整 8/9/18、变基后复验与审查尚未运行。

主控 #31 后读回：green-01 的 12 项已全绿；red-02 的 R8 上限有 2 项业务失败，0 errors。新增 `check-02` 验证 R8 候选，并对 W05/W07/W09/W11 补起点红态；该批尚未执行，不修改其原断言抢跑。

主控 #38 后读回：green-02 的 2 项 R8 全绿；red-03 五项业务红态均成立、0 errors。当前范围审计见 `assertion-audit-02.json`：5 个已有文件的改动均位于授权坐标；对白名单外恢复断言、唯一认领断言的变动均拒绝，显式执行的 allow-all 审计变异体被这两项检查拒绝。`assertion-audit-01.json` 保留早一版范围检查记录；02 补充了显式坏审计器调用。这个范围 PASS 不证明断言语义或产品行为正确。

主控 #40 后：green-03 的 W05/W07/W09 信号通过，W11 因第二个 wrapper 被夹具误用 release-all 主动 abort 而失败；原记录保留。W11 只将“后续 Git 的放行方式”改为恢复 fixture 路由，业务断言 AST 不变，仍位于 W11 原行 20～35 的驱动范围。`assertion-audit-03.json` 范围检查 PASS，诊断见 `check-03-diagnosis.json` / `HANDOFF-check-04.md`。下一批对修正夹具重做 W11 红绿，并运行未执行的回归。
