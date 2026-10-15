# T-086 执行主控决策记录

## 建票与开工（2026-10-15 UTC）

来源：T-081 6e 回归（Grok wF:p30）发现 T-077 lifecycle 冲突套件两案（CONFLICT-ACTIVE-WRITEBACK、CONFLICT-ENDED-NEW-ATTEMPT）在 main 上因 T-084 新规则返回 trailer_identity_mismatch：test_worktree_lifecycle_e2e.py commit_worker 写 Model fixture、Launch thread_id。T-084 回归仅覆盖该文件 3 案。执行主控按 T-004 自建缺陷票 bb6c0ba3（ready_by executor），worktree a2a-wt-t086（exec/t086，基于 bb6c0ba3），npm ci（外置盘缓存），spawn-helper 755。worker：T-084 作者 Grok 会话 wF:p3Z（用户指定 Grok；无 A2A 启动记录，提交由主控代做）。写入范围：tests/acceptance 中写尾注的夹具与本票证据，不改 workbench/src。T-081 待本票合入后变基、全量重跑。
