# T-076-1 执行主控决定 02：outside-real-01 的回合预留核账（2026-10-11）

- 核对结果：outside-real-01 在 `card_save` 一步就被门禁拒收（`invalid_task_card`：Card ID must contain the ticket ID and a sequence number）。原因是夹具里的卡号 `T-076-1-real` 格式不合法，属于夹具错误，不是产品问题。
- 事件读回只有 `daemon_started` 一条、`request_received` 两条、`request_result` 一条；没有启动窗格，也没有起 Codex。因此实际消耗的真实回合为 **0**，隔离 home 已删除。
- 核账：outside-real-01 的“预留 2 个回合”核销为实际使用 0 个。请在预算记录里追加一条 `kind: reconciliation`，引用本决定，写明 reserved=2、actual=0、原因是夹具卡号不合法；不改写原来那条预留记录。
- 批准：把卡号改成合法格式（例如 `T-076-9`，这是一个隔离夹具 ticket，与真实 ticket 不冲突），换新标签重跑一次 real-two-turns。真实回合上限仍为 3，第 3 个使用前须先问我。RESULTS 里要如实记录 outside-real-01 这次失败。
