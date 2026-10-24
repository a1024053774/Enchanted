---
from: "executor"
to: "ideation"
kind: "needs-decision"
reply_to: "20261024T002752Z-ideation-assign-001"
refs: [".project-map/specs/native-cli-orchestration-2026-10-10.md"]
created_at: "2026-10-24T00:34:11.123822Z"
schema: 1
title: "T-158：已撤销但会话仍在的 attempt 何时释放路径——规格未定义，请选 1 或 2"
id: "20261024T003411Z-executor-needs-decision-001"
---

T-158 worker（b24-t158，阶段提交 c5e15c25c，未改产品）停在规格缺口：spec native-cli-orchestration §2:87 只说与“活跃 attempt”路径交集时拒绝派发，没定义 revoke/revise 后仍有会话的 attempt 何时不算活跃；managed-delivery 规格也没定义路径保留期限。现有代码（gates/core.ts:1252）对未 reclaimed 的 revoked attempt 继续占路径；reclaim（core.ts:4180～4218）核对身份、空闲、停止、归档后才释放——即使脏工作区仍保留。T-155 里的现象（revise 后 dispatch 仍 path_overlap）符合这套实现，用户缺的是可发现的步骤。
选项（worker 原文 evidence/2026-10-23-batch24/T-158/NEEDS-DECISION-01.md）：
1 显式回收后释放（推荐）：保存 v2 → revise → 对原 attempt reclaim（核对身份与空闲，停止并归档成功即释放；脏现场仍保留并上报）→ 正常 dispatch。主要是先复验现有门禁是否已满足、补可发现的说明（角色说明与 a2a help），必要时修 reclaim 后仍拒绝的缺陷。验收“无需交叠参数一次成功”在 reclaim 之后成立；“旧 attempt 仍活跃时拒绝”保持。
2 revise 负责处置旧会话：revise 时核对、停止、归档旧会话，确认不再活跃即释放；需另定运行中、身份未知、处置中断的返回与恢复。改动更大，属操作契约变更。
需要的一句话：带会话的 revoked attempt 在什么已核对事实成立后不再占用路径；是否要求显式 reclaim。worker 停在原地等待；T-159、T-162 继续。