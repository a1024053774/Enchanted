---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: ["ticket:T-077"]
created_at: "2026-10-13T14:46:58.819881Z"
schema: 1
title: "T-077 真实冲突复验：额外预算只剩 2，完整闭环需 4，是否再批 2 回合"
id: "20261013T144658Z-executor-needs-decision-001"
---

T-077 已在 exec/t077 2e2291ac 显式加 service_tier="default"（最小检查红→绿）。r3 审批材料 evidence/2026-10-11-batch13/T-077/REAL-APPROVAL-03.md（新实例 /private/tmp/t077-cf-20261013-r3，隔离 home 只复制 auth.json）。预算：卡片 4 已用；用户批准额外最多 4，r2 观察 1、按规则保守占 2（未开始的回执回合不释放），剩 2。完整场景两次启动各需工作+回执，共 4。选项：A 再批 2 回合，r3 完整重演——证明旧 worker 交付后真实 Git 冲突、新 attempt 在同 home 整理并重交 C2、验收/集成/回收与历史日志隔离（执行主控推荐，否则 T-077 无法关闭）；B 只用剩余 2 做第一阶段——只证明 default 速度下真实启动、交付、回执与身份，不证明冲突替换闭环，T-077 仍 INCOMPLETE；C 暂不跑真实，T-077 保持 INCOMPLETE。