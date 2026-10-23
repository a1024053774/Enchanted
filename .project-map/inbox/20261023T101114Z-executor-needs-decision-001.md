---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: ["file:workbench/tests/test_t111_flow.mjs#L44"]
created_at: "2026-10-23T10:11:14.486741Z"
schema: 1
title: "T-146：‘三处都显示已结束’与 T-111 不列已结束会话冲突"
id: "20261023T101114Z-executor-needs-decision-001"
---

T-146 的验收里有一项要构思主控（必要时问用户）裁定；该票不停，按下面的“暂行做法”继续。

问题：ticket 验收写“关闭终端/CLI 退出后，三处页面都显示已结束”。但流程页按 T-111 的既定设计（受保护的 workbench/tests/test_t111_flow.mjs:44,47）不列已结束的会话；侧栏（sidebar.ts:184）也只列已批准的角色申请，终端关闭后该主控从侧栏消失。所以“三处都显示已结束”字面上做不到，除非改 T-111 的展示规则和它的验收文件。

证据（真实 Electron，修前 ebbae7bd0，沙箱外运行）：/Users/luckye/Documents/Code/a2a-wt-t146/evidence/2026-10-23-batch23/T-146/outside-20261023T100809Z-50877/red.json。同一时刻：空闲 worker 在侧栏“空闲”、流程“空闲”、Reflect“运行中”；主控终端在侧栏和流程“未知”、Reflect“运行中”。这就是用户看到的不一致，根因是 Reflect 用自己的 lifecycle 计算状态，与侧栏的 agentState 不同源。

暂行做法（执行主控定的，不改验收文件）：三处状态统一取侧栏的同一来源；已结束的会话在哪一页都不得显示“运行中”——Reflect 显示“已结束”，侧栏与流程沿用现有规则不列出。

选项：
A. 沿用暂行做法（推荐，最小改动，不改 T-111 合同）。
B. 侧栏与流程也列出已结束的会话并标“已结束”：要改 T-111 的展示规则和受保护的验收文件，需要用户同意。

最小选择：答 A 或 B。