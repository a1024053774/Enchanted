---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: "20261011T012611Z-ideation-revise-001"
refs: ["ticket:T-074", "ticket:T-075"]
created_at: "2026-10-11T01:51:41.982502Z"
schema: 1
title: "T-074 rev 3：空闲门禁有 145–268 ms 漏放窗口，Esc 中断后无恢复信号；需定主控窗格注入方案"
id: "20261011T015141Z-executor-needs-decision-001"
---

T-074 rev 3 交付 BLOCKED（a2a 040d017），执行主控核对后认为成立，详见 evidence/2026-10-10-batch12/T-074/controller-review-rev3.md。

可用的部分：两家空闲注入各 5 次以上，全部作为新消息送达；本轮没有出现被当成批准的情况。

挡不住的部分：
1. 上一条消息的回车已提交、但新回合开始事件还没到达时，门禁仍判为空闲，第二条被写进去。实测窗口 Codex 268 ms，Claude 145 ms。
2. 用户按 Esc 中断后，两家都不发 Stop，排队的消息放不出去。
3. 回合开始事件的标识和回合对不上。

请用户选：
A. 第一版不往主控窗格自动注入，只提示，由人放行。worker 窗格照常注入（rev 2 已证实）。T-075 按此做。
B. 修订合约再验证一轮。执行主控的建议：由于所有输入都经编排后台写进 node-pty，后台在提交回车时就在本地记“等待回合开始”，以此封住窗口；Esc 中断后的队列由人放行。需要给 Claude 加额度（现已用 22/25，Codex 已用 32/40）。
C. 其他。