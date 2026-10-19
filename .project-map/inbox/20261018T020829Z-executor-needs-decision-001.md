---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: ["ticket:T-096"]
created_at: "2026-10-18T02:08:29.162203Z"
schema: 1
title: "T-096：受管 worker 重启后进程身份变了，门禁会拒绝；需要决定是否给门禁加'恢复身份重绑定'操作"
id: "20261018T020829Z-executor-needs-decision-001"
---

事实（T-096 worker s16-t096 只读诊断，主控核对过代码位置）：重启后续接原生会话，会产生新的 shell PID 和 leader PID。门禁 workbench/src/gates/core.ts:2485 的 checkThread() 要求 identity.shell_pid 等于绑定时的 shell_pid，旧 leader 非空时还要求新 leader PID 也相等。bindObservedIdentity() 只会补齐首次观察时为空的字段，没有'同一原生会话在新后台中恢复'的重绑定入口。所以 T-096 即使把窗格、launch、task、role、session 和完整 argv 都恢复了，受管 worker 之后的验收和交付仍会被门禁当成身份不符拒绝。不能把新 PID 冒充旧 PID，也不能由 Panes 绕过门禁直接改 tasks/attempts 表。T-096 的任务卡禁止改 workbench/src/gates/，worker 已停下（BLOCKED）。单窗格 tracer 的局部合同已经转绿（真实 SQLite、模型 0），T-091 的回归也通过了。

选项：
A（推荐）：给门禁加一个显式的'恢复身份重绑定'操作。它在原操作锁和 CAS 内核对：原 attempt 仍是 current、fence 一致、launch 一致、原生会话一致、CLI 版本与启动记录一致、旧进程确实已经不在；全部满足才记录新的 shell 和 leader 身份，并追加一条恢复事件。任何一项不符就拒绝，并保留'未恢复'。这是门禁语义的改动，验收时须整组重跑原交付 8、恢复 9、编排 18（这是 T-090 留下的教训），另开独立审查。T-096 的修改边界相应放开到 gates/ 里这一个操作。
B：T-096 只恢复主控窗格（主控没有 worker attempt），受管 worker 的窗格恢复成只读的'未恢复'状态；要继续干活，走门禁重新认领一个新 attempt。这样不改门禁，但不满足'受管 worker 续接原会话'。
C：受管 worker 恢复后，自动经门禁 reclaim 旧 attempt、开新 attempt，并续接同一个原生会话。会话历史是连续的，但 attempt 换了，需要定义清楚交付和尾注怎么归属。

在你裁定之前，T-096 只继续做主控窗格部分和不涉及门禁的恢复路径。