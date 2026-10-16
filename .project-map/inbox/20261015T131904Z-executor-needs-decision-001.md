---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: ["ticket:T-078", "file:evidence/2026-10-11-batch13/T-078/controller-decision-04.md"]
created_at: "2026-10-15T13:19:04.446139Z"
schema: 1
title: "T-078 A-11 阶段 A 批准：执行主控签字被权限拦下"
id: "20261015T131904Z-executor-needs-decision-001"
---

问题：A-11 材料已冻结（exec/t078 68d57c89 + 20160280，static-check PASS，launch NO_GO）。按 A-06～A-10 先例，阶段 A 批准由执行主控签字（approved_by executor）后运行 run-09b.py --stage A。本次填写 a11-stage-a-approval-01.json 并启动时，执行主控会话的权限分类器判为 Self-Approval 拒绝；文件未改，阶段 A 未启动。
核对：materials-11 与 -10 只差身份字段；预算 ideation 4 roots/6 Messages、executor 6/11，与 protocol 一致；阶段 A 不启动角色 CLI、无真实模型回合、无用户输入。
选项：1) 用户本人签阶段 A（及后续各阶段）批准；2) 用户在执行主控会话里明确授权执行主控代签 T-078 09B 各阶段批准（可能还需在该会话权限设置里放行）；3) 暂停 T-078。
最小选择：1 或 2。其余票（T-086 返工、T-085、T-081 等待）不受影响。