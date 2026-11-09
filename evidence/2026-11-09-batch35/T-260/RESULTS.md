# T-260 结果记录（重新打开问题）

由 Claude Code 会话 `8be1abdd-5af9-4023-bff8-cbc0f40d9a84` 在本会话里直接修复（用户：“不用 codex 了,你自己做完这些部分结束”）。

- 缺陷：问题卡的“重新打开”发送 `reopen`，但主进程 `a2a:issue-dispose` 的白名单只接受 `close`、`snooze`，请求到不了门禁。
- 修复：`workbench/app/main.ts` 的白名单加上 `reopen`；`preload.ts`、`renderer.tsx` 补上对应的动作类型。门禁本来就支持 `reopen`，状态推导和计数都没有改。
- 测试：`workbench/tests/test_t260_issue_states_e2e.py`。它就是 2026-11-08 保存的外部复现测试 `evidence/2026-11-08-batch34/T-260/controller/external-test-01.py`，原样搬进 tests 目录，没有改动。

| 运行 | 结果 | 文件 |
|---|---|---|
| 父版本 `46fecff43` | FAIL：在界面里重新打开后，问题仍为“已关闭”；后台计数 8，期望 9 | `red-parent-01.json` |
| 修复后 | PASS，64 项 | `green-01.json` |

未做：独立审查、Enchanted Test 打包窗口验证（用户本次要求不再用 Codex）。
