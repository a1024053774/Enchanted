# T-076-1 执行主控决定 01：批准 PLAN（2026-10-11）

`card-1/PLAN.md` 批准，按第 7 节的顺序执行。

1. **尾注**：按第 2 节执行。
   - 请求值写进 `*_REQUESTED` 环境变量。
   - 实际值由钩子从隔离 `CODEX_HOME` 里绑定的根会话 JSONL 读取。
   - 取不到实际值时写 `unknown`，不能拿请求值冒充，此时本项判 INCOMPLETE。
2. **多回合身份**：按第 3 节执行。如需在测试宿主中提供明确的受控所有者事实，只改 `workbench/tests/`；`acceptance/` 不动。若无法保留原测试的独立含义，停下报告。
3. **一致性检查器**：按第 4 节执行。发现不一致或无法重建时，保存报告后停下交给我，不改存储。按 ticket 规定，改存储另开切片。
4. **五类变异体**：按第 5 节执行。起点上已能检出的，如实登记“已有覆盖”。每个变异体在候选上都必须是业务断言失败。
5. **Hook 批准**：本卡的真实回合中，下列 hook 逐次批准，各自只做记录、只通过每会话参数安装：
   - workbench 钩子目录的 `prepare-commit-msg`；
   - Codex 的 UserPromptSubmit、Stop、PermissionRequest 三个 hook。

   完整 argv 写进 outside-sandbox.sh。
6. **真实回合**：计划用 2 个，上限 3 个。第 3 个须先问我。
7. **运行器参数**：`run_daemon_acceptance.py` 增加输出根参数，批准。默认值保持不变，旧证据不覆盖。
