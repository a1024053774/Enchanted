STATUS: INCOMPLETE
TARGET: ae54aac378d7e646b8677e1763cf604ef8a182c4
EVIDENCE:
- 上次 P1 的 L1 缺口已关闭。`workbench/tests/test_t093_login_chain.ts:199` 现将最终 group/child 明细纳入 `all_exited`。
- 原独立脚本重放 7 项全部 PASS，rc 0。group/child 最终 EPERM 均产生 `all_exited:false`、禁止删除；确认 ESRCH 的正常路径仍可清理。
- 原件：`/private/tmp/t093-r14-review-recheck-OhgZ9U/independent-green.json`；命令与退出码：同目录 `commands.json`。
- 审查结束 HEAD 未变，tracked diff 为空；project-map status 为 0 problems、0 stale。
FINDINGS:
- 本次仅复核原 P1；该 finding 已解决，无遗留项。
COUNTEREXAMPLE:
- 仅删除 group 条件：最终 group EPERM 反例命中删除业务断言，rc 2。
- 仅删除 child 条件：最终 child EPERM 反例命中删除业务断言，rc 2。
- 两份变异及输出保存在 `/private/tmp/t093-r14-review-recheck-OhgZ9U/`。
LIMITATIONS:
- 仅运行纯合成回调检查，未执行实际进程查询、sandbox、CLI、认证、网络或模型。
- 实际 counts OS/V 复验与 T-096 跨票检查仍为 INCOMPLETE；本结论不代表整票通过。
RULE:
- 已保存的 `workbench/tests/test_t093_writer_exit.mjs` 覆盖最终 group/child EPERM：任一逐项退出未确认，汇总不得放行删除。两个删条件变异证明该检查有效。
