STATUS: INCOMPLETE
TARGET: 7a5adebfcda47b10f28b8c51ecfc49dd7a490720（仅复核相对 3fca92984443d0954f1fda8fbe0ba68230c66dcc 的 alias 修复）
EVIDENCE:
- L1 alias 修复：PASS。`startController` 在原版本比较通过后捕获规范 executable_path，保留实际 argv；`processInfo` 使用捕获值，不重新解析 alias。Codex 记录既有规范路径。
- 独立运行 `test_t093_process_alias.ts`：2 项通过；合法 alias 可 release，启动后改指向其他目标被拒绝。
- 独立运行 `test_t093_process_observer.ts`：11 项通过。
- 独立运行 `node --experimental-vm-modules workbench/tests/test_t091_claude_version.mjs`：8 项及版本比较变异检查通过。
- 本次输出保存在 `/private/tmp/t093-alias-review-ibr5mh3y/{alias,observer,version}.json`。
- 候选及受审文件未变；project-map status 为 0 problems、0 stale living docs。
FINDINGS:
- 无新增阻断项。前次 panes.ts:413 的合法 alias 误拒问题已在本次 L1 范围关闭。
COUNTEREXAMPLE:
- 已保存的 process-alias-red-02 在原候选命中 `valid_alias_must_keep_foreground_identity`；修复后同一业务正例通过。
- 已保存的查询时重新解析 alias 变异，被 `different_target_must_not_take_over_identity` 拒绝。
- 本次独立运行中，删除版本比较的变异仍被版本不匹配业务断言拒绝。
LIMITATIONS:
- 完整 OS／C 权限边界及完整链路仍为 INCOMPLETE；真实 libproc、same-C primary/green、正式六场均 NOT_RUN。
- 测试模拟执行、PTY 和内核返回；未启动真实 CLI、查询真实 PID，或访问认证、网络、模型。
- 本次仅复核已确认的 alias 回归及直接版本、启动、身份绑定变化。
RULE:
- N/A：未发现需要新增规则的重复失败类别。
