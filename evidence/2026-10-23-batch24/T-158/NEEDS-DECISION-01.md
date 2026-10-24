# T-158：revoked attempt 的路径释放条件待裁定

状态：BLOCKED / NEEDS-DECISION。task `T-158-1`，attempt `a1`，worker `b24-t158`，起点 `c01742804961214ed025b6c9fb9924a1ea49ee2d`。

## 看到了什么

- 任务卡 `evidence/2026-10-23-batch24/T-158/card.md` 最后一段明确要求：“‘保留证据’与‘占用路径’的区分须来自现行规格；若规格没有定义 revoked attempt 何时释放路径，上报 NEEDS-DECISION。”
- 现行 `.project-map/specs/native-cli-orchestration-2026-10-10.md:87` 只要求与“活跃 attempt”有路径交集时拒绝派发，没有定义撤销后仍有会话的 attempt 是否活跃。
- 同规格第 3 节第 8 步（第 94 行）要求回收时核对身份、已 idle 且交付已提交；第 4 节（第 100～108 行）规定撤销后干净工作区清理、脏或未知现场保留。两处都未明确路径释放是否依赖回收或工作区删除。
- `.project-map/specs/managed-delivery-2026-10-06.md:31`～34 规定 revoke/revise 撤销执行和候选、保留历史；第 62～64 行规定 reclaim 核对身份并关闭会话。没有定义 revoked attempt 的路径保留期限。
- `workbench/src/gates/core.ts:1252` 的路径检查保留所有未 reclaimed、未 removed 且带 thread_id 的 revoked attempt。
- `workbench/src/gates/core.ts:3793`～3819 的 revise 撤销旧 attempt 后调用清理，但 `core.ts:1276`～1278 对未 reclaimed 的会话推迟清理。
- `workbench/src/gates/core.ts:4180`～4218 的 reclaim 核对历史 attempt 的会话身份、空闲、停止和归档，才记 reclaimed。路径检查随后会排除这个 attempt，即使脏工作区需保留。

这些是源码与规格检查结果，不是本轮真实 Electron 红态或绿态证据。T-155 的原始观察仅作问题背景，不替本票复验。

## 为什么必须先决定

仅把 revoked 从路径检查中排除，会允许旧会话尚在运行时重叠派发，违反本票反例。自动回收旧会话，或要求执行主控显式回收，则是不同的操作契约。现行规格不足以给其中任一行为提供独立验收标准，worker 不能自行选定。

## 最小选项（请经构思主控裁定）

1. **显式回收后释放**：保存 v2 → revise → 对原 attempt 显式 reclaim（核对身份与空闲；停止并归档成功后释放路径）→ 正常 dispatch。脏工作区仍保留并上报，不继续占用路径。优先复验现有门禁是否已满足此语义，再按结果修复并补齐说明。
2. **修订命令负责处置旧会话**：明确 revise 对旧会话的核对、停止、归档和失败语义；只有确认旧会话不再活跃才释放路径。需同时明确运行中、身份未知及处置中断时的返回结果与恢复步骤，再实施。

需明确的核心一句话：带会话的 revoked attempt，在什么已核对事实成立后不再占用路径；是否要求显式 reclaim。

本轮停在此决定门禁；未修改产品、角色说明或测试，未启动模型、后台或 Electron，未申请提权。
