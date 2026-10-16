# T-081 结果表

状态：INCOMPLETE

| 案例 | 状态 | 发现判定 | 预期 | 实际拒收码/结果 | 事件位置 | 工作分支是否不动 | 集成状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6a | 待裁定 |  |  |  |  | 未执行 | 未执行 |
| 7 | 待逐次批准 |  |  |  |  | 未执行 | 未执行 |
| probe_launch | FINDING | NO_GO | 仅观察追溯字段一致性；契约待裁定 | {'baseline': {'verify_error': None, 'state': 'reviewing', 'integrated': True}, 'main': {'verify_error': None, 'state': 'reviewing', 'integrated': True}} | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-04/probe_launch-pair.json observations.*.events | {'baseline': False, 'main': False} | {'baseline': 'accepted', 'main': 'accepted'} |
| probe_model | FINDING | NO_GO | 仅观察追溯字段一致性；契约待裁定 | {'baseline': {'verify_error': None, 'state': 'reviewing', 'integrated': True}, 'main': {'verify_error': None, 'state': 'reviewing', 'integrated': True}} | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-04/probe_model-pair.json observations.*.events | {'baseline': False, 'main': False} | {'baseline': 'accepted', 'main': 'accepted'} |
| probe_effort | FINDING | NO_GO | 仅观察追溯字段一致性；契约待裁定 | {'baseline': {'verify_error': None, 'state': 'reviewing', 'integrated': True}, 'main': {'verify_error': None, 'state': 'reviewing', 'integrated': True}} | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-04/probe_effort-pair.json observations.*.events | {'baseline': False, 'main': False} | {'baseline': 'accepted', 'main': 'accepted'} |
| probe_tool | FINDING | NO_GO | 仅观察追溯字段一致性；契约待裁定 | {'baseline': {'verify_error': None, 'state': 'reviewing', 'integrated': True}, 'main': {'verify_error': None, 'state': 'reviewing', 'integrated': True}} | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-04/probe_tool-pair.json observations.*.events | {'baseline': False, 'main': False} | {'baseline': 'accepted', 'main': 'accepted'} |
| oracle_test | PASS |  | oracle_modified | oracle_modified | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-04/green-oracle_test/oracle_test/observation.json events | True | submitted |
| oracle_entry | PASS |  | oracle_modified | oracle_modified | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-04/green-oracle_entry/oracle_entry/observation.json events | True | submitted |
| self_report_unchanged | PASS |  | oracle_failed | oracle_failed | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-04/green-self_report_unchanged/self_report_unchanged/observation.json events | True | submitted |
| self_report_wrong | PASS |  | oracle_failed | oracle_failed | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-04/green-self_report_wrong/self_report_wrong/observation.json events | True | submitted |
| stale_attempt | PASS |  | stale_attempt | stale_attempt | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-04/green-stale_attempt/stale_attempt/observation.json events | True | claimed |
| deny_path | PASS |  | path_boundary_failed | path_boundary_failed | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-04/green-deny_path/deny_path/observation.json events | True | submitted |
| trailer_partial | PASS |  | invalid_trailers | invalid_trailers | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-04/green-trailer_partial/trailer_partial/observation.json events | True | submitted |
| trailer_duplicate | PASS |  | invalid_trailers | invalid_trailers | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-04/green-trailer_duplicate/trailer_duplicate/observation.json events | True | submitted |
| trailer_task | PASS |  | trailer_task_mismatch | trailer_task_mismatch | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-04/green-trailer_task/trailer_task/observation.json events | True | submitted |
| trailer_attempt | PASS |  | trailer_identity_mismatch | trailer_identity_mismatch | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-04/green-trailer_attempt/trailer_attempt/observation.json events | True | submitted |
| after_review | PASS |  | stale_turn; integrate C1 only | stale_turn; integrated C1 | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-04/green-after_review/after_review/observation.json events | 否；仅允许集成 C1 | accepted |
| positive_single | PASS |  |  | integrated | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-04/positive-positive_single/positive_single/observation.json events | False | accepted |
| positive_multi | PASS |  |  | integrated | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-04/positive-positive_multi/positive_multi/observation.json events | False | accepted |
| positive_red_card | PASS |  |  | integrated | /Users/luckye/Documents/Code/a2a-wt-t081/evidence/2026-10-14-batch14/T-081/full-04/positive-positive_red_card/positive_red_card/observation.json events | False | accepted |

正例执行数：3
误拒绝数：0
原始事件与命令输出位置见 run.json 的 steps 与逐案 observation.json。
6e 是发现观察，FINDING/NO_GO 不触发全量停止，也不计拒收绿态或正例通过。
6a 待裁定；真实 Codex 回合为 0；未运行项不计通过。
