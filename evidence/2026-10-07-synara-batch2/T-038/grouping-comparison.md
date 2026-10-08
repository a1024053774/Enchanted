# T-038 分组载体对照（2026-10-07）

**REALITY GATE: INCOMPLETE，载体选择待主控确认；尚未实现。** 基线：Synara `a9cc30c395af9ffd51476a1841d80bca66568993`，worktree `synara-t038`。目标是普通仓库项目下多个任务、每任务多个带角色的 agent thread，显示唯一门禁的状态。不改上游 thread 表，不启用模型、不改 Hub 生命周期，也不把上游的完成状态当作门禁验收。

| 原生对象 | observed：实际表达与代码 | 同任务多 thread 与角色 | 与门禁对应 |
| --- | --- | --- | --- |
| ProjectTask | `packages/contracts/src/projectAgent.ts:139`：必须有 `projectId`、`goalId`，一个 `assignedThreadId`；`apps/server/src/persistence/Migrations/109_ProjectAgent.ts:72` 持久表 FK 指向 goal | 单个当前 assignee；附加表可以补 reviewer 等角色，但原生并非任意多会话分组 | 可把其 id 映射 gate task id，但原生 `ready/running/review/done` 不能替代 `claimed/submitted/verified/accepted` |
| ProjectTaskAttempt | 同文件 `:165`；migration `:105`。每条绑定 task 和一个 `workerThreadId`，attemptNumber、outcome | 同 task 有历史 attempts；没有角色。不同 retry 不能当作同一次分工的 worker/reviewer | 不能等同 gate attempt；缺少 session_id/fence/spec_rev 和门禁 CAS 事实 |
| HubWorkItem | `packages/contracts/src/hubWork.ts:43`，sourceThreadId + 单个 workerThreadId，队列和运行状态 | 一次委派的一对关系；没有任意成员/角色 | 是 Hub 编排工作项，不是 gate task 或受锁交付 |
| Todo | `packages/contracts/src/todo.ts:49`，可选 projectId + 单个 threadId；不是 chatThreadId（实际字段名为 threadId） | 单个委派会话；不能容纳并行角色 | 个人待办；客户端从会话推导展示状态，不能作为门禁验收事实 |
| parentThreadId | `packages/contracts/src/orchestration.ts:1087`、`packages/shared/src/threadHierarchy.ts:10`；SQLite projection 持久化创建关系 | 可找后代，但它描述创建树；会混入子任务、派生与历史，没有独立任务身份和角色 | 无 gate 绑定。不能从创建树推出同一门禁任务 |
| split views | `apps/web/src/splitViewStore.ts:60/:119/:715`：ownerProjectId、sourceThreadId、pane tree，Zustand localStorage | 持久化多会话布局，但只有浏览器客户端持久性；没有任务身份、角色或服务端归属 | 可复用布局/聊天组件，不能成为 gate task 的权威归属 |

## 选择与理由

优先评估 ProjectTask + 附加表。其多角色缺口可以用 membership 补齐；决定不优先采用它的原因是载体前置条件，而不是字段缺失：

- `ProjectAgentService.createTask`（`apps/server/src/projectAgent/Layers/ProjectAgentService.ts:4079`）必须引用本项目的 active goal（`:4103`），goal FK 指向已配置 coordinator（migration `109:50`）。
- coordinator 只允许 Hub 项目（同 service `:1350`，`The coordinator is only available on hubs.`），普通仓库项目不能直接走该创建流程。
- Groups/ProjectAgent API 在 Stable 被权威禁用（`apps/server/src/projectAgent/groupsBetaGate.ts:49/:73`，service `:6560`）。为普通项目创建 ProjectTask 需要绕过原生服务写上游表，或扩大本 ticket 去改 Hub/goal/Stable 语义；两者均超出当前范围。
- 原生 acceptance 路径由 coordinator/user 依据已记录 evidence 将 ProjectTask 标为 done（service `:4208`）；这不是独立 oracle + Git CAS 门禁。即便作为只读载体，也必须保留两个状态而不能同步写 done。本轮不建立第二套业务完成路径。

**建议选择：独立 membership，受管任务直接以现有 gate task id 为身份，保存项目、显示标题、thread 与角色；业务状态仍只读门禁核心。** 未挂合同的任务只有归属和标题，不拥有第二套门禁状态。它是 spec 明确允许的缺少所需分组时的独立模块，不修改原生 ProjectTask/ProjectTaskAttempt。主控统一术语后才能宣布载体 gate PASS。

若主控要求 ProjectTask 载体，最小选项是本轮只展示已经合法存在于 Hub 的 ProjectTask，并在附加表记录 gate id 和角色；这会把“普通仓库项目”限定为 Hub，需主控确认范围和测试输入。当前不自行作此变化。

## 探针与下一步

已完成源码探针：从公开 contract 追到 createTask、coordinator 条件、migration FK 和 Stable gate；PASS 条件为能沿现有服务在普通项目创建 carrier，观察结果为不满足。未运行原生 API 拒绝实测，故以上是源码 observed，非运行 measured。

下一步：将本页交主控。确认后先通过隔离服务器 HTTP 入口保留任务归属请求的预期红态，再实现 storage → auth HTTP → web 的 Tracer bullet。Deep modules 仅新增一个归属存储接口；Ubiquitous language 不把 ProjectTaskAttempt、gate attempt、thread session 混用。人工介入事件形状尚未给定，暂显示空。
