# T-259 结构完整性自查

STATUS: PASS

TARGET: 本目录所属冻结候选，相对 `1013b542377325cc1e37f89bdbf37ceb70b7e0ef`。

按项目 AGENTS.md 的 2026-11-03 规则由实现者自查；不是独立行为验收。扫描结果见 `design-scan-01.json`，未发现新增异常捕获或冻结验收修改，扫描本身不作为通过依据。

Reachability：真实 dispatch 在 createThread 后第一次 readThread 抛错；真实 CLI/socket 停止、重启、reclaim 的父版红态和候选绿态见 e2e-*-03。

Ownership：A2AGates 拥有 attempt 绑定、操作锁、路径占用与回收；本次只在现有 reclaim 里核验初始身份尚未保存的停止窗格。不添加平行回收 API，不由 UI 或后台旁路清理目录。

Architecture / Deep modules：沿用 runtime 的 read/stop/archive 与既有 cleanupAttempt。新增条件有明确反例，不添加 wrapper、重试、兼容路径或吞异常。恢复分支不会把仍活着、已发送或输入未知的会话当作成功。

Proportion：生产变更仅 core.ts 的 reclaim 分支与 README。初始 JSON 异常来源未知，不在本次猜测并添加解析重试。37 个边界场景用于验证拒收身份、输入、锁及停止/归档失败，三个变异均命中业务断言。

FINDINGS: 无已确认的结构问题。

LIMITATIONS: 仍须独立行为审查及正式安装后的原 attempt 复验；本自查不能替代它们。该恢复只支持未建立原生会话的 Codex 准备失败。
