# T-229 各次运行的结果（由摘要 JSON 生成）

每行一次运行：名称（`rN` 为第 N 轮，`-k` 为第 k 次尝试，`base` 为基线 `59815ea30`，`mutant` 为变异），状态，未通过的检查。原始摘要、日志、截图与夹具已按只存状态的规定删除。

| run | 状态 | 未通过的检查 | 备注 |
| --- | --- | --- | --- |
| `final-agy` | PASS |  |  |
| `final-claude` | PASS |  |  |
| `final-codex` | PASS |  |  |
| `final-opencode` | PASS |  |  |
| `final-t206` | PASS |  |  |
| `green-agy-01-window-task` | FAIL |  |  |
| `green-agy-02` | PASS |  |  |
| `green-agy-03` | PASS |  |  |
| `green-claude-01-dispatch-label` | FAIL |  |  |
| `green-claude-02` | PASS |  |  |
| `green-codex-01` | PASS |  |  |
| `green-opencode-01-window-task` | FAIL |  | daemon_start 期限 |
| `green-opencode-02` | PASS |  |  |
| `green-opencode-03` | PASS |  |  |
| `mutant-attach-too-codex` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、interventions_follow_records |  |
| `mutant-ctrl-c-keeps-draft-agy` | FAIL | cleared_draft_not_recorded |  |
| `mutant-cursor-ignored-opencode` | FAIL | followed_edit_text_only |  |
| `mutant-no-claim-claude` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、interventions_follow_records |  |
| `r10-agy-1` | PASS |  |  |
| `r10-claude-1` | PASS |  |  |
| `r10-codex-1` | PASS |  |  |
| `r10-diagnostic-fails-claude-1` | PASS |  |  |
| `r10-diagnostic-fails-codex-1` | PASS |  |  |
| `r10-mutant-late-handled-claude-1` | FAIL |  | daemon_start 期限 |
| `r10-mutant-late-handled-claude-2` | FAIL | no_record_for_blocked_submission、pane_idle_after_block、dispatch_waits_for_returned_draft、late_request_refused |  |
| `r10-mutant-late-handled-codex-1` | FAIL | late_request_refused |  |
| `r10-mutant-no-claim-claude-1` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r10-mutant-no-claim-codex-1` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r10-mutant-no-deadline-claude-1` | FAIL | unrecorded_submission_not_sent_to_model、pane_idle_after_block、dispatch_waits_for_returned_draft、dispatch_after_block_delivered |  |
| `r10-mutant-no-deadline-codex-1` | FAIL | unrecorded_submission_not_sent_to_model、pane_idle_after_block、dispatch_after_block_delivered |  |
| `r10-mutant-no-restore-claude-1` | FAIL | pane_idle_after_block、dispatch_waits_for_returned_draft |  |
| `r10-mutant-no-restore-codex-1` | FAIL | pane_idle_after_block、dispatch_after_block_delivered |  |
| `r10-mutant-snapshot-overwritten-claude-1` | FAIL | pane_idle_after_block |  |
| `r10-mutant-snapshot-overwritten-codex-1` | FAIL | pane_idle_after_block、dispatch_after_block_delivered |  |
| `r10-opencode-1` | PASS |  |  |
| `r10-query-fails-claude-1` | PASS |  |  |
| `r10-query-fails-codex-1` | FAIL |  | daemon_start 期限 |
| `r10-query-fails-codex-2` | FAIL |  | daemon_start 期限 |
| `r10-query-fails-codex-3` | FAIL |  | daemon_start 期限 |
| `r10-query-fails-codex-4` | FAIL |  | daemon_start 期限 |
| `r10-record-fails-claude-1` | FAIL |  | daemon_start 期限 |
| `r10-record-fails-claude-2` | PASS |  |  |
| `r10-record-fails-codex-1` | FAIL |  | daemon_start 期限 |
| `r10-record-fails-codex-2` | PASS |  |  |
| `r10-reg-t165-ordered-1-t157` | PASS |  |  |
| `r10-reg-t165-ordered-1` | PASS |  |  |
| `r10-reg-t166-separate-1` | PASS |  |  |
| `r10-reg-t207-1` | FAIL |  | daemon_start 期限 |
| `r10-reg-t207-2` | FAIL |  | daemon_start 期限 |
| `r10-reg-t207-3` | PASS |  |  |
| `r10-reg-t216-issue-push-1` | PASS |  |  |
| `r10-reg-t216-provenance-claude-1` | PASS |  |  |
| `r10-reg-t216-provenance-codex-1` | PASS |  |  |
| `r10-request-fails-claude-1` | PASS |  |  |
| `r10-request-fails-codex-1` | PASS |  |  |
| `r10-request-hangs-claude-1` | PASS |  |  |
| `r10-request-hangs-codex-1` | PASS |  |  |
| `r10-t206-1` | PASS |  |  |
| `r10b-query-fails-codex-1` | PASS |  |  |
| `r10s-mutant-snapshot-overwritten-claude-1` | FAIL | pane_idle_after_block |  |
| `r10s-request-hangs-claude-1` | PASS |  |  |
| `r10s-request-hangs-codex-1` | PASS |  |  |
| `r11-agy-1` | PASS |  |  |
| `r11-claude-1` | PASS |  |  |
| `r11-codex-1` | FAIL |  | daemon_start 期限 |
| `r11-codex-2` | PASS |  |  |
| `r11-diagnostic-fails-claude-1` | PASS |  |  |
| `r11-diagnostic-fails-codex-1` | PASS |  |  |
| `r11-mutant-attach-too-claude-1` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r11-mutant-attach-too-codex-1` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r11-mutant-enter-starts-turn-claude-1` | FAIL | pane_idle_after_block、dispatch_waits_for_user_draft |  |
| `r11-mutant-enter-starts-turn-codex-1` | FAIL | pane_idle_after_block、dispatch_waits_for_user_draft |  |
| `r11-mutant-hook-error-passes-claude-1` | FAIL | unrecorded_submission_not_sent_to_model、dispatch_after_block_delivered |  |
| `r11-mutant-hook-error-passes-codex-1` | FAIL | unrecorded_submission_not_sent_to_model、dispatch_after_block_delivered |  |
| `r11-mutant-late-handled-claude-1` | FAIL | no_record_for_blocked_submission、pane_idle_after_block、dispatch_waits_for_user_draft、late_request_refused |  |
| `r11-mutant-late-handled-codex-1` | FAIL | no_record_for_blocked_submission、pane_idle_after_block、dispatch_waits_for_user_draft、late_request_refused |  |
| `r11-mutant-no-claim-claude-1` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r11-mutant-no-claim-codex-1` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r11-mutant-no-deadline-claude-1` | FAIL | unrecorded_submission_not_sent_to_model、dispatch_after_block_delivered |  |
| `r11-mutant-no-deadline-codex-1` | FAIL | unrecorded_submission_not_sent_to_model、dispatch_after_block_delivered |  |
| `r11-mutant-no-observer-mark-claude-1` | FAIL |  | daemon_start 期限 |
| `r11-mutant-no-observer-mark-claude-2` | FAIL | observer_failed_after_block |  |
| `r11-mutant-no-observer-mark-codex-1` | FAIL | observer_failed_after_block |  |
| `r11-opencode-1` | PASS |  |  |
| `r11-query-fails-claude-1` | PASS |  |  |
| `r11-query-fails-codex-1` | FAIL |  | daemon_start 期限 |
| `r11-query-fails-codex-2` | PASS |  |  |
| `r11-record-fails-claude-1` | PASS |  |  |
| `r11-record-fails-codex-1` | PASS |  |  |
| `r11-reg-t133-t134-1` | PASS |  |  |
| `r11-reg-t157-stale-expired-1` | PASS |  |  |
| `r11-reg-t157-stale-recover-1` | PASS |  |  |
| `r11-reg-t157-stop-input-1` | INCOMPLETE |  | daemon_start 期限 |
| `r11-reg-t157-stop-input-2` | PASS |  |  |
| `r11-reg-t165-ordered-1-t157` | PASS |  |  |
| `r11-reg-t165-ordered-1` | PASS |  |  |
| `r11-reg-t165-unrelated-stop-1-t157` | PASS |  |  |
| `r11-reg-t165-unrelated-stop-1` | PASS |  |  |
| `r11-reg-t166-absorbed-1` | PASS |  |  |
| `r11-reg-t166-separate-1` | PASS |  |  |
| `r11-reg-t167-dialog-open-1` | PASS |  |  |
| `r11-reg-t167-receipt-1` | PASS |  |  |
| `r11-reg-t207-1` | PASS |  |  |
| `r11-reg-t216-issue-push-1` | PASS |  |  |
| `r11-reg-t216-provenance-claude-1` | PASS |  |  |
| `r11-reg-t216-provenance-codex-1` | PASS |  |  |
| `r11-request-fails-claude-1` | PASS |  |  |
| `r11-request-fails-codex-1` | PASS |  |  |
| `r11-request-hangs-claude-1` | PASS |  |  |
| `r11-request-hangs-codex-1` | PASS |  |  |
| `r11-t206-1` | PASS |  |  |
| `r11s-claude-1` | PASS |  |  |
| `r11s-codex-1` | PASS |  |  |
| `r11s-request-fails-codex-1` | PASS |  |  |
| `r12-after-record-fails-claude-1` | PASS |  |  |
| `r12-after-record-fails-codex-1` | PASS |  |  |
| `r12-agy-1` | PASS |  |  |
| `r12-claude-1` | PASS |  |  |
| `r12-codex-1` | FAIL |  | daemon_start 期限 |
| `r12-codex-2` | PASS |  |  |
| `r12-diagnostic-fails-claude-1` | PASS |  |  |
| `r12-diagnostic-fails-codex-1` | PASS |  |  |
| `r12-draft-after-enter-claude-1` | PASS |  |  |
| `r12-draft-after-enter-codex-1` | PASS |  |  |
| `r12-mutant-attach-too-claude-1` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r12-mutant-attach-too-codex-1` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r12-mutant-draft-released-on-submit-claude-1` | FAIL | dispatch_waits_for_later_draft、later_draft_sent_alone |  |
| `r12-mutant-draft-released-on-submit-codex-1` | FAIL | dispatch_waits_for_later_draft、later_draft_sent_alone |  |
| `r12-mutant-enter-starts-turn-claude-1` | FAIL | pane_idle_after_block、dispatch_waits_for_user_draft |  |
| `r12-mutant-enter-starts-turn-codex-1` | FAIL | pane_idle_after_block、dispatch_waits_for_user_draft |  |
| `r12-mutant-hook-error-passes-claude-1` | FAIL | unrecorded_submission_not_sent_to_model、dispatch_after_block_delivered |  |
| `r12-mutant-hook-error-passes-codex-1` | FAIL | unrecorded_submission_not_sent_to_model、dispatch_after_block_delivered |  |
| `r12-mutant-late-handled-claude-1` | FAIL | no_record_for_blocked_submission、pane_idle_after_block、dispatch_waits_for_user_draft、late_request_refused |  |
| `r12-mutant-late-handled-codex-1` | FAIL | no_record_for_blocked_submission、pane_idle_after_block、dispatch_waits_for_user_draft、late_request_refused |  |
| `r12-mutant-no-claim-claude-1` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r12-mutant-no-claim-codex-1` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r12-mutant-no-deadline-claude-1` | FAIL | unrecorded_submission_not_sent_to_model、dispatch_after_block_delivered |  |
| `r12-mutant-no-deadline-codex-1` | FAIL | unrecorded_submission_not_sent_to_model、dispatch_after_block_delivered |  |
| `r12-mutant-no-observer-mark-claude-1` | FAIL | observer_failed_after_block |  |
| `r12-mutant-no-observer-mark-codex-1` | FAIL | observer_failed_after_block |  |
| `r12-mutant-record-then-block-a-claude-1` | FAIL | recorded_submission_sent_to_model、pane_failure_visible |  |
| `r12-mutant-record-then-block-a-codex-1` | FAIL | recorded_submission_sent_to_model、pane_failure_visible |  |
| `r12-mutant-record-then-block-r-claude-1` | FAIL |  | daemon_start 期限 |
| `r12-mutant-record-then-block-r-claude-2` | FAIL | recorded_submission_sent_to_model、pane_failure_visible |  |
| `r12-mutant-record-then-block-r-codex-1` | FAIL |  | daemon_start 期限 |
| `r12-mutant-record-then-block-r-codex-2` | FAIL | recorded_submission_sent_to_model、pane_failure_visible |  |
| `r12-opencode-1` | PASS |  |  |
| `r12-query-fails-claude-1` | FAIL |  | daemon_start 期限 |
| `r12-query-fails-claude-2` | PASS |  |  |
| `r12-query-fails-codex-1` | PASS |  |  |
| `r12-record-fails-claude-1` | PASS |  |  |
| `r12-record-fails-codex-1` | PASS |  |  |
| `r12-reg-t133-t134-1` | PASS |  |  |
| `r12-reg-t157-stale-expired-1` | PASS |  |  |
| `r12-reg-t157-stale-recover-1` | PASS |  |  |
| `r12-reg-t157-stop-input-1` | PASS |  |  |
| `r12-reg-t165-ordered-1-t157` | PASS |  |  |
| `r12-reg-t165-ordered-1` | PASS |  |  |
| `r12-reg-t165-unrelated-stop-1-t157` | PASS |  |  |
| `r12-reg-t165-unrelated-stop-1` | PASS |  |  |
| `r12-reg-t166-absorbed-1` | PASS |  |  |
| `r12-reg-t166-separate-1` | PASS |  |  |
| `r12-reg-t167-dialog-open-1` | PASS |  |  |
| `r12-reg-t167-receipt-1` | PASS |  |  |
| `r12-reg-t207-1` | PASS |  |  |
| `r12-reg-t216-issue-push-1` | PASS |  |  |
| `r12-reg-t216-provenance-claude-1` | PASS |  |  |
| `r12-reg-t216-provenance-codex-1` | PASS |  |  |
| `r12-request-fails-claude-1` | PASS |  |  |
| `r12-request-fails-codex-1` | PASS |  |  |
| `r12-request-hangs-claude-1` | PASS |  |  |
| `r12-request-hangs-codex-1` | PASS |  |  |
| `r12-result-fails-claude-1` | PASS |  |  |
| `r12-result-fails-codex-1` | PASS |  |  |
| `r12-t206-1` | PASS |  |  |
| `r13-after-record-fails-claude-1` | PASS |  |  |
| `r13-after-record-fails-codex-1` | PASS |  |  |
| `r13-agy-1` | PASS |  |  |
| `r13-base-t165-unrelated-stop-1-t157` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r13-base-t165-unrelated-stop-1` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r13-base-t165-unrelated-stop-2-t157` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r13-base-t165-unrelated-stop-2` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r13-base-t165-unrelated-stop-3-t157` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r13-base-t165-unrelated-stop-3` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r13-claude-1` | PASS |  |  |
| `r13-codex-1` | FAIL |  | daemon_start 期限 |
| `r13-codex-2` | PASS |  |  |
| `r13-composition-after-enter-claude-1` | PASS |  |  |
| `r13-composition-after-enter-codex-1` | PASS |  |  |
| `r13-diagnostic-fails-claude-1` | PASS |  |  |
| `r13-diagnostic-fails-codex-1` | PASS |  |  |
| `r13-draft-after-enter-claude-1` | PASS |  |  |
| `r13-draft-after-enter-codex-1` | PASS |  |  |
| `r13-mutant-attach-too-claude-1` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r13-mutant-attach-too-codex-1` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r13-mutant-draft-released-on-submit-c-claude-1` | FAIL | dispatch_waits_for_later_draft |  |
| `r13-mutant-draft-released-on-submit-c-codex-1` | FAIL | dispatch_waits_for_later_draft |  |
| `r13-mutant-draft-released-on-submit-claude-1` | FAIL | dispatch_waits_for_later_draft、later_draft_sent_alone |  |
| `r13-mutant-draft-released-on-submit-codex-1` | FAIL | dispatch_waits_for_later_draft、later_draft_sent_alone |  |
| `r13-mutant-enter-starts-turn-claude-1` | FAIL | pane_idle_after_block、dispatch_waits_for_user_draft、dispatch_after_block_delivered |  |
| `r13-mutant-enter-starts-turn-codex-1` | FAIL | pane_idle_after_block、dispatch_waits_for_user_draft、dispatch_after_block_delivered |  |
| `r13-mutant-hook-error-passes-claude-1` | FAIL | unrecorded_submission_not_sent_to_model、dispatch_after_block_delivered |  |
| `r13-mutant-hook-error-passes-codex-1` | FAIL | unrecorded_submission_not_sent_to_model、dispatch_after_block_delivered |  |
| `r13-mutant-late-handled-claude-1` | FAIL | no_record_for_blocked_submission、pane_idle_after_block、dispatch_waits_for_user_draft、late_request_refused |  |
| `r13-mutant-late-handled-codex-1` | FAIL | no_record_for_blocked_submission、pane_idle_after_block、dispatch_waits_for_user_draft、late_request_refused |  |
| `r13-mutant-no-claim-claude-1` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r13-mutant-no-claim-codex-1` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r13-mutant-no-deadline-claude-1` | FAIL | unrecorded_submission_not_sent_to_model、dispatch_after_block_delivered |  |
| `r13-mutant-no-deadline-codex-1` | FAIL | unrecorded_submission_not_sent_to_model、dispatch_after_block_delivered |  |
| `r13-mutant-no-observer-mark-claude-1` | FAIL | observer_failed_after_block |  |
| `r13-mutant-no-observer-mark-codex-1` | FAIL | observer_failed_after_block |  |
| `r13-mutant-record-then-block-a-claude-1` | FAIL | recorded_submission_sent_to_model、pane_failure_visible |  |
| `r13-mutant-record-then-block-a-codex-1` | FAIL | recorded_submission_sent_to_model、pane_failure_visible |  |
| `r13-mutant-record-then-block-r-claude-1` | FAIL | recorded_submission_sent_to_model、pane_failure_visible |  |
| `r13-mutant-record-then-block-r-codex-1` | FAIL |  | daemon_start 期限 |
| `r13-mutant-record-then-block-r-codex-2` | FAIL | recorded_submission_sent_to_model、pane_failure_visible |  |
| `r13-opencode-1` | PASS |  |  |
| `r13-query-fails-claude-1` | PASS |  |  |
| `r13-query-fails-codex-1` | FAIL |  | daemon_start 期限 |
| `r13-query-fails-codex-2` | PASS |  |  |
| `r13-record-fails-claude-1` | PASS |  |  |
| `r13-record-fails-codex-1` | PASS |  |  |
| `r13-reg-t133-t134-1` | PASS |  |  |
| `r13-reg-t157-stale-expired-1` | PASS |  |  |
| `r13-reg-t157-stale-recover-1` | PASS |  |  |
| `r13-reg-t157-stop-input-1` | PASS |  |  |
| `r13-reg-t165-ordered-1-t157` | PASS |  |  |
| `r13-reg-t165-ordered-1` | PASS |  |  |
| `r13-reg-t165-unrelated-stop-1-t157` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r13-reg-t165-unrelated-stop-1` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r13-reg-t165-unrelated-stop-2-t157` | PASS |  |  |
| `r13-reg-t165-unrelated-stop-2` | PASS |  |  |
| `r13-reg-t165-unrelated-stop-3-t157` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r13-reg-t165-unrelated-stop-3` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r13-reg-t166-absorbed-1` | PASS |  |  |
| `r13-reg-t166-separate-1` | PASS |  |  |
| `r13-reg-t167-dialog-open-1` | PASS |  |  |
| `r13-reg-t167-receipt-1` | PASS |  |  |
| `r13-reg-t207-1` | PASS |  |  |
| `r13-reg-t216-issue-push-1` | PASS |  |  |
| `r13-reg-t216-provenance-claude-1` | PASS |  |  |
| `r13-reg-t216-provenance-codex-1` | PASS |  |  |
| `r13-request-fails-claude-1` | PASS |  |  |
| `r13-request-fails-codex-1` | PASS |  |  |
| `r13-request-hangs-claude-1` | PASS |  |  |
| `r13-request-hangs-codex-1` | PASS |  |  |
| `r13-result-fails-claude-1` | PASS |  |  |
| `r13-result-fails-codex-1` | FAIL |  | daemon_start 期限 |
| `r13-result-fails-codex-2` | PASS |  |  |
| `r13-t206-1` | PASS |  |  |
| `r14-after-record-fails-claude-1` | PASS |  |  |
| `r14-after-record-fails-codex-1` | PASS |  |  |
| `r14-agy-1` | PASS |  |  |
| `r14-base-t157-stop-input-1` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r14-base-t157-stop-input-2` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r14-base-t165-ordered-1-t157` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r14-base-t165-ordered-1` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r14-base-t165-ordered-2-t157` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r14-base-t165-ordered-2` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r14-claude-1` | PASS |  |  |
| `r14-codex-1` | PASS |  |  |
| `r14-composition-after-enter-claude-1` | PASS |  |  |
| `r14-composition-after-enter-codex-1` | PASS |  |  |
| `r14-diagnostic-fails-claude-1` | PASS |  |  |
| `r14-diagnostic-fails-codex-1` | PASS |  |  |
| `r14-draft-after-enter-claude-1` | PASS |  |  |
| `r14-draft-after-enter-codex-1` | PASS |  |  |
| `r14-esc-then-submit-codex-1` | PASS |  |  |
| `r14-mutant-attach-too-claude-1` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r14-mutant-attach-too-codex-1` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r14-mutant-draft-released-on-submit-c-claude-1` | FAIL | dispatch_waits_for_later_draft |  |
| `r14-mutant-draft-released-on-submit-c-codex-1` | FAIL | dispatch_waits_for_later_draft |  |
| `r14-mutant-draft-released-on-submit-claude-1` | FAIL | dispatch_waits_for_later_draft、later_draft_sent_alone |  |
| `r14-mutant-draft-released-on-submit-codex-1` | FAIL | dispatch_waits_for_later_draft、later_draft_sent_alone |  |
| `r14-mutant-enter-starts-turn-claude-1` | FAIL | pane_idle_after_block、dispatch_waits_for_user_draft、dispatch_after_block_delivered |  |
| `r14-mutant-enter-starts-turn-codex-1` | FAIL | pane_idle_after_block、dispatch_waits_for_user_draft、dispatch_after_block_delivered |  |
| `r14-mutant-esc-reuses-turn-codex-1` | FAIL | user_turn_hooks_and_stop_accepted、user_turn_is_its_own_submission |  |
| `r14-mutant-hook-error-passes-claude-1` | FAIL | unrecorded_submission_not_sent_to_model、dispatch_after_block_delivered |  |
| `r14-mutant-hook-error-passes-codex-1` | FAIL | unrecorded_submission_not_sent_to_model、dispatch_after_block_delivered |  |
| `r14-mutant-late-handled-claude-1` | FAIL | no_record_for_blocked_submission、pane_idle_after_block、dispatch_waits_for_user_draft、late_request_refused |  |
| `r14-mutant-late-handled-codex-1` | FAIL | no_record_for_blocked_submission、pane_idle_after_block、dispatch_waits_for_user_draft、late_request_refused |  |
| `r14-mutant-no-claim-claude-1` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r14-mutant-no-claim-codex-1` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r14-mutant-no-deadline-claude-1` | FAIL | unrecorded_submission_not_sent_to_model、dispatch_after_block_delivered |  |
| `r14-mutant-no-deadline-codex-1` | FAIL | unrecorded_submission_not_sent_to_model、dispatch_after_block_delivered |  |
| `r14-mutant-no-observer-mark-claude-1` | FAIL | observer_failed_after_block |  |
| `r14-mutant-no-observer-mark-codex-1` | FAIL | observer_failed_after_block |  |
| `r14-mutant-record-then-block-a-claude-1` | FAIL | recorded_submission_sent_to_model、pane_failure_visible |  |
| `r14-mutant-record-then-block-a-codex-1` | FAIL | recorded_submission_sent_to_model、pane_failure_visible |  |
| `r14-mutant-record-then-block-r-claude-1` | FAIL | recorded_submission_sent_to_model、pane_failure_visible |  |
| `r14-mutant-record-then-block-r-codex-1` | FAIL | recorded_submission_sent_to_model、pane_failure_visible |  |
| `r14-opencode-1` | PASS |  |  |
| `r14-query-fails-claude-1` | FAIL |  | daemon_start 期限 |
| `r14-query-fails-claude-2` | PASS |  |  |
| `r14-query-fails-codex-1` | PASS |  |  |
| `r14-record-fails-claude-1` | PASS |  |  |
| `r14-record-fails-codex-1` | PASS |  |  |
| `r14-reg-t133-t134-1` | PASS |  |  |
| `r14-reg-t157-stale-expired-1` | PASS |  |  |
| `r14-reg-t157-stale-recover-1` | PASS |  |  |
| `r14-reg-t157-stop-input-1` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r14-reg-t165-ordered-1-t157` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r14-reg-t165-ordered-1` | INCOMPLETE | positive_returns_idle_without_regular_recovery |  |
| `r14-reg-t165-unrelated-stop-1-t157` | PASS |  |  |
| `r14-reg-t165-unrelated-stop-1` | PASS |  |  |
| `r14-reg-t166-absorbed-1` | PASS |  |  |
| `r14-reg-t166-separate-1` | PASS |  |  |
| `r14-reg-t167-dialog-open-1` | PASS |  |  |
| `r14-reg-t167-receipt-1` | PASS |  |  |
| `r14-reg-t207-1` | PASS |  |  |
| `r14-reg-t207-mutant-user-turn-not-marked-1` | FAIL | delivered_at_turn_end、user_turn_hooks_trusted |  |
| `r14-reg-t216-issue-push-1` | PASS |  |  |
| `r14-reg-t216-provenance-claude-1` | PASS |  |  |
| `r14-reg-t216-provenance-codex-1` | PASS |  |  |
| `r14-request-fails-claude-1` | PASS |  |  |
| `r14-request-fails-codex-1` | PASS |  |  |
| `r14-request-hangs-claude-1` | PASS |  |  |
| `r14-request-hangs-codex-1` | PASS |  |  |
| `r14-result-fails-claude-1` | PASS |  |  |
| `r14-result-fails-codex-1` | PASS |  |  |
| `r14-t206-1` | PASS |  |  |
| `r14s-esc-then-submit-codex-1` | PASS |  |  |
| `r14s-mutant-esc-reuses-turn-codex-1` | FAIL | user_turn_is_its_own_submission |  |
| `r3-claude` | PASS |  |  |
| `r3-codex` | PASS |  |  |
| `r3-fails-claude` | PASS |  |  |
| `r3-fails-codex` | PASS |  |  |
| `r3-final-agy` | PASS |  |  |
| `r3-final-opencode` | PASS |  |  |
| `r3-final-t206` | PASS |  |  |
| `r3-mutant-no-block-claude` | FAIL | unrecorded_submission_not_sent_to_model |  |
| `r3-mutant-no-block-codex` | FAIL | unrecorded_submission_not_sent_to_model |  |
| `r3-mutant-no-claim-codex` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r3-reg-t157` | PASS |  |  |
| `r3-reg-t165-ordered-t157` | PASS |  |  |
| `r3-reg-t165-ordered` | PASS |  |  |
| `r3-reg-t166-absorbed` | PASS |  |  |
| `r3-reg-t166-separate` | PASS |  |  |
| `r3-reg-t187-opencode` | PASS | card_accepts_cli、worker_argv、worker_env、submitted、sidebar_running_during_turn、sidebar_idle_after_turn、verify_started、review_passed、review_checkout_read_only、integrated、trailers_unknown_model_effort |  |
| `r3-reg-t207` | PASS |  |  |
| `r3-reg-t216-issue-push` | PASS |  |  |
| `r3-reg-t216-provenance-claude-01-daemon-start` | INCOMPLETE |  | daemon_start 期限 |
| `r3-reg-t216-provenance-claude-02` | PASS |  |  |
| `r4-claude` | PASS |  |  |
| `r4-codex` | PASS |  |  |
| `r4-diag-claude` | PASS |  |  |
| `r4-diag-codex` | PASS |  |  |
| `r4-fails-claude` | PASS |  |  |
| `r4-fails-codex` | PASS |  |  |
| `r4-mutant-diagnostic-unguarded-claude` | FAIL |  |  |
| `r4-mutant-diagnostic-unguarded-codex` | FAIL |  |  |
| `r4-mutant-no-block-claude` | FAIL | unrecorded_submission_not_sent_to_model |  |
| `r4-mutant-no-claim-codex` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r4-reg-t216-provenance-claude` | PASS |  |  |
| `r4-reg-t216-provenance-codex` | PASS |  |  |
| `r4-t206` | PASS |  |  |
| `r4b-diag-claude` | PASS |  |  |
| `r4b-diag-codex` | PASS |  |  |
| `r4b-mutant-diagnostic-unguarded-claude` | FAIL | diagnostic_failure_logged、unrecorded_submission_not_sent_to_model |  |
| `r4b-mutant-diagnostic-unguarded-codex` | FAIL | diagnostic_failure_logged、unrecorded_submission_not_sent_to_model |  |
| `r5-agy` | PASS |  |  |
| `r5-claude-02` | FAIL |  | daemon_start 期限 |
| `r5-claude-03` | PASS |  |  |
| `r5-claude` | FAIL |  | daemon_start 期限 |
| `r5-codex` | PASS |  |  |
| `r5-diagnostic-fails-claude` | PASS |  |  |
| `r5-diagnostic-fails-codex` | PASS |  |  |
| `r5-mutant-attach-too-codex` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r5-mutant-hook-error-passes-claude` | FAIL | unrecorded_submission_not_sent_to_model |  |
| `r5-mutant-hook-error-passes-codex-02` | FAIL | unrecorded_submission_not_sent_to_model |  |
| `r5-mutant-hook-error-passes-codex` | FAIL |  | daemon_start 期限 |
| `r5-mutant-no-claim-codex` | FAIL | edited_message_one_record_without_keys、dispatches_not_user_input、claimed_dispatch_resent_by_user_is_recorded、interventions_follow_records |  |
| `r5-mutant-no-observer-mark-claude` | FAIL | observer_failed_after_block |  |
| `r5-opencode` | PASS |  |  |
| `r5-query-fails-claude` | PASS |  |  |
| `r5-query-fails-codex` | PASS |  |  |
| `r5-record-fails-claude` | PASS |  |  |
| `r5-record-fails-codex` | PASS |  |  |
| `r5-reg-t157` | PASS |  |  |
| `r5-reg-t165-ordered-t157` | PASS |  |  |
| `r5-reg-t165-ordered` | PASS |  |  |
| `r5-reg-t166-absorbed` | PASS |  |  |
| `r5-reg-t166-separate` | PASS |  |  |
| `r5-reg-t187-opencode` | PASS | card_accepts_cli、worker_argv、worker_env、submitted、sidebar_running_during_turn、sidebar_idle_after_turn、verify_started、review_passed、review_checkout_read_only、integrated、trailers_unknown_model_effort |  |
| `r5-reg-t207` | PASS |  |  |
| `r5-reg-t216-issue-push` | PASS |  |  |
| `r5-reg-t216-provenance-claude` | PASS |  |  |
| `r5-reg-t216-provenance-codex` | PASS |  |  |
| `r5-request-fails-claude` | PASS |  |  |
| `r5-request-fails-codex-02` | PASS |  |  |
| `r5-request-fails-codex` | FAIL |  | daemon_start 期限 |
| `r5-t108-questions-base` | INCOMPLETE |  |  |
| `r5-t108-questions` | INCOMPLETE |  |  |
| `r5-t206` | PASS |  |  |
| `r6-claude` | PASS |  |  |
| `r6-diagnostic-fails-claude` | PASS |  |  |
| `r6-mutant-no-deadline-claude` | FAIL | unrecorded_submission_not_sent_to_model |  |
| `r6-mutant-no-deadline-codex` | FAIL | unrecorded_submission_not_sent_to_model |  |
| `r6-query-fails-claude` | FAIL |  | daemon_start 期限 |
| `r6-record-fails-claude` | PASS |  |  |
| `r6-record-fails-codex` | FAIL |  | daemon_start 期限 |
| `r6-request-fails-claude` | PASS |  |  |
| `r6-request-hangs-claude` | PASS |  |  |
| `r6-request-hangs-codex` | FAIL |  |  |
| `r6b-codex` | PASS |  |  |
| `r6b-diagnostic-fails-codex` | PASS |  |  |
| `r6b-query-fails-claude` | PASS |  |  |
| `r6b-query-fails-codex` | PASS |  |  |
| `r6b-record-fails-codex` | PASS |  |  |
| `r6b-reg-t165-ordered-t157` | PASS |  |  |
| `r6b-reg-t165-ordered` | PASS |  |  |
| `r6b-reg-t166-separate` | PASS |  |  |
| `r6b-reg-t207` | PASS |  |  |
| `r6b-reg-t216-issue-push` | PASS |  |  |
| `r6b-reg-t216-provenance-claude` | PASS |  |  |
| `r6b-reg-t216-provenance-codex` | PASS |  |  |
| `r6b-request-fails-codex-02` | PASS |  |  |
| `r6b-request-fails-codex` | FAIL |  | daemon_start 期限 |
| `r6b-request-hangs-codex-02` | FAIL |  | daemon_start 期限 |
| `r6b-request-hangs-codex-03` | PASS |  |  |
| `r6b-request-hangs-codex` | FAIL |  | daemon_start 期限 |
| `r6b-t206` | PASS |  |  |
| `r7-claude` | PASS |  |  |
| `r7-codex` | FAIL |  | daemon_start 期限 |
| `r7-diagnostic-fails-claude` | PASS |  |  |
| `r7-diagnostic-fails-codex` | PASS |  |  |
| `r7-mutant-late-handled-claude` | FAIL | no_record_for_blocked_submission、late_request_refused、no_turn_for_blocked_submission |  |
| `r7-mutant-late-handled-codex` | FAIL | no_record_for_blocked_submission、late_request_refused、no_turn_for_blocked_submission |  |
| `r7-mutant-no-deadline-claude` | FAIL | unrecorded_submission_not_sent_to_model、no_turn_for_blocked_submission |  |
| `r7-mutant-no-deadline-codex` | FAIL | unrecorded_submission_not_sent_to_model |  |
| `r7-query-fails-claude` | FAIL |  | daemon_start 期限 |
| `r7-query-fails-codex` | FAIL |  | daemon_start 期限 |
| `r7-record-fails-claude` | FAIL |  | daemon_start 期限 |
| `r7-record-fails-codex` | PASS |  |  |
| `r7-reg-t165-ordered-t157` | PASS |  |  |
| `r7-reg-t165-ordered` | PASS |  |  |
| `r7-reg-t166-separate` | INCOMPLETE |  | daemon_start 期限 |
| `r7-reg-t207` | PASS |  |  |
| `r7-reg-t216-issue-push` | INCOMPLETE |  | daemon_start 期限 |
| `r7-reg-t216-provenance-claude` | PASS |  |  |
| `r7-reg-t216-provenance-codex` | PASS |  |  |
| `r7-request-fails-claude` | FAIL |  | daemon_start 期限 |
| `r7-request-fails-codex` | PASS |  |  |
| `r7-request-hangs-claude` | FAIL | no_turn_for_blocked_submission |  |
| `r7-request-hangs-codex` | FAIL |  | daemon_start 期限 |
| `r7-t206` | PASS |  |  |
| `r7b-codex` | FAIL |  | daemon_start 期限 |
| `r7b-mutant-late-handled-claude` | FAIL | no_record_for_blocked_submission、late_request_refused、no_turn_for_blocked_submission |  |
| `r7b-query-fails-claude` | PASS |  |  |
| `r7b-query-fails-codex` | FAIL |  | daemon_start 期限 |
| `r7b-record-fails-claude` | FAIL |  | daemon_start 期限 |
| `r7b-reg-t166-separate` | PASS |  |  |
| `r7b-reg-t216-issue-push` | PASS |  |  |
| `r7b-request-fails-claude` | FAIL |  | daemon_start 期限 |
| `r7b-request-hangs-claude` | FAIL |  | daemon_start 期限 |
| `r7b-request-hangs-codex` | FAIL |  | daemon_start 期限 |
| `r7c-request-hangs-claude-1` | FAIL |  | daemon_start 期限 |
| `r7d-codex-1` | PASS |  |  |
| `r7d-query-fails-codex-1` | FAIL |  | daemon_start 期限 |
| `r7d-query-fails-codex-2` | FAIL |  | daemon_start 期限 |
| `r7d-query-fails-codex-3` | FAIL |  | daemon_start 期限 |
| `r7d-record-fails-claude-1` | PASS |  |  |
| `r7d-request-fails-claude-1` | FAIL |  | daemon_start 期限 |
| `r7d-request-fails-claude-2` | PASS |  |  |
| `r7d-request-hangs-claude-1` | FAIL |  | daemon_start 期限 |
| `r7d-request-hangs-claude-2` | FAIL |  | daemon_start 期限 |
| `r7d-request-hangs-claude-3` | PASS |  |  |
| `r7d-request-hangs-codex-1` | FAIL |  | daemon_start 期限 |
| `r7d-request-hangs-codex-2` | FAIL | no_turn_for_blocked_submission |  |
| `r7e-mutant-late-handled-codex-1` | FAIL | no_record_for_blocked_submission、late_request_refused |  |
| `r7e-query-fails-codex-1` | PASS |  |  |
| `r7e-request-hangs-codex-1` | FAIL |  | daemon_start 期限 |
| `r7e-request-hangs-codex-2` | FAIL |  | daemon_start 期限 |
| `r7e-request-hangs-codex-3` | FAIL |  | daemon_start 期限 |
| `r7f-request-hangs-codex-1` | FAIL |  | daemon_start 期限 |
| `r7f-request-hangs-codex-2` | PASS |  |  |
| `r8-claude-1` | PASS |  |  |
| `r8-codex-1` | PASS |  |  |
| `r8-diagnostic-fails-claude-1` | FAIL |  |  |
| `r8-diagnostic-fails-codex-1` | FAIL |  |  |
| `r8-mutant-late-handled-claude-1` | FAIL |  | daemon_start 期限 |
| `r8-mutant-late-handled-claude-2` | FAIL |  | daemon_start 期限 |
| `r8-mutant-late-handled-claude-3` | FAIL | no_record_for_blocked_submission、pane_idle_after_block、dispatch_after_block_delivered、late_request_refused |  |
| `r8-mutant-late-handled-codex-1` | FAIL |  | daemon_start 期限 |
| `r8-mutant-late-handled-codex-2` | FAIL | no_record_for_blocked_submission、pane_idle_after_block、dispatch_after_block_delivered、late_request_refused |  |
| `r8-mutant-no-deadline-claude-1` | FAIL |  | daemon_start 期限 |
| `r8-mutant-no-deadline-claude-2` | FAIL | unrecorded_submission_not_sent_to_model |  |
| `r8-mutant-no-deadline-codex-1` | FAIL | unrecorded_submission_not_sent_to_model |  |
| `r8-mutant-no-restore-claude-1` | FAIL |  | daemon_start 期限 |
| `r8-mutant-no-restore-claude-2` | FAIL | pane_idle_after_block、dispatch_after_block_delivered |  |
| `r8-mutant-no-restore-codex-1` | FAIL | pane_idle_after_block、dispatch_after_block_delivered |  |
| `r8-query-fails-claude-1` | PASS |  |  |
| `r8-query-fails-codex-1` | PASS |  |  |
| `r8-record-fails-claude-1` | FAIL |  | daemon_start 期限 |
| `r8-record-fails-claude-2` | FAIL |  | daemon_start 期限 |
| `r8-record-fails-claude-3` | PASS |  |  |
| `r8-record-fails-codex-1` | FAIL |  | daemon_start 期限 |
| `r8-record-fails-codex-2` | PASS |  |  |
| `r8-reg-t165-ordered-1-t157` | PASS |  |  |
| `r8-reg-t165-ordered-1` | PASS |  |  |
| `r8-reg-t166-separate-1` | INCOMPLETE |  | daemon_start 期限 |
| `r8-reg-t207-1` | PASS |  |  |
| `r8-reg-t216-issue-push-1` | INCOMPLETE |  | daemon_start 期限 |
| `r8-reg-t216-issue-push-2` | INCOMPLETE |  | daemon_start 期限 |
| `r8-reg-t216-issue-push-3` | PASS |  |  |
| `r8-reg-t216-provenance-claude-1` | INCOMPLETE |  | daemon_start 期限 |
| `r8-reg-t216-provenance-claude-2` | PASS |  |  |
| `r8-reg-t216-provenance-codex-1` | PASS |  |  |
| `r8-request-fails-claude-1` | FAIL |  | daemon_start 期限 |
| `r8-request-fails-claude-2` | FAIL | dispatch_after_block_delivered |  |
| `r8-request-fails-codex-1` | PASS |  |  |
| `r8-request-hangs-claude-1` | FAIL | dispatch_after_block_delivered |  |
| `r8-request-hangs-codex-1` | PASS |  |  |
| `r8-t206-1` | PASS |  |  |
| `r8s-record-fails-codex` | FAIL |  | daemon_start 期限 |
| `r8s-request-fails-claude` | FAIL |  | daemon_start 期限 |
| `r8s2-diagnostic-fails-claude-1` | FAIL |  | daemon_start 期限 |
| `r8s2-diagnostic-fails-claude-2` | PASS |  |  |
| `r8s2-request-fails-claude-1` | FAIL |  | daemon_start 期限 |
| `r8s2-request-fails-claude-2` | FAIL |  | daemon_start 期限 |
| `r8s2-request-fails-claude-3` | PASS |  |  |
| `r9-agy-1` | PASS |  |  |
| `r9-claude-1` | FAIL |  | daemon_start 期限 |
| `r9-claude-2` | PASS |  |  |
| `r9-codex-1` | PASS |  |  |
| `r9-diagnostic-fails-claude-1` | PASS |  |  |
| `r9-diagnostic-fails-codex-1` | PASS |  |  |
| `r9-mutant-late-handled-claude-1` | FAIL |  | daemon_start 期限 |
| `r9-mutant-late-handled-claude-2` | FAIL | no_record_for_blocked_submission、pane_idle_after_block、dispatch_waits_for_returned_draft、late_request_refused |  |
| `r9-mutant-late-handled-codex-1` | FAIL | no_record_for_blocked_submission、pane_idle_after_block、dispatch_after_block_delivered、late_request_refused |  |
| `r9-mutant-no-deadline-claude-1` | FAIL | unrecorded_submission_not_sent_to_model、dispatch_after_block_delivered |  |
| `r9-mutant-no-deadline-codex-1` | FAIL | unrecorded_submission_not_sent_to_model、dispatch_after_block_delivered |  |
| `r9-mutant-no-restore-claude-1` | FAIL |  | daemon_start 期限 |
| `r9-mutant-no-restore-claude-2` | FAIL | pane_idle_after_block、dispatch_waits_for_returned_draft |  |
| `r9-mutant-no-restore-codex-1` | FAIL | pane_idle_after_block、dispatch_after_block_delivered |  |
| `r9-opencode-1` | PASS |  |  |
| `r9-query-fails-claude-1` | FAIL |  | daemon_start 期限 |
| `r9-query-fails-claude-2` | PASS |  |  |
| `r9-query-fails-codex-1` | FAIL |  | daemon_start 期限 |
| `r9-query-fails-codex-2` | PASS |  |  |
| `r9-record-fails-claude-1` | PASS |  |  |
| `r9-record-fails-codex-1` | FAIL |  | daemon_start 期限 |
| `r9-record-fails-codex-2` | FAIL |  | daemon_start 期限 |
| `r9-record-fails-codex-3` | PASS |  |  |
| `r9-reg-t165-ordered-1-t157` | PASS |  |  |
| `r9-reg-t165-ordered-1` | PASS |  |  |
| `r9-reg-t166-separate-1` | PASS |  |  |
| `r9-reg-t207-1` | PASS |  |  |
| `r9-reg-t216-issue-push-1` | INCOMPLETE |  | daemon_start 期限 |
| `r9-reg-t216-issue-push-2` | PASS |  |  |
| `r9-reg-t216-provenance-claude-1` | PASS |  |  |
| `r9-reg-t216-provenance-codex-1` | PASS |  |  |
| `r9-request-fails-claude-1` | PASS |  |  |
| `r9-request-fails-codex-1` | PASS |  |  |
| `r9-request-hangs-claude-1` | PASS |  |  |
| `r9-request-hangs-codex-1` | FAIL |  | daemon_start 期限 |
| `r9-request-hangs-codex-2` | FAIL |  | daemon_start 期限 |
| `r9-request-hangs-codex-3` | PASS |  |  |
| `r9-t206-1` | PASS |  |  |
| `red-agy` | FAIL | followed_edit_text_only、unfollowed_key_marked_uncertain_without_keys |  |
| `red-claude` | FAIL | edited_message_one_record_without_keys、history_recall_records_actual_text、dispatches_not_user_input、interventions_follow_records |  |
| `red-codex` | FAIL | edited_message_one_record_without_keys、history_recall_records_actual_text、dispatches_not_user_input、interventions_follow_records |  |
| `red-opencode` | FAIL | followed_edit_text_only、unfollowed_key_marked_uncertain_without_keys |  |
| `reg-t157` | PASS |  |  |
| `reg-t165-ordered-t157` | PASS |  |  |
| `reg-t165-ordered` | PASS |  |  |
| `reg-t166-absorbed` | PASS |  |  |
| `reg-t166-separate` | PASS |  |  |
| `reg-t187-opencode` | PASS | card_accepts_cli、worker_argv、worker_env、submitted、sidebar_running_during_turn、sidebar_idle_after_turn、verify_started、review_passed、review_checkout_read_only、integrated、trailers_unknown_model_effort |  |
| `reg-t207` | PASS |  |  |
| `reg-t216-issue-push` | PASS |  |  |
| `reg-t216-provenance-claude` | PASS |  |  |
| `t206-green` | PASS |  |  |
| `t206-mutant-record-every-key` | FAIL | one_record_for_first_message、one_record_for_edited_message、cleared_draft_and_esc_not_recorded、interventions_follow_records |  |
