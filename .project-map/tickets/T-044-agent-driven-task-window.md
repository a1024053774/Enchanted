---
id: T-044
title: 任务窗口由 agent 驱动
type: build
status: open
blocked_by: []
claimed_by: Codex T-044 worker（2026-10-09）
supersedes:
---

## What to build

用户要求（2026-10-09）：任务窗口里的任务与会话由主控 agent 经门禁建立，不靠人手动添加会话、选角色。
- 门禁 `create` 同时在任务窗口建立该任务（标题、项目取自任务信息）。
- `dispatch` 创建的 worker 会话自动归入该任务，角色 worker。
- 新增门禁命令 `attach`：主控传入任务、角色（reviewer、monitor 等）、模型与指令，Synara 新建会话并自动归入该任务。用户已确认：这类会话是"普通会话加角色"，不是交付 attempt，没有 submit、验收、集成权限，只记一条事件。
- 回收后会话标为已结束，保留在任务历史中，界面淡化显示。
- 手动"会话归属"编辑保留为人工修正入口。
所有新行为在门禁核心实现，CLI 与 HTTP 自动可用；主控的 MCP 工具等主控迁入 Synara 时再开放（本 ticket 不给 agent 会话开放 create/dispatch/attach 工具）。

## Acceptance

- [ ] 经 `a2a/scripts/gate`（或同一 CLI 的 HTTP 传输）依次 create → dispatch → attach reviewer，任务窗口无需任何手动操作即显示该任务、worker 与 reviewer；有截图与命令输出。
- [ ] attach 的会话调用 `a2a_submit` 被拒绝；不能经它推进门禁状态。先在缺失实现时取得红态。
- [ ] 回收后会话在任务中标为已结束；membership 与门禁事件读回一致。
- [ ] T-036/T-037 的 35 项与 T-038 membership 场景仍通过；typecheck、lint 通过。

## Resolution

2026-10-09 worker 交接：**BLOCKED，保持 open**。代码已在 fork `a2a` 分支提交，最终候选 `808156d63ef8e265a0e2c017fae7851e50a51019`，未 push；[中文报告](../../evidence/2026-10-09-batch5/T-044/RESULTS.md) 保存全部红态、检查、截图失败、两次审查原文与边界。

create/dispatch/attach 自动归属已取得早期候选 HTTP 与 dev UI 证据；MCP handler 身份反例与最终候选 CLI/SQLite 历史修复通过。最终 35 项为 34/35，剩余一项 native 夹具 thread 缺失；fmt/lint/typecheck 通过，服务端另有 verifying 超时未定因。最终界面与真实 Gateway 认证链未通过，验收框保持未勾选。

主控需要决定：任务书要求 provider 关闭，导致原生会话为 error，既有 T-037 回收保护拒绝，无法完成门禁回收/淡化截图。选择保持保护并批准受控无模型 provider 夹具，或扩大恢复合同并重新取得反例；worker 未自行选择。另有一次范围偏离类型：执行正式 status 两次读取了被禁止目录中的启动身份元数据，详见报告；未写正式实例或重启它。
