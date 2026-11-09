# T-270 结果：任务已结束后的未决问题退出“等你决定”

状态：PASS

- 绿态：`node workbench/tests/test_t270_integrated_issues.mjs` → `green-01.json`，9 项全过（已集成、已升级、已放弃任务的问题读成“可能已随任务结束失效”；未结束与审查中任务不变；计数为 0；原因记录；只有用户关闭且记为用户输入）。
- 红态：同一测试读父版本 `core.ts` → `red-parent-01.txt`，`sys-old-attempt`、`worker-current` 仍为“等你决定”。
- 正式数据只读副本：改动前 `waiting_total` 为 5（会话中输出，原文件未保留）；改动后 `real-copy-after.json` 为 0，a2a+T-249-2 的 5 条读成“可能已随任务结束失效”。
- 回归：`test_t260_issue_states_e2e.py` 全过，摘要见 `t260-regression.json`。
