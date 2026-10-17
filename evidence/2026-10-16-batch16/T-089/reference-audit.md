# T-089 evidence 引用核对（2026-10-17）

状态：PASS（仅 T-086 一次性副本搬迁的引用范围核对）。

没有源码直接引用 T-086；没有重跑历史业务验收，也不据此允许归档其他历史批次。

| 文件 | 用途与输入 | 本次核对 |
| --- | --- | --- |
| `workbench/tests/archive_t081_capability_run02.py` | T-081/capability-run-02/commands.jsonl，归档命令读取原件 | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/audit_legacy_scope.py` | T-076/card-2/legacy-acceptance-hunks.diff | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/check_t081_capability_paths.py` | T-081/capability-run-02 的 commands、run.json | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/check_t081_capability_run03.py` | T-081/capability-run-02 的 commands 与 run-03 的 run.json | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/collect_t081_closeout.py` | T-081/full-04、capability 与补充验收 JSON | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/commit_t081_closeout.py` | T-081/cas-01、home-cleanup-01、closeout-final-01 的结果 | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/commit_t081_duplicate_fix.py` | T-081/duplicate-conflict-01 的 run/review 记录和 source_snapshot 路径 | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/commit_t081_review01.py` | 输出、同次运行读回或记录引用 | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/diagnose_t081_capability_run02.py` | T-081/capability-run-02 的 pty、events、commands、run.json | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/prepare_daemon_mutants.py` | 输出、同次运行读回或记录引用 | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/prepare_s3_baseline.py` | 旧 T-077 checkout 的 outside-red-01/run.json 和 sources.tar.gz | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/prepare_t081_capability.py` | 输出、同次运行读回或记录引用 | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/prepare_t081_capability_run02.ts` | T-081/capability-review-01 的 policy、task-card、role、config；prepared 的 hooks | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/prepare_t081_capability_run03.ts` | T-081/capability-review-02、run02-diagnosis-02、prepared 的 hooks | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/prepare_t081_capability_run04.ts` | T-081/capability-review-03、run03-finding-01、prepared 的 hooks | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/run_daemon_acceptance.py` | T-075/card-5 三个小文件、T-075/run-acceptance.py；T-076/card-2 两个小文件 | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/run_p_review.py` | T-076/card-2/p-review-02 的 policy、角色、批准材料与 source snapshot | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/run_s3_regression.py` | 输出、同次运行读回或记录引用 | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/run_t076_green.py` | T-076 consistency 数据库目录；T-075/card-4/outside-live-04/lifecycle | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/run_t076_legacy_green.py` | T-076/card-2/legacy-acceptance-hunks.diff；T-075 lifecycle | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/run_t076_quality_real.py` | T-076/card-2/real-delivery-02 的 policy、脚本与归档；p-review-readback-01.json | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/run_t076_quality_red.py` | 输出、同次运行读回或记录引用 | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/run_t076_quality_widen.py` | T-076/card-2/outside-focused-tracer-01/run.json 与 candidate-source.tar.gz | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/run_t076_real.py` | 输出、同次运行读回或记录引用 | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/run_t081_absent_case.py` | 输出、同次运行读回或记录引用 | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/run_t081_bad_worker_suite.py` | T-081/full-03/t076-wide/run.json；T-077/controlled-trailer-input.json | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/run_t081_capability_recheck.py` | 输出、同次运行读回或记录引用 | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/run_t081_capability_turn.py` | T-081 的 prepared/review/receipt、run-01/02/03、finding 与 native-root；旧归档仍要求外置盘 | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/run_t081_cas_suite.py` | 输出、同次运行读回或记录引用 | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/run_t081_commit_scope.py` | 输出、同次运行读回或记录引用 | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/run_t081_duplicate_case.py` | T-081/full-04/green-trailer_duplicate/trailer_duplicate/observation.json | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/run_worker_delivery.py` | 输出、同次运行读回或记录引用 | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/t081_capability_home.py` | T-081/capability-run-02/03/04 的 run.json；夹具 owned-pids | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/test_command_evidence.py` | T-075/card-4/offline-trace 的 commands.jsonl 与两份 .bin | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/test_t081_archive_ownership.py` | T-081/full-02/t075-coop/run.json 和 fixtures.tar.gz | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/test_t081_capability_audit.ts` | T-081/capability-review-04 的 policy 与 FIRST-TURN.template.md | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/test_t081_commit.py` | 输出、同次运行读回或记录引用 | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/test_t082_review_boundary_e2e.py` | T-082/protocol-red-green-01/real-review-submit.json | PASS；不在 T-086 搬迁集合 |
| `workbench/tests/test_worktree_lifecycle_e2e.py` | T-077 的 PLAN、决定01/02、outside-sandbox.sh；baseline 模式另读 outside-red-01/sources.tar.gz | PASS；不在 T-086 搬迁集合 |
| `acceptance/test_coop_e2e.py` | 输出、同次运行读回或记录引用 | PASS；不在 T-086 搬迁集合 |
| `acceptance/test_dispatch_session_e2e.py` | 输出、同次运行读回或记录引用 | PASS；不在 T-086 搬迁集合 |
| `acceptance/test_inbox_e2e.py` | 输出、同次运行读回或记录引用 | PASS；不在 T-086 搬迁集合 |
| `acceptance/test_recovery_e2e.py` | 输出、同次运行读回或记录引用 | PASS；不在 T-086 搬迁集合 |
| `acceptance/test_run_e2e.py` | 输出、同次运行读回或记录引用 | PASS；不在 T-086 搬迁集合 |

三个真实输入样本经过归档入口后仍原样可读；路径、逐项位置及命令见 `t086-local-02.json`。
