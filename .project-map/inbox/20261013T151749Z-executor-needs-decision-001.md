---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: ""
refs: ["ticket:T-077"]
created_at: "2026-10-13T15:17:49.428538Z"
schema: 1
title: "T-077 r3 诊断：被测 worker 手写了两个不支持的尾注；冲突闭环其余环节真实通过，C2 验收未到达"
id: "20261013T151749Z-executor-needs-decision-001"
---

只读诊断（a2a-wt-t077 evidence/.../T-077/REAL-R3-DIAGNOSIS-01.md，新增真实回合 0）：C2 提交的 9 项规定尾注全部正确，另多出 A2A-Fence: 2 与 A2A-Spec-Rev: 1。来源是被测 worker 自己在 git commit 里手写 --trailer（rollout ordinal 73 原文），产品尾注 hook 只写 9 项，门禁 checkTrailers 也只接受这 9 项——属于模型行为导致的交付错误，不是产品缺陷，也不是夹具期望写错。真实已证明：第一个 worker 交付；真实 Git 文本冲突；旧会话结束、冲突替换出新 attempt（fence 2、base=G）；新 worker 重做并显式重交 C2；按 launch 作用域的 relay 去重生效；同一 home 两份根日志各自独立、旧日志逐字节不变。未到达：C2 的 verify/integrate（按源码推论 verify 会因额外尾注拒收）。T-077 状态 INCOMPLETE；r1+r2+r3 实际观察 9、保守占位 10 回合。选项：A 再批 2～4 回合重跑 r4，并在 worker 角色卡/派发文本里写明'不要手写 A2A 尾注，由 hook 生成'（提示词层，不改门禁）；B 再批回合，但只跑第二阶段需要的最小重演（不可行：第二阶段依赖同一实例的真实冲突，需整套重来，故实际同 A）；C 不再跑真实，用现有证据加一条受控夹具：对 C2 同样带额外尾注的交付，门禁 verify 应拒收 invalid_trailers（不花模型额度），T-077 以'真实冲突闭环到重交为止 + 尾注拒收受控证明'报告，是否可关票由用户定。执行主控建议 C 先做，再由用户决定是否 A。