---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: "20261011T004535Z-ideation-revise-001"
refs: ["ticket:T-074", "ticket:T-075"]
created_at: "2026-10-11T01:22:07.484436Z"
schema: 1
title: "T-074 rev 2：worker 不问模式成立；主控 hook 缺结束事件与请求标识，需定恢复条件"
id: "20261011T012207Z-executor-needs-decision-001"
---

T-074 rev 2 交付 BLOCKED（a2a 2fcd1d0），执行主控核对后认为 BLOCKED 成立。详情见 evidence/2026-10-10-batch12/T-074/controller-review-rev2.md 与 needs-decision-03.md。

已证实：受管 worker 用“不问”模式，越界操作会被拒，之后注入的文字作为新消息送达。Codex（-a never）、Claude（dontAsk）各 3 次，全部成立。spec 第 6 节的 worker 规则可以用。

未证实：主控窗格“等批准时暂停”。两家的 PermissionRequest hook 都只在批准窗口出现时有一个开始事件，窗口关闭后没有结束事件，也没有请求标识（Claude 的 prompt_id 是用户输入的标识）。按决定 02，worker 停在这里，没有做竞态测试。

请用户决定（最小选项）：
A. 第一版暂缓往主控窗格自动注入：主控窗格只收提示，由人手动处理。T-075 按此修订后开工。
B. 授权在本票核实另一条结构化接口，再定恢复条件。例如 Codex 内部日志里带 request_id 的 serverRequest/resolved；Claude 那边需要另找。这超出 rev 2 已授权的 hook 范围。
C. 其他。

另需决定：Claude R7 现有 7 次，不到 10 次，也缺 running 状态。可以用剩余 4 回合补到 10 次以上，也可以接受现状。Claude 已用 11/15，Codex 已用 23/30。

另记：worker 窗格中途被中断，有人把模型改成 gpt-6-astra，并输入了没有标记的“继续”。这算用户人工介入，已补记。探针都是在改模型之前、用 gpt-6.1-sol 测的。