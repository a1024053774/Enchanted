# T-122 质量链回归对照（test_quality_chain_e2e.py，--card-dialect current）

候选：工作区（T-122 改动）；基线：HEAD 7a8a6f74f 导出到 scratchpad 的源码。运行目录体量大，未入库（T-088）。

| 一侧 | case | 结果 |
|---|---|---|
| candidate | control_busy_queue | harness_error |
| candidate | control_completion | passed |
| candidate | control_fence | passed |
| candidate | control_frozen_candidate | passed |
| candidate | control_paths | passed |
| candidate | control_relay_duplicate | harness_error |
| candidate | control_relay_invalid | harness_error |
| candidate | control_stop_without_request | harness_error |
| candidate | red_base_not_failing | passed |
| candidate | red_candidate_fails | passed |
| candidate | red_feedback_idle | harness_error |
| candidate | red_manifest_missing | passed |
| candidate | red_repair_resubmit | harness_error |
| candidate | red_review_required | passed |
| candidate | red_rules_failing | passed |
| candidate | red_rules_frozen | passed |
| candidate | red_run_reject_preserves_worker | harness_error |
| candidate | red_run_waits_for_executor | harness_error |
| candidate | red_terminal_prerequisites | passed |
| head | control_busy_queue | harness_error |
| head | control_relay_duplicate | harness_error |
| head | control_relay_invalid | harness_error |
| head | control_stop_without_request | harness_error |
| head | red_feedback_idle | harness_error |
| head | red_repair_resubmit | harness_error |
| head | red_run_reject_preserves_worker | harness_error |
| head | red_run_waits_for_executor | harness_error |

结论：候选 11 项 passed；8 项 harness_error 在基线上同样 harness_error（同一报错“Controlled pane did not reach its expected boundary”，受控窗格停在 busy），是 T-122 之前就存在的测试夹具问题，不是本票回归。

重现：`cd workbench/tests && python3 test_quality_chain_e2e.py --source <源码根> --output <新目录> --group red|controls --card-dialect current [--case <case>]`
