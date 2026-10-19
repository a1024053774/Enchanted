STATUS: PASS

TARGET: 91cd22d523af28ab9a13631d6919635be430ba34；仅主控 #125 的 L0/L1 恢复合同。

EVIDENCE:

- 独立新建 SQLite、原生会话文件及 nonce，调用实际 `Panes.recover`。命令：`/opt/homebrew/bin/node --experimental-vm-modules /private/tmp/a2a-normal-review-17-7zJjor/probe.mjs`，退出码 0。
- 两类正常登录记录均未调用版本、PTY、旧进程或认证边界；持久化 `normal_login_restore_requires_protected_start` 和经正常登录入口重新启动的提示。重开 SQLite 后记录仍在，历史启动记录未变。
- fake API、缺少 `executable_path` 的 legacy 记录均按完整原 argv 恢复；版本、原生会话、规范路径和前台进程反例均被拒绝。
- worker 未恢复、无边界调用，attempt 数据逐字节不变。
- 原始结果：[candidate-raw.json](/private/tmp/a2a-normal-review-17-7zJjor/candidate-raw.json)；摘要：[summary.json](/private/tmp/a2a-normal-review-17-7zJjor/summary.json)。
- 结束核对：HEAD 仍为指定候选，产品及验收快照无 diff；项目 status 为 0 problems、0 stale。

FINDINGS:

- 本次限定范围内未发现可复现违规。

COUNTEREXAMPLE:

- 同一业务断言拒绝旧坏版本 `8771ba58d71a3fc025b09e32c45096b39858572e`：正常登录确实到达供应的 `--version` 和 PTY，且产生恢复成功记录。证据：[known-bad-raw.json](/private/tmp/a2a-normal-review-17-7zJjor/known-bad-raw.json)。

LIMITATIONS:

- 仅证明局部逻辑和持久化合同。CLI、PTY、进程观察及认证准备边界均为供应边界；未执行真实 OS、认证、服务、网络或模型操作。
- OS/new443 与原生恢复七场景仍待执行；T-093 整体验收保持 INCOMPLETE。
- 复跑须把两个探针源码复制到新临时目录，避免覆盖本次证据。

RULE:

- 无新增规则。现有独立检查可捕获“版本探测先于正常登录恢复拒绝”和“一律拒绝导致合法恢复退化”。
