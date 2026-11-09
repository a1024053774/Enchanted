# 本轮跟进记录

- T-266 范围外：既有 `test_t093_process_snapshot.py:65` 的严格期望缺少 `started` 字段；worker 保留 `process-snapshot-failure-01.json`。本轮未修改该测试或实现。
- T-266 范围外：旧诊断脚本请求已不存在的 `pane_release`；外部执行父版与候选都在模块链接阶段退出 1，尚未到 pane_release 断言，原输出在 T-266 worker 的 `external-diagnostics-*-01-command.json`。不能计作回归通过，后续单独处置。
- T-250 原 attempt 启动核对发生 `codex_startup_failed: SyntaxError: Unexpected end of JSON input`，随后进程查询识别原 shell/leader。尚未证明与 T-266 同根因；保留现场，修复安装后经正常门禁恢复，不重复任务输入。
- T-249 集成客户端请求超时，但随后的门禁状态为 accepted、intent completed，main 为 `4164b43a81ac5092ec35d7f881967ec3947bad66`；无重复集成。evidence 删除检查为空。
- 已核对 REVIEW.md 对 RUN-OUTSIDE 脚本的敏感路径覆盖仍准确，冻结正文不改；只更新 MAP.md 的 Verified 到集成版本。project-map 检查零问题、零 stale。
