# T-081 结果表

状态：INCOMPLETE

| 案例 | 状态 | 发现判定 | 预期 | 实际拒收码/结果 | 事件位置 | 工作分支是否不动 | 集成状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 7 | 已知行为 | 不改 | 记为已知行为，不改 | 20261015T044138Z-ideation-answer-001 |  | 见 RESULTS.md 第 7 项 | 本轮不重跑 |
| oracle_test | PASS |  | oracle_modified | oracle_modified | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/green-oracle_test/oracle_test/observation.json events | True | submitted |
| oracle_entry | PASS |  | oracle_modified | oracle_modified | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/green-oracle_entry/oracle_entry/observation.json events | True | submitted |
| self_report_unchanged | PASS |  | oracle_failed | oracle_failed | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/green-self_report_unchanged/self_report_unchanged/observation.json events | True | submitted |
| self_report_wrong | PASS |  | oracle_failed | oracle_failed | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/green-self_report_wrong/self_report_wrong/observation.json events | True | submitted |
| stale_attempt | PASS |  | stale_attempt | stale_attempt | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/green-stale_attempt/stale_attempt/observation.json events | True | claimed |
| deny_path | PASS |  | path_boundary_failed | path_boundary_failed | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/green-deny_path/deny_path/observation.json events | True | submitted |
| trailer_partial | PASS |  | invalid_trailers | invalid_trailers | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/green-trailer_partial/trailer_partial/observation.json events | True | submitted |
| trailer_duplicate | PASS |  | 尾注含本会话与其他会话的矛盾身份，必须拒收；实际拒收码单列记录 | invalid_trailers | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/green-trailer_duplicate/trailer_duplicate/observation.json events | True | submitted |
| trailer_task | PASS |  | trailer_task_mismatch | trailer_task_mismatch | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/green-trailer_task/trailer_task/observation.json events | True | submitted |
| trailer_attempt | PASS |  | trailer_identity_mismatch | trailer_identity_mismatch | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/green-trailer_attempt/trailer_attempt/observation.json events | True | submitted |
| trailer_launch | PASS |  | trailer_identity_mismatch | trailer_identity_mismatch | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/green-trailer_launch/trailer_launch/observation.json events | True | submitted |
| trailer_tool | PASS |  | trailer_identity_mismatch | trailer_identity_mismatch | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/green-trailer_tool/trailer_tool/observation.json events | True | submitted |
| trailer_model | PASS |  | trailer_identity_mismatch | trailer_identity_mismatch | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/green-trailer_model/trailer_model/observation.json events | True | submitted |
| trailer_effort | PASS |  | trailer_identity_mismatch | trailer_identity_mismatch | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/green-trailer_effort/trailer_effort/observation.json events | True | submitted |
| trailer_no_launch | PASS |  | trailer_launch_record_missing | trailer_launch_record_missing | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/green-trailer_no_launch/trailer_no_launch/observation.json events | True | submitted |
| after_review | PASS |  | stale_turn; integrate C1 only | stale_turn; integrated C1 | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/green-after_review/after_review/observation.json events | 否；仅允许集成 C1 | accepted |
| 6a | PASS |  | 完全无尾注恰好记一次人工介入并集成 | integrated | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/green-trailer_absent/trailer_absent/observation.json events | False | accepted |
| positive_single | PASS |  |  | integrated | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/positive-positive_single/positive_single/observation.json events | False | accepted |
| positive_multi | PASS |  |  | integrated | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/positive-positive_multi/positive_multi/observation.json events | False | accepted |
| positive_red_card | PASS |  |  | integrated | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/6e-rerun-01/positive-positive_red_card/positive_red_card/observation.json events | False | accepted |

正例执行数：4
误拒绝数：0
原始事件与命令输出位置见 run.json 的 steps 与逐案 observation.json。
6e 拒收：伪造 Launch、Tool、Model、Effort 期望 trailer_identity_mismatch；带尾注且无启动记录期望 trailer_launch_record_missing。每案先在 /tmp 副本删掉对应比较，红态须放行该交付，再在候选上取绿。
6a 正向核对完全无尾注恰好记一次人工介入并集成。三个正例计入正例执行数。正确拒收不计入误拒绝。真实 Codex 回合为 0；未运行项不计通过。
