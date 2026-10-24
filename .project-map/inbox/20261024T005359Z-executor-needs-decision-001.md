---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: "20261024T002752Z-ideation-assign-001"
refs: [".project-map/tickets/T-159-split-keeps-original-pane.md"]
created_at: "2026-10-24T00:53:59.835470Z"
schema: 1
title: "T-159：任务视图分屏走“事前说明”而非并排，验收第 1 条要你确认"
id: "20261024T005359Z-executor-needs-decision-001"
---

T-159 候选（16fca3526，修复中加一处小改）根因：任务视图分屏调用 shell_start 再切到项目层，原 worker 被普通终端替换。T-139 已定“普通终端只在项目层，不混入任务视图”，所以 worker 选了 ticket 正文允许的那一支：任务视图里的 agent 会话菜单禁用右/下分屏并事先说明“任务视图只展示 Agent 会话。请在普通终端中分屏。”，后端也拒绝绕过菜单的请求；项目层终端照常分屏。真实 Electron 红态（修前被替换）、绿态、两个变异、T-139 三项回归均通过（outside-01/02）。
冲突：ticket 验收第 1 条写“任务视图点向右分屏后，原 worker 与新窗格并排”。候选不并排，独立审查据此判 INCOMPLETE，要求交你确认。
选项：A 接受“事前说明”分支，把验收第 1 条改为“任务视图内不提供分屏并事先说明，原 worker 与布局不变；项目层终端分屏保留原窗格并排”（推荐，最小、与 T-139 一致）；B 要求任务视图真并排——需定新窗格是什么（同任务另一个 agent 会话？还是允许普通终端进任务视图，即改 T-139）；这是设计取舍，需用户。
另：审查发现菜单按 role==='shell' 判断，已批准主控的项目终端也被禁分屏（回归），已让 worker 改成与后端同一判据并加测试。