# T-096 受管 worker 的运行时身份重绑定

状态：BLOCKED。来源：s16-t096，T-096 / a1，ready_rev 1。

重启原生 CLI 会创建新的 shell PID。现有门禁 `workbench/src/gates/core.ts:2485` 的
`checkThread()` 要求 `identity.shell_pid === bound.shell_pid`，并在旧 leader 非空时
要求新 leader PID 也相等。`bindObservedIdentity()` 只补齐首次观察的空 leader/native 值，
没有允许同一原生会话在新后台恢复后的重绑定入口。

因此仅恢复 PTY、原 launch、task、role、session 与完整 argv，仍无法让该 attempt 的
后续验收或交付通过运行时身份检查。不能把新 PID 假装成旧 PID，也不能由 Panes 直接
改写门禁拥有的 tasks / attempts 表；两者都会绕过门禁的身份与锁语义。

任务卡禁止修改 `workbench/src/gates/`。本 worker 不修改该目录。建议主控协调：

1. 为门禁提供显式恢复身份操作，仍核对原 attempt、fence、launch、原生会话与版本，
   在原操作锁和 CAS 保护内记录新 shell/leader 身份；主控协调该变更的写入者与授权。
2. 若不允许门禁变更，则本票不能宣称受管 worker 已完成可用续接；需由主控明确收缩验收。

已在 commentary 上报。因任务卡禁止写 `.project-map/`，此处保存正文，收件箱条目由主控登记。
