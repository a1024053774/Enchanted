# 从 tar 独立核对第 2 场失败原件

此步骤由主控只读外置归档完成，不操作现场。未审阅前 `failed-scene-review-template.json` 保持INCOMPLETE/null，不能凭本清单给PASS。

- 核对 bundle 的 root/source、archive路径/字节数/成员清单；标准 `verify_archive(staging, archive)` 必须对全部成员类型和字节通过。确认指针可逐项定位，脱敏span有记录，无认证头/凭据值。真实系统提示中“authorization”普通单词不是认证头，按字段/原件结构判断。
- 从每个 `files/roles/<role>/http-exchanges/*.request.bin` 的实际POST元数据、响应字节、complete/error统计；与标准readback.counts相等。保留executor首条 `C_executor_hold_deadline` 未完整响应、后续409 `dispatch_replayed`，不把失败POST排除。当前诊断3/11为先前观察，最终计数按tar，不固定为成功预算。
- 从 ideation HTTP0002 的真实 tool_result 提取 queued=true、delivered=false、request_id **95058fd0-1e9d-4028-b1c1-f45845dd3584**，按同ID关联停机前 live-rows.relay_requests 与 relay_results；不在tool_result合成stop。
- live-rows.inbox_records 原 stop **bfa23030-9da9-413f-87fc-e7cb81317987**，created_at **2026-10-17T01:06:15.258Z**，ideation→executor；thread **dab3ce0e-5481-472d-9617-b02bd07f801b**、attempt **cccb5ef6-4fdb-40f0-9a08-9692760d8ab8**。实际Stop/relay结果与delivery可追到同一entry；如未delivered或不一致就停止，不补事件。原clock-origin与settlement保留，不重新取起点。
- 从HTTP/hook及terminal事件核对C-I1批准/实际一次Enter→真实工具→Stop；C-I2只到tool_use/permission_wait，原permission草稿未签，`execute-02/result.json` 与外层 `timed-01/result.json` 均保存 `unexpected_daemon_descendants`；C-I2不得有terminal Enter/C-I3中断/ack。将实际C-I2 Enter数填入审阅字段，必须为0才允许finish预检通过。
- `files/target/received.bin` 与baseline逐字节相等，target_delta_hex为空；没有本场stop的ack、没有本场emergency_interrupt_requested。若实际有差异，保持BLOCKED，不改清单期待来放行。
- 保留原九owner/process_graph、当前probe两次原ps和诊断选行；明确**失败当时ps未保存，历史额外进程身份仍未知**。当前probe不是故障时快照，不能将它写成已恢复原始进程集合。
- 从snapshot.records按source路径定位本轮追加的timed-01与forensic原件，不依赖evidence/<n>固定下标。成员不存在、原件被截断、源变化、redaction不可核对均停下，不签readback。

审阅通过后，复制模板字段到新的 `../09c-attempt-2-raw-readback-01/failed-scene-review.json`，填写真实counts/no_ack/C_I2_Enter_count/target_delta_hex、来源成员路径、批准人和引用。该PASS仅表示失败原件保留与关联完整；**09C第2场始终INCOMPLETE**。然后分别签标准readback.json，再执行05与06。
