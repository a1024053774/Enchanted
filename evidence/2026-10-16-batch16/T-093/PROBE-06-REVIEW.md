# T-093 probe-06 冻结候选独立审查（2026-10-17）

审查员 `/root/terminal_classification_review`，gpt-6.1-sol / xhigh，新上下文、只读。
以下保留审查返回的 FAIL，不因 worker 后续修正改写结论。

```text
STATUS: FAIL
TARGET: T093-terminal-v7；HEAD 151d96bf8bd6099cd06af0f36d5d5d2e8a8b0bbc 的冻结未提交候选
EVIDENCE:
- 新分类单项测试通过：python3 -B workbench/tests/test_t093_probe_safety.py ProbeSafety.test_terminal_process_denials_and_host_failures_keep_only_categories。
- 独立内存输入验证了 vfork/execvp/posix_spawnp、ANSI、空白折叠及合成敏感标记不落入输出。
- diff 仅增加分类、测试、变异和交接说明；未修改 sandbox/profile、权限或启动路径。
- probe-05 摘要不足以确认 fork/exec 被拒；PROBE-06.md 明确保留原权限并交主控执行新报告命令。
- project_map.py status：0 problems，0 stale living docs；全程未编辑文件。
FINDINGS:
- [P2] workbench/tests/probe_t093_normal_login.py:374 — 未把失败词绑定到连接目标。
  Unable to connect to 127.0.0.1:54321.\nAPI documentation: https://api.anthropic.com 被误报为官方主机连接失败；
  Failed to connect to api.anthropic.com.invalid 同样误报。应限定失败描述中的完整目标主机，并补混合目标及域名后缀反例。
- [P2] workbench/tests/probe_t093_normal_login.py:374 — 只接受失败词在主机名前的顺序。
  独立输入 api.anthropic.com: unable to connect 返回 false，漏掉明确的官方主机失败文字；应覆盖主机名前置形式。
COUNTEREXAMPLE:
- 内存变异 process_denial_operations 恒空被独立 vfork/EACCES 输入拒绝。
- 内存变异仅出现官方主机名就判失败被文档引用输入拒绝。
- 当前候选仍接受上述本地失败加官方引用、非官方域名后缀两个错误输入；新增测试未覆盖。
LIMITATIONS:
- 仅验证 L1 分类逻辑及静态交接，不证明真实 CLI、syscall、网络或沙箱归属。
- 缺少真实 probe-06 结果，实际退出原因仍为 INCOMPLETE；不能据此放宽 process-fork/process-exec。
- 未运行真实 Claude、凭据读取、进程核对、sandbox 应用、网络或完整辅助测试套件。
RULE:
- N/A；本轮未确认属于已知重复缺陷类别。
```

worker 后续处理：把上述反例及 URL 用户信息反例加入分类检查，`terminal-target-red-06.json` 保存修正前断言失败。
随后改为提取失败描述中的目标主机并精确比较，同时支持主机名前置；不再按附近出现的官方地址推断目标。
`probe-helper-checks-12.json` 保存相同测试通过及旧错误匹配方式被拒绝的结果。
这是 worker 复验，不替代新的独立验收；实际退出原因仍待主控执行 probe-06。
